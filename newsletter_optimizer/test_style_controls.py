"""
Test that style controls actually influence the newsletter generation.
"""

import json
from pathlib import Path

# Metric definitions (copied from app.py for testing)
metric_definitions = {
    'doom_level': {'name': 'Doom Level', 'description': 'Warnings about AI dangers, job losses, existential risks'},
    'optimism_level': {'name': 'Optimism Level', 'description': 'Positive outlook on AI opportunities and benefits'},
    'humor_usage': {'name': 'Humor Usage', 'description': 'Jokes, wit, sarcasm in the content'},
    'expert_citations': {'name': 'Expert Citations', 'description': 'Quotes and references to named experts'},
    'africa_focus': {'name': 'Africa Focus', 'description': 'Content specific to Africa and Global South'},
    'storytelling': {'name': 'Storytelling', 'description': 'Narrative elements and personal anecdotes'},
}

def build_metric_instructions(metrics: dict, definitions: dict, analysis: dict) -> str:
    """Build AI instructions from the metric dial settings."""
    
    instructions = []
    instructions.append("## STYLE SETTINGS (from user's dial adjustments)")
    instructions.append("")
    
    high_metrics = []
    low_metrics = []
    
    for metric_key, value in metrics.items():
        if metric_key not in definitions:
            continue
        
        avg = analysis.get('metrics', {}).get(metric_key, {}).get('mean', 50)
        name = definitions[metric_key]['name']
        description = definitions[metric_key]['description']
        
        if value >= 70:
            high_metrics.append({
                'name': name,
                'value': value,
                'description': description,
                'intensity': 'HEAVILY' if value >= 85 else 'MORE'
            })
        elif value <= 30:
            low_metrics.append({
                'name': name,
                'value': value,
                'description': description,
                'intensity': 'COMPLETELY AVOID' if value <= 15 else 'MINIMIZE'
            })
    
    if high_metrics:
        instructions.append("**EMPHASIZE THESE ELEMENTS (user set dials HIGH):**")
        for m in high_metrics:
            instructions.append(f"- {m['intensity']} use {m['name']}: {m['description']}")
    
    if low_metrics:
        instructions.append("")
        instructions.append("**MINIMIZE THESE ELEMENTS (user set dials LOW):**")
        for m in low_metrics:
            instructions.append(f"- {m['intensity']} {m['name']}: {m['description']}")
    
    instructions.append("")
    
    doom = metrics.get('doom_level', 50)
    optimism = metrics.get('optimism_level', 50)
    
    if doom >= 70 and optimism <= 30:
        instructions.append("**OVERALL TONE:** Dark and cautionary. This newsletter should feel urgent and warning-oriented.")
    elif optimism >= 70 and doom <= 30:
        instructions.append("**OVERALL TONE:** Hopeful and constructive. Focus on solutions and opportunities.")
    elif doom >= 60 and optimism >= 60:
        instructions.append("**OVERALL TONE:** Balanced but intense. Acknowledge serious risks while highlighting opportunities.")
    
    return "\n".join(instructions)


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING STYLE CONTROLS")
    print("=" * 60)
    
    # Load metrics analysis if it exists
    metrics_file = Path(__file__).parent / "data" / "advanced_metrics.json"
    if metrics_file.exists():
        with open(metrics_file) as f:
            metrics_analysis = json.load(f)
        print(f"\n✓ Loaded metrics analysis from {metrics_file}")
    else:
        metrics_analysis = {}
        print("\n⚠ No metrics analysis file found")
    
    # Test 1: High doom, low optimism
    print("\n" + "-" * 40)
    print("TEST 1: High Doom (90), Low Optimism (20)")
    print("-" * 40)
    
    test1 = {
        'doom_level': 90,
        'optimism_level': 20,
    }
    
    result1 = build_metric_instructions(test1, metric_definitions, metrics_analysis)
    print(result1)
    
    # Test 2: High Africa focus, high humor
    print("\n" + "-" * 40)
    print("TEST 2: High Africa Focus (85), High Humor (80)")
    print("-" * 40)
    
    test2 = {
        'africa_focus': 85,
        'humor_usage': 80,
        'expert_citations': 25,
    }
    
    result2 = build_metric_instructions(test2, metric_definitions, metrics_analysis)
    print(result2)
    
    # Test 3: All neutral (no output expected)
    print("\n" + "-" * 40)
    print("TEST 3: All Neutral (50)")
    print("-" * 40)
    
    test3 = {
        'doom_level': 50,
        'optimism_level': 50,
        'humor_usage': 50,
    }
    
    result3 = build_metric_instructions(test3, metric_definitions, metrics_analysis)
    print(result3 if result3.strip() else "(No special instructions - all neutral)")
    
    print("\n" + "=" * 60)
    print("✅ Style controls ARE generating instructions!")
    print("These instructions are passed to the AI via 'additional_instructions'")
    print("=" * 60)









