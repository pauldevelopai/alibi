"""
OpenAI Dashboard - Track API usage, costs, and model performance

Provides:
- API usage tracking per session
- Cost estimation
- Model performance metrics
- Fine-tuned model stats
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from collections import defaultdict

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATA_DIR = Path(__file__).parent / "data"
USAGE_LOG_FILE = DATA_DIR / "openai_usage_log.json"

# Pricing per 1K tokens (approximate, as of late 2024)
PRICING = {
    # Base models
    'gpt-4.1': {'input': 0.002, 'output': 0.008},
    'gpt-4.1-mini': {'input': 0.00015, 'output': 0.0006},
    'gpt-4o': {'input': 0.005, 'output': 0.015},
    'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
    'gpt-4o-mini-2024-07-18': {'input': 0.00015, 'output': 0.0006},
    'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015},
    'dall-e-3': {'per_image': 0.04},  # Standard quality 1024x1024
    'dall-e-3-hd': {'per_image': 0.08},  # HD quality
    # Fine-tuned pricing (3x base for training, same for inference)
    'ft:gpt-4o-mini': {'input': 0.0003, 'output': 0.0012},
}


# ============================================================================
# Usage Logging
# ============================================================================

def load_usage_log() -> dict:
    """Load usage log from file."""
    if not USAGE_LOG_FILE.exists():
        return {
            'entries': [],
            'totals': {
                'input_tokens': 0,
                'output_tokens': 0,
                'images': 0,
                'estimated_cost': 0.0
            },
            'by_model': {},
            'by_feature': {},
            'session_start': datetime.now().isoformat()
        }
    try:
        with open(USAGE_LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return load_usage_log.__wrapped__()


def save_usage_log(log: dict):
    """Save usage log to file."""
    DATA_DIR.mkdir(exist_ok=True)
    with open(USAGE_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2, default=str)


def log_api_call(
    model: str,
    feature: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    is_image: bool = False,
    image_size: str = "",
    image_quality: str = "standard"
):
    """
    Log an API call for tracking.
    
    Args:
        model: The model used (e.g., 'gpt-4.1', 'ft:gpt-4o-mini:...')
        feature: What feature used it ('idea_generation', 'newsletter_generation', 'image', etc.)
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        is_image: Whether this was an image generation
        image_size: Image size for DALL-E
        image_quality: 'standard' or 'hd'
    """
    log = load_usage_log()
    
    # Calculate cost
    cost = 0.0
    if is_image:
        if image_quality == 'hd':
            cost = PRICING.get('dall-e-3-hd', {}).get('per_image', 0.08)
        else:
            cost = PRICING.get('dall-e-3', {}).get('per_image', 0.04)
    else:
        # Find matching pricing
        model_key = model
        if model.startswith('ft:'):
            model_key = 'ft:gpt-4o-mini'  # Use fine-tuned pricing
        
        pricing = PRICING.get(model_key, PRICING.get('gpt-4.1-mini', {}))
        cost = (input_tokens / 1000) * pricing.get('input', 0.001)
        cost += (output_tokens / 1000) * pricing.get('output', 0.002)
    
    # Create entry
    entry = {
        'timestamp': datetime.now().isoformat(),
        'model': model,
        'feature': feature,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'is_image': is_image,
        'cost': round(cost, 6)
    }
    
    log['entries'].append(entry)
    
    # Update totals
    log['totals']['input_tokens'] += input_tokens
    log['totals']['output_tokens'] += output_tokens
    if is_image:
        log['totals']['images'] += 1
    log['totals']['estimated_cost'] += cost
    
    # Update by model
    if model not in log['by_model']:
        log['by_model'][model] = {'calls': 0, 'tokens': 0, 'cost': 0.0}
    log['by_model'][model]['calls'] += 1
    log['by_model'][model]['tokens'] += input_tokens + output_tokens
    log['by_model'][model]['cost'] += cost
    
    # Update by feature
    if feature not in log['by_feature']:
        log['by_feature'][feature] = {'calls': 0, 'tokens': 0, 'cost': 0.0}
    log['by_feature'][feature]['calls'] += 1
    log['by_feature'][feature]['tokens'] += input_tokens + output_tokens
    log['by_feature'][feature]['cost'] += cost
    
    save_usage_log(log)
    
    return entry


def get_usage_summary() -> dict:
    """Get a summary of API usage."""
    log = load_usage_log()
    
    # Calculate session duration
    session_start = log.get('session_start')
    if session_start:
        try:
            start_dt = datetime.fromisoformat(session_start)
            duration = datetime.now() - start_dt
            duration_str = f"{duration.days}d {duration.seconds // 3600}h"
        except:
            duration_str = "Unknown"
    else:
        duration_str = "Unknown"
    
    return {
        'total_calls': len(log.get('entries', [])),
        'input_tokens': log.get('totals', {}).get('input_tokens', 0),
        'output_tokens': log.get('totals', {}).get('output_tokens', 0),
        'total_tokens': log.get('totals', {}).get('input_tokens', 0) + log.get('totals', {}).get('output_tokens', 0),
        'images_generated': log.get('totals', {}).get('images', 0),
        'estimated_cost': round(log.get('totals', {}).get('estimated_cost', 0), 4),
        'by_model': log.get('by_model', {}),
        'by_feature': log.get('by_feature', {}),
        'session_duration': duration_str,
    }


def get_recent_calls(limit: int = 20) -> list:
    """Get recent API calls."""
    log = load_usage_log()
    entries = log.get('entries', [])
    return list(reversed(entries[-limit:]))


def reset_usage_log():
    """Reset usage log (start new session)."""
    new_log = {
        'entries': [],
        'totals': {
            'input_tokens': 0,
            'output_tokens': 0,
            'images': 0,
            'estimated_cost': 0.0
        },
        'by_model': {},
        'by_feature': {},
        'session_start': datetime.now().isoformat()
    }
    save_usage_log(new_log)


# ============================================================================
# Fine-tuned Model Stats
# ============================================================================

def get_fine_tuned_model_stats() -> dict:
    """Get statistics about fine-tuned models."""
    try:
        from fine_tuning import (
            load_fine_tuning_status,
            get_active_fine_tuned_model,
            list_fine_tuned_models,
            get_training_metrics
        )
        
        status = load_fine_tuning_status()
        active = get_active_fine_tuned_model()
        
        # Get training metrics if available
        jobs = status.get('jobs', [])
        latest_job = jobs[-1] if jobs else None
        
        metrics = {}
        if latest_job:
            job_id = latest_job.get('job_id')
            if job_id:
                try:
                    metrics = get_training_metrics(job_id)
                except:
                    pass
        
        return {
            'active_model': active,
            'total_jobs': len(jobs),
            'successful_jobs': sum(1 for j in jobs if j.get('status') == 'succeeded'),
            'latest_job': latest_job,
            'training_metrics': metrics,
            'is_using_fine_tuned': active is not None
        }
    except ImportError:
        return {
            'active_model': None,
            'error': 'Fine-tuning module not available'
        }


# ============================================================================
# OpenAI Account Info (requires API access)
# ============================================================================

def get_openai_models() -> list:
    """Get list of available models from OpenAI."""
    try:
        models = client.models.list()
        
        # Filter and categorize
        gpt_models = []
        fine_tuned_models = []
        other_models = []
        
        for model in models.data:
            model_id = model.id
            if model_id.startswith('ft:'):
                fine_tuned_models.append({
                    'id': model_id,
                    'created': datetime.fromtimestamp(model.created).isoformat(),
                    'type': 'fine-tuned'
                })
            elif 'gpt' in model_id:
                gpt_models.append({
                    'id': model_id,
                    'type': 'gpt'
                })
            elif 'dall-e' in model_id:
                other_models.append({
                    'id': model_id,
                    'type': 'image'
                })
        
        return {
            'gpt_models': sorted(gpt_models, key=lambda x: x['id']),
            'fine_tuned_models': fine_tuned_models,
            'other_models': other_models
        }
    except Exception as e:
        return {'error': str(e)}


def check_api_health() -> dict:
    """Check OpenAI API health and connection."""
    try:
        # Quick test call
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": "Say 'OK'"}],
            max_tokens=5
        )
        
        return {
            'status': 'healthy',
            'response_time': 'fast',
            'model_access': True
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


# ============================================================================
# Dashboard Data
# ============================================================================

def get_dashboard_data() -> dict:
    """Get all data needed for the dashboard."""
    return {
        'usage': get_usage_summary(),
        'recent_calls': get_recent_calls(10),
        'fine_tuning': get_fine_tuned_model_stats(),
        'api_health': check_api_health(),
        'pricing': PRICING
    }








