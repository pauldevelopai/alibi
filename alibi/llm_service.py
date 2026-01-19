"""
Alibi LLM Service

Optional LLM integration for generating alert text and reports.
MUST be fail-safe - all functions return None on failure.
"""

from typing import Optional, Tuple
import os

from alibi.schemas import Incident, IncidentPlan, Decision
from alibi.config import AlibiConfig


def generate_alert_text(
    plan: IncidentPlan,
    incident: Incident,
    config: AlibiConfig
) -> Optional[Tuple[str, str]]:
    """
    Generate alert title and body using LLM.
    
    Returns None if API key not available or call fails.
    
    Args:
        plan: The incident plan
        incident: The incident
        config: Configuration with API key
        
    Returns:
        (title, body) tuple or None on failure
    """
    if not config.openai_api_key:
        return None
    
    try:
        import openai
        
        client = openai.OpenAI(api_key=config.openai_api_key)
        
        # Build context for LLM
        event_summary = "\n".join([
            f"  - {e.event_type} at {e.ts.strftime('%H:%M:%S')} "
            f"(conf: {e.confidence:.2f}, sev: {e.severity})"
            for e in incident.events[:5]  # Limit to first 5
        ])
        
        if len(incident.events) > 5:
            event_summary += f"\n  ... and {len(incident.events) - 5} more events"
        
        prompt = f"""You are writing an incident alert for security operators. Use NEUTRAL, CAUTIOUS language.

CRITICAL RULES:
1. NEVER use accusatory terms: suspect, criminal, perpetrator, intruder, thief
2. ALWAYS use: "possible", "appears", "may indicate", "needs review"
3. NO identity claims - say "appears to match" not "is identified as"
4. If no evidence, explicitly state "no video evidence available"

Incident: {incident.incident_id}
Time: {incident.created_ts.strftime('%Y-%m-%d %H:%M:%S')}
Events:
{event_summary}

Assessment:
- Severity: {plan.severity}/5
- Confidence: {plan.confidence:.2f}
- Evidence: {"Available" if plan.evidence_refs else "No clips available"}
- Recommended Action: {plan.recommended_next_step.value}
- Requires Human Review: {plan.requires_human_approval}

Generate:
1. A short alert title (under 80 chars)
2. A brief alert body (2-4 sentences) explaining what was detected and why review is needed

Format your response as:
TITLE: [your title]
BODY: [your body text]
"""
        
        response = client.chat.completions.create(
            model=config.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "You write neutral, cautious security alerts. Never accuse or make identity claims."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=config.openai_max_tokens,
            temperature=config.openai_temperature,
        )
        
        content = response.choices[0].message.content
        if not content:
            return None
        
        # Parse response
        lines = content.strip().split("\n")
        title = None
        body_parts = []
        
        in_body = False
        for line in lines:
            if line.startswith("TITLE:"):
                title = line.replace("TITLE:", "").strip()
            elif line.startswith("BODY:"):
                body_parts.append(line.replace("BODY:", "").strip())
                in_body = True
            elif in_body and line.strip():
                body_parts.append(line.strip())
        
        if title and body_parts:
            body = " ".join(body_parts)
            return (title, body)
        
        return None
        
    except Exception as e:
        print(f"LLM alert generation failed: {e}")
        return None


def generate_shift_report_narrative(
    incidents: list,
    decisions: list,
    kpis: dict,
    config: AlibiConfig
) -> str:
    """
    Generate shift report narrative using LLM.
    
    Falls back to simple summary on failure.
    
    Args:
        incidents: List of incidents
        decisions: List of decisions
        kpis: KPI dictionary
        config: Configuration
        
    Returns:
        Narrative text (or fallback)
    """
    if not config.openai_api_key:
        return _fallback_narrative(incidents, decisions, kpis)
    
    try:
        import openai
        
        client = openai.OpenAI(api_key=config.openai_api_key)
        
        prompt = f"""Summarize this security shift in 3-4 sentences.

Total Incidents: {len(incidents)}
True Positives: {kpis.get('true_positives', 0)}
False Positives: {kpis.get('false_positives', 0)}
Precision: {kpis.get('precision', 0):.1%}
Average Severity: {kpis.get('avg_severity', 0):.1f}/5

Write a professional summary for the shift supervisor. Focus on key patterns and notable incidents.
"""
        
        response = client.chat.completions.create(
            model=config.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "You write professional security shift reports."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.4,
        )
        
        content = response.choices[0].message.content
        if content:
            return content.strip()
        
        return _fallback_narrative(incidents, decisions, kpis)
        
    except Exception as e:
        print(f"LLM report generation failed: {e}")
        return _fallback_narrative(incidents, decisions, kpis)


def _fallback_narrative(incidents: list, decisions: list, kpis: dict) -> str:
    """Simple fallback narrative without LLM"""
    total = len(incidents)
    precision = kpis.get('precision', 0)
    
    if total == 0:
        return "Quiet shift with no incidents detected."
    
    quality = "excellent" if precision > 0.9 else "good" if precision > 0.75 else "moderate"
    
    return (
        f"Processed {total} incident(s) during shift with {quality} detection quality "
        f"({precision:.1%} precision). "
        f"Operators reviewed {len(decisions)} case(s). "
        f"System performance within normal parameters."
    )
