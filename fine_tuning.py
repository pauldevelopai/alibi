"""
Fine-Tuning Pipeline for Newsletter Generation

This module handles:
1. Exporting newsletters as training data (idea → newsletter pairs)
2. Uploading to OpenAI for fine-tuning
3. Managing fine-tuning jobs
4. Using fine-tuned models for generation

OpenAI Fine-tuning Pricing (as of Jan 2025):

GPT-4o-mini (gpt-4o-mini-2024-07-18):
- Training: $0.30 per 1M tokens ($0.0003/1K)
- Input: $0.15 per 1M tokens ($0.00015/1K)
- Output: $0.60 per 1M tokens ($0.0006/1K)
- Good for: Short tasks, style prompts, headlines
- Limitation: Struggles with 1000+ word generation

GPT-4o (gpt-4o-2024-08-06) - RECOMMENDED:
- Training: $25.00 per 1M tokens ($0.025/1K)  
- Input: $3.75 per 1M tokens ($0.00375/1K)
- Output: $15.00 per 1M tokens ($0.015/1K)
- Good for: Full newsletter generation, complex reasoning
- Your voice + powerful reasoning in ONE model
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import hashlib

from dotenv import load_dotenv
from openai import OpenAI
from bs4 import BeautifulSoup
import tiktoken

load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Paths
DATA_DIR = Path(__file__).parent / "data"
RAW_NEWSLETTERS_FILE = DATA_DIR / "newsletters_raw.jsonl"
TRAINING_DATA_FILE = DATA_DIR / "fine_tuning_training.jsonl"
FINE_TUNING_STATUS_FILE = DATA_DIR / "fine_tuning_status.json"

# Models available for fine-tuning
FINE_TUNABLE_MODELS = [
    "gpt-4o-2024-08-06",       # RECOMMENDED: Your voice + powerful reasoning
    "gpt-4o-mini-2024-07-18",  # Budget option - good for style prompts only
    "gpt-3.5-turbo-0125",      # Legacy - not recommended
]

# Model descriptions for UI
MODEL_INFO = {
    "gpt-4o-2024-08-06": {
        "name": "GPT-4o (Recommended)",
        "description": "Full newsletter generation with your voice. Single-stage, no need for GPT-4.1 fallback.",
        "training_cost_per_1m": 25.00,
        "input_cost_per_1m": 3.75,
        "output_cost_per_1m": 15.00,
        "capabilities": ["Full 1000+ word newsletters", "Complex reasoning", "Your unique voice"],
        "recommended_for": "full_newsletter"
    },
    "gpt-4o-mini-2024-07-18": {
        "name": "GPT-4o-mini (Budget)",
        "description": "Good for style prompts and headlines, but needs GPT-4.1 for full generation.",
        "training_cost_per_1m": 0.30,
        "input_cost_per_1m": 0.15,
        "output_cost_per_1m": 0.60,
        "capabilities": ["Headlines", "Style prompts", "Short tasks"],
        "recommended_for": "style_prompts"
    },
    "gpt-3.5-turbo-0125": {
        "name": "GPT-3.5 Turbo (Legacy)",
        "description": "Not recommended - limited capabilities.",
        "training_cost_per_1m": 0.30,
        "input_cost_per_1m": 0.15,
        "output_cost_per_1m": 0.60,
        "capabilities": ["Basic tasks only"],
        "recommended_for": "none"
    }
}

# Default to gpt-4o for best quality
DEFAULT_BASE_MODEL = "gpt-4o-2024-08-06"

# For backwards compatibility - track what kind of model is active
def get_model_tier(model_id: str) -> str:
    """
    Determine if a fine-tuned model is based on gpt-4o or gpt-4o-mini.
    Returns: 'gpt-4o', 'gpt-4o-mini', or 'unknown'
    """
    if not model_id:
        return 'unknown'
    model_lower = model_id.lower()
    if 'gpt-4o-mini' in model_lower:
        return 'gpt-4o-mini'
    elif 'gpt-4o' in model_lower:
        return 'gpt-4o'
    elif 'gpt-3.5' in model_lower or 'gpt-35' in model_lower:
        return 'gpt-3.5'
    return 'unknown'


# ============================================================================
# Token Counting
# ============================================================================

def count_tokens(text: str, model: str = "gpt-4o-mini-2024-07-18") -> int:
    """Count tokens in text."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def estimate_training_cost(training_data: List[dict], base_model: str = DEFAULT_BASE_MODEL) -> dict:
    """
    Estimate the cost of fine-tuning.
    
    OpenAI charges for training tokens (the full conversation is used for training).
    After training, you pay input/output costs for each API call.
    """
    total_tokens = 0
    
    for example in training_data:
        # Count tokens in the conversation
        for message in example.get('messages', []):
            total_tokens += count_tokens(message.get('content', ''))
    
    # Training cost per 1M tokens (Jan 2025 pricing)
    training_cost_per_1m = {
        "gpt-4o-2024-08-06": 25.00,
        "gpt-4o-mini-2024-07-18": 0.30,
        "gpt-3.5-turbo-0125": 0.30,
    }
    
    # Usage cost per 1M tokens after training
    usage_cost_per_1m = {
        "gpt-4o-2024-08-06": {"input": 3.75, "output": 15.00},
        "gpt-4o-mini-2024-07-18": {"input": 0.15, "output": 0.60},
        "gpt-3.5-turbo-0125": {"input": 0.15, "output": 0.60},
    }
    
    training_rate = training_cost_per_1m.get(base_model, 25.00)
    estimated_training_cost = (total_tokens / 1_000_000) * training_rate
    
    # Estimate per-newsletter usage cost (assume ~500 input, ~2000 output tokens)
    usage_rates = usage_cost_per_1m.get(base_model, {"input": 3.75, "output": 15.00})
    per_newsletter_cost = (500 / 1_000_000) * usage_rates["input"] + (2000 / 1_000_000) * usage_rates["output"]
    
    model_info = MODEL_INFO.get(base_model, {})
    
    return {
        'total_tokens': total_tokens,
        'estimated_training_cost_usd': round(estimated_training_cost, 2),
        'per_newsletter_cost_usd': round(per_newsletter_cost, 4),
        'base_model': base_model,
        'model_name': model_info.get('name', base_model),
        'model_tier': get_model_tier(base_model),
        'recommended_for': model_info.get('recommended_for', 'unknown'),
        'num_examples': len(training_data),
        # Legacy field for backwards compatibility
        'estimated_cost_usd': round(estimated_training_cost, 2)
    }


# ============================================================================
# Training Data Preparation
# ============================================================================

def html_to_text(html: str) -> str:
    """Convert HTML to plain text."""
    if not html:
        return ""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script and style elements
    for element in soup(['script', 'style']):
        element.decompose()
    
    # Get text
    text = soup.get_text(separator='\n')
    
    # Clean up whitespace
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(line for line in lines if line)
    
    return text


def extract_newsletter_summary(newsletter: dict) -> str:
    """
    Extract a brief summary/idea from a newsletter.
    This simulates what the user would input as an "idea" for fine-tuning.
    """
    title = newsletter.get('title', '')
    subtitle = newsletter.get('subtitle', '')
    
    # Create an "idea" prompt that would generate this newsletter
    idea = f"Write a newsletter titled '{title}'"
    if subtitle:
        idea += f" with the focus: {subtitle}"
    
    return idea


def load_newsletters() -> List[dict]:
    """Load all raw newsletters."""
    if not RAW_NEWSLETTERS_FILE.exists():
        return []
    
    newsletters = []
    with open(RAW_NEWSLETTERS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                newsletters.append(json.loads(line))
    return newsletters


def prepare_training_example(newsletter: dict, system_prompt: str) -> dict:
    """
    Convert a newsletter to a fine-tuning training example.
    
    Format follows OpenAI's chat fine-tuning format:
    {
        "messages": [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ]
    }
    """
    # Extract the idea/prompt
    idea = extract_newsletter_summary(newsletter)
    
    # Get the newsletter content
    content_html = newsletter.get('content_html', '')
    content_text = html_to_text(content_html)
    
    if not content_text or len(content_text) < 100:
        return None
    
    # Create the training example
    return {
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": idea
            },
            {
                "role": "assistant",
                "content": content_text
            }
        ]
    }


def get_system_prompt() -> str:
    """Get the system prompt for fine-tuning."""
    return """You are Paul McNally's AI writing assistant, specifically trained on his newsletter "Whose Intelligence Is It Anyway?" about AI developments in Africa.

Your writing style:
- Conversational but informative tone
- Strong opening hooks that grab attention
- Clear section structure with engaging headings
- Use of rhetorical questions to engage readers
- Balance of technical insight with accessible explanations
- Africa-focused perspective on AI and technology
- Personal anecdotes and observations where relevant
- Call-to-action elements for reader engagement

Format newsletters in Markdown with:
- Compelling main headline
- Engaging introduction (2-3 paragraphs)
- Clear section headers (##)
- Bullet points for lists and key takeaways
- Links to sources where relevant
- Strong closing with call-to-action"""


def export_training_data(
    output_file: Path = TRAINING_DATA_FILE,
    min_length: int = 500,
    max_length: int = 15000
) -> dict:
    """
    Export all newsletters as fine-tuning training data.
    
    Returns statistics about the export.
    """
    newsletters = load_newsletters()
    system_prompt = get_system_prompt()
    
    training_examples = []
    skipped = {'too_short': 0, 'too_long': 0, 'invalid': 0}
    
    for nl in newsletters:
        content_text = html_to_text(nl.get('content_html', ''))
        
        # Filter by length
        if len(content_text) < min_length:
            skipped['too_short'] += 1
            continue
        if len(content_text) > max_length:
            skipped['too_long'] += 1
            continue
        
        example = prepare_training_example(nl, system_prompt)
        if example:
            training_examples.append(example)
        else:
            skipped['invalid'] += 1
    
    # Write training data in JSONL format
    with open(output_file, 'w', encoding='utf-8') as f:
        for example in training_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    # Estimate costs
    cost_estimate = estimate_training_cost(training_examples)
    
    result = {
        'total_newsletters': len(newsletters),
        'training_examples': len(training_examples),
        'skipped': skipped,
        'output_file': str(output_file),
        'cost_estimate': cost_estimate,
        'exported_at': datetime.now().isoformat()
    }
    
    return result


# ============================================================================
# Fine-Tuning Job Management
# ============================================================================

def load_fine_tuning_status() -> dict:
    """Load fine-tuning status from file."""
    if not FINE_TUNING_STATUS_FILE.exists():
        return {
            'jobs': [],
            'active_model': None,
            'last_updated': None
        }
    with open(FINE_TUNING_STATUS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_fine_tuning_status(status: dict):
    """Save fine-tuning status."""
    status['last_updated'] = datetime.now().isoformat()
    with open(FINE_TUNING_STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)


def upload_training_file(training_file: Path = TRAINING_DATA_FILE) -> str:
    """
    Upload training data file to OpenAI.
    Returns the file ID.
    """
    if not training_file.exists():
        raise FileNotFoundError(f"Training file not found: {training_file}")
    
    with open(training_file, 'rb') as f:
        response = client.files.create(
            file=f,
            purpose='fine-tune'
        )
    
    return response.id


def create_fine_tuning_job(
    training_file_id: str,
    base_model: str = DEFAULT_BASE_MODEL,
    suffix: str = "newsletter-paul",
    n_epochs: int = 3
) -> dict:
    """
    Create a fine-tuning job.
    
    Args:
        training_file_id: The uploaded training file ID
        base_model: Base model to fine-tune
        suffix: Custom suffix for the model name
        n_epochs: Number of training epochs (1-10)
    
    Returns job details.
    """
    job = client.fine_tuning.jobs.create(
        training_file=training_file_id,
        model=base_model,
        suffix=suffix,
        hyperparameters={
            "n_epochs": n_epochs
        }
    )
    
    # Save to status
    status = load_fine_tuning_status()
    status['jobs'].append({
        'job_id': job.id,
        'status': job.status,
        'base_model': base_model,
        'suffix': suffix,
        'created_at': datetime.now().isoformat(),
        'training_file_id': training_file_id,
        'fine_tuned_model': None
    })
    save_fine_tuning_status(status)
    
    return {
        'job_id': job.id,
        'status': job.status,
        'base_model': base_model,
        'created_at': str(job.created_at)
    }


def check_job_status(job_id: str) -> dict:
    """Check the status of a fine-tuning job."""
    job = client.fine_tuning.jobs.retrieve(job_id)
    
    result = {
        'job_id': job.id,
        'status': job.status,  # validating_files, queued, running, succeeded, failed, cancelled
        'base_model': job.model,
        'fine_tuned_model': job.fine_tuned_model,
        'created_at': str(job.created_at),
        'finished_at': str(job.finished_at) if job.finished_at else None,
        'trained_tokens': job.trained_tokens,
        'error': job.error.message if job.error else None
    }
    
    # Update local status
    status = load_fine_tuning_status()
    for saved_job in status['jobs']:
        if saved_job['job_id'] == job_id:
            saved_job['status'] = job.status
            saved_job['fine_tuned_model'] = job.fine_tuned_model
            if job.status == 'succeeded' and job.fine_tuned_model:
                status['active_model'] = job.fine_tuned_model
            break
    save_fine_tuning_status(status)
    
    return result


def list_fine_tuning_jobs() -> List[dict]:
    """List all fine-tuning jobs."""
    jobs = client.fine_tuning.jobs.list(limit=20)
    
    return [{
        'job_id': job.id,
        'status': job.status,
        'base_model': job.model,
        'fine_tuned_model': job.fine_tuned_model,
        'created_at': str(job.created_at)
    } for job in jobs.data]


def cancel_job(job_id: str) -> dict:
    """Cancel a running fine-tuning job."""
    job = client.fine_tuning.jobs.cancel(job_id)
    return {
        'job_id': job.id,
        'status': job.status
    }


def get_job_events(job_id: str, limit: int = 20) -> List[dict]:
    """Get events/logs for a fine-tuning job."""
    events = client.fine_tuning.jobs.list_events(
        fine_tuning_job_id=job_id,
        limit=limit
    )
    
    return [{
        'message': event.message,
        'created_at': str(event.created_at),
        'level': event.level
    } for event in events.data]


# ============================================================================
# Model Management
# ============================================================================

def get_active_fine_tuned_model() -> Optional[str]:
    """Get the currently active fine-tuned model ID."""
    status = load_fine_tuning_status()
    return status.get('active_model')


def set_active_model(model_id: str):
    """Set the active fine-tuned model."""
    status = load_fine_tuning_status()
    status['active_model'] = model_id
    save_fine_tuning_status(status)


def list_fine_tuned_models() -> List[dict]:
    """List all available fine-tuned models."""
    models = client.models.list()
    
    fine_tuned = []
    for model in models.data:
        if 'ft:' in model.id:
            fine_tuned.append({
                'model_id': model.id,
                'created': str(model.created),
                'owned_by': model.owned_by
            })
    
    return fine_tuned


def delete_fine_tuned_model(model_id: str) -> bool:
    """Delete a fine-tuned model."""
    try:
        client.models.delete(model_id)
        
        # Update status if this was the active model
        status = load_fine_tuning_status()
        if status.get('active_model') == model_id:
            status['active_model'] = None
            save_fine_tuning_status(status)
        
        return True
    except Exception as e:
        print(f"Error deleting model: {e}")
        return False


# ============================================================================
# Generation with Fine-Tuned Model
# ============================================================================

def generate_with_fine_tuned_model(
    idea: str,
    model_id: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4000
) -> str:
    """
    Generate a newsletter using the fine-tuned model.
    
    Args:
        idea: The newsletter idea/topic
        model_id: Fine-tuned model ID (uses active model if not specified)
        temperature: Creativity level (0.0-1.0)
        max_tokens: Maximum length of generation
    """
    if model_id is None:
        model_id = get_active_fine_tuned_model()
    
    if not model_id:
        raise ValueError("No fine-tuned model available. Please complete fine-tuning first.")
    
    system_prompt = get_system_prompt()
    
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": idea}
        ],
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    return response.choices[0].message.content


def compare_models(
    idea: str,
    fine_tuned_model: Optional[str] = None,
    base_model: str = "gpt-4o-mini-2024-07-18",
    temperature: float = 0.7,
    max_tokens: int = 1500
) -> Dict:
    """
    Generate the same content with both base and fine-tuned models for comparison.
    
    Returns dict with 'base_output', 'fine_tuned_output', and metadata.
    """
    if fine_tuned_model is None:
        fine_tuned_model = get_active_fine_tuned_model()
    
    system_prompt = get_system_prompt()
    
    results = {
        'idea': idea,
        'base_model': base_model,
        'fine_tuned_model': fine_tuned_model,
        'base_output': None,
        'fine_tuned_output': None,
        'base_tokens': 0,
        'fine_tuned_tokens': 0,
    }
    
    # Generate with base model
    try:
        base_response = client.chat.completions.create(
            model=base_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": idea}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        results['base_output'] = base_response.choices[0].message.content
        results['base_tokens'] = base_response.usage.completion_tokens
    except Exception as e:
        results['base_output'] = f"Error: {e}"
    
    # Generate with fine-tuned model
    if fine_tuned_model:
        try:
            ft_response = client.chat.completions.create(
                model=fine_tuned_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": idea}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            results['fine_tuned_output'] = ft_response.choices[0].message.content
            results['fine_tuned_tokens'] = ft_response.usage.completion_tokens
        except Exception as e:
            results['fine_tuned_output'] = f"Error: {e}"
    else:
        results['fine_tuned_output'] = "No fine-tuned model available"
    
    return results


def get_training_metrics(job_id: str) -> Dict:
    """
    Get detailed training metrics for a job including loss curves.
    """
    try:
        job = client.fine_tuning.jobs.retrieve(job_id)
        events = client.fine_tuning.jobs.list_events(
            fine_tuning_job_id=job_id,
            limit=100
        )
        
        # Parse training metrics from events
        metrics = {
            'job_id': job_id,
            'status': job.status,
            'trained_tokens': job.trained_tokens,
            'training_steps': [],
            'final_loss': None,
        }
        
        for event in events.data:
            msg = event.message
            # Parse step messages like "Step 100/300: training loss=0.1234"
            if 'Step' in msg and 'loss' in msg.lower():
                try:
                    # Extract step number and loss
                    import re
                    step_match = re.search(r'Step (\d+)', msg)
                    loss_match = re.search(r'loss[=:]?\s*([\d.]+)', msg.lower())
                    if step_match and loss_match:
                        step = int(step_match.group(1))
                        loss = float(loss_match.group(1))
                        metrics['training_steps'].append({
                            'step': step,
                            'loss': loss
                        })
                except:
                    pass
        
        # Sort by step and get final loss
        if metrics['training_steps']:
            metrics['training_steps'].sort(key=lambda x: x['step'])
            metrics['final_loss'] = metrics['training_steps'][-1]['loss']
            metrics['initial_loss'] = metrics['training_steps'][0]['loss'] if metrics['training_steps'] else None
            if metrics['initial_loss'] and metrics['final_loss']:
                metrics['loss_reduction'] = round(
                    (1 - metrics['final_loss'] / metrics['initial_loss']) * 100, 1
                )
        
        return metrics
    except Exception as e:
        return {'error': str(e)}


def get_current_job_id() -> Optional[str]:
    """Get the most recent job ID."""
    status = load_fine_tuning_status()
    jobs = status.get('jobs', [])
    if jobs:
        return jobs[-1].get('job_id')
    return None


# ============================================================================
# Full Pipeline
# ============================================================================

def run_full_pipeline(
    base_model: str = DEFAULT_BASE_MODEL,
    suffix: str = "newsletter-paul",
    n_epochs: int = 3,
    wait_for_completion: bool = False
) -> dict:
    """
    Run the complete fine-tuning pipeline:
    1. Export training data
    2. Upload to OpenAI
    3. Create fine-tuning job
    4. Optionally wait for completion
    
    Returns pipeline status.
    """
    print("=" * 60)
    print("NEWSLETTER FINE-TUNING PIPELINE")
    print("=" * 60)
    
    # Step 1: Export training data
    print("\n📝 Step 1: Exporting training data...")
    export_result = export_training_data()
    print(f"   Exported {export_result['training_examples']} newsletters")
    print(f"   Estimated cost: ${export_result['cost_estimate']['estimated_cost_usd']}")
    print(f"   Total tokens: {export_result['cost_estimate']['total_tokens']:,}")
    
    if export_result['training_examples'] < 10:
        return {
            'error': 'Not enough training examples (minimum 10 required)',
            'details': export_result
        }
    
    # Step 2: Upload training file
    print("\n📤 Step 2: Uploading training file to OpenAI...")
    file_id = upload_training_file()
    print(f"   File uploaded: {file_id}")
    
    # Step 3: Create fine-tuning job
    print(f"\n🚀 Step 3: Creating fine-tuning job (base model: {base_model})...")
    job_result = create_fine_tuning_job(
        training_file_id=file_id,
        base_model=base_model,
        suffix=suffix,
        n_epochs=n_epochs
    )
    print(f"   Job created: {job_result['job_id']}")
    print(f"   Status: {job_result['status']}")
    
    # Step 4: Optionally wait for completion
    if wait_for_completion:
        print("\n⏳ Step 4: Waiting for training to complete...")
        while True:
            time.sleep(60)  # Check every minute
            status = check_job_status(job_result['job_id'])
            print(f"   Status: {status['status']}")
            
            if status['status'] in ['succeeded', 'failed', 'cancelled']:
                if status['status'] == 'succeeded':
                    print(f"\n✅ Fine-tuning complete!")
                    print(f"   Fine-tuned model: {status['fine_tuned_model']}")
                else:
                    print(f"\n❌ Fine-tuning {status['status']}")
                    if status.get('error'):
                        print(f"   Error: {status['error']}")
                break
    else:
        print("\n⏳ Fine-tuning job submitted. Check status with check_job_status()")
    
    return {
        'export_result': export_result,
        'file_id': file_id,
        'job': job_result,
        'base_model': base_model
    }


# ============================================================================
# Incremental Training (Auto-train on publish)
# ============================================================================

def add_to_training_data(
    idea: str,
    headline: str,
    content: str,
    story_type: str = ""
) -> dict:
    """
    Add a single newsletter to the training data file.
    This is called when a newsletter is published.
    
    Returns:
        dict with 'success', 'message', 'total_examples'
    """
    if not idea or not content:
        return {'success': False, 'message': 'Missing idea or content'}
    
    # Create the training example
    example = {
        "messages": [
            {
                "role": "system",
                "content": "You are Paul McNally, a journalist who writes newsletters about AI and media. Write in a punchy, personal style with short paragraphs, specific examples, and an Africa/Global South perspective."
            },
            {
                "role": "user",
                "content": f"Write a newsletter about: {idea}"
            },
            {
                "role": "assistant",
                "content": f"# {headline}\n\n{content}" if headline else content
            }
        ]
    }
    
    # Append to training file
    DATA_DIR.mkdir(exist_ok=True)
    incremental_file = DATA_DIR / "incremental_training.jsonl"
    
    with open(incremental_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    # Count total examples
    total = 0
    if incremental_file.exists():
        with open(incremental_file, 'r', encoding='utf-8') as f:
            total = sum(1 for line in f if line.strip())
    
    return {
        'success': True,
        'message': f'Added to training data. Total new examples: {total}',
        'total_examples': total,
        'file': str(incremental_file)
    }


def get_incremental_training_count() -> int:
    """Get count of newsletters in incremental training data."""
    incremental_file = DATA_DIR / "incremental_training.jsonl"
    if not incremental_file.exists():
        return 0
    with open(incremental_file, 'r', encoding='utf-8') as f:
        return sum(1 for line in f if line.strip())


def trigger_incremental_training(
    min_new_examples: int = 5,
    base_model: str = DEFAULT_BASE_MODEL,
    suffix: str = "newsletter-paul"
) -> dict:
    """
    Trigger fine-tuning if enough new examples have accumulated.
    Combines original training data with incremental data.
    
    Args:
        min_new_examples: Minimum new examples before training (default: 5)
        base_model: Base model to fine-tune
        suffix: Model name suffix
    
    Returns:
        dict with status and details
    """
    incremental_file = DATA_DIR / "incremental_training.jsonl"
    
    if not incremental_file.exists():
        return {'triggered': False, 'reason': 'No incremental training data'}
    
    # Count new examples
    new_count = get_incremental_training_count()
    
    if new_count < min_new_examples:
        return {
            'triggered': False, 
            'reason': f'Only {new_count} new examples. Need {min_new_examples} to trigger training.',
            'current_count': new_count,
            'threshold': min_new_examples
        }
    
    # Combine original training data with incremental
    combined_file = DATA_DIR / "combined_training.jsonl"
    
    all_examples = []
    
    # Load original training data if exists
    if TRAINING_DATA_FILE.exists():
        with open(TRAINING_DATA_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    all_examples.append(json.loads(line))
    
    # Load incremental training data
    with open(incremental_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                all_examples.append(json.loads(line))
    
    # Write combined file
    with open(combined_file, 'w', encoding='utf-8') as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    # Upload and start training
    try:
        # Upload combined file
        with open(combined_file, 'rb') as f:
            uploaded = client.files.create(file=f, purpose="fine-tune")
        file_id = uploaded.id
        
        # Create job
        job = client.fine_tuning.jobs.create(
            training_file=file_id,
            model=base_model,
            suffix=suffix,
            hyperparameters={"n_epochs": 3}
        )
        
        # Save status
        status = load_fine_tuning_status()
        status['current_job_id'] = job.id
        status['jobs'].append({
            'job_id': job.id,
            'started_at': datetime.now().isoformat(),
            'status': 'running',
            'base_model': base_model,
            'training_examples': len(all_examples),
            'new_examples': new_count,
            'triggered': 'auto'
        })
        save_fine_tuning_status(status)
        
        # Clear incremental file (data is now in combined/training)
        incremental_file.unlink()
        
        return {
            'triggered': True,
            'job_id': job.id,
            'total_examples': len(all_examples),
            'new_examples': new_count,
            'file_id': file_id,
            'message': f'Training started with {len(all_examples)} total examples ({new_count} new)'
        }
        
    except Exception as e:
        return {
            'triggered': False,
            'error': str(e),
            'reason': 'Failed to start training'
        }


def should_auto_train() -> dict:
    """Check if auto-training should be triggered."""
    count = get_incremental_training_count()
    threshold = 5  # Can be made configurable
    
    return {
        'should_train': count >= threshold,
        'current_count': count,
        'threshold': threshold,
        'needed': max(0, threshold - count)
    }


# ============================================================================
# CLI Interface
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Newsletter Fine-Tuning Pipeline")
    parser.add_argument('command', choices=[
        'export', 'upload', 'start', 'status', 'list', 'models', 'pipeline'
    ])
    parser.add_argument('--job-id', help="Job ID for status check")
    parser.add_argument('--model', default=DEFAULT_BASE_MODEL, help="Base model")
    parser.add_argument('--wait', action='store_true', help="Wait for completion")
    
    args = parser.parse_args()
    
    if args.command == 'export':
        result = export_training_data()
        print(json.dumps(result, indent=2))
    
    elif args.command == 'upload':
        file_id = upload_training_file()
        print(f"Uploaded: {file_id}")
    
    elif args.command == 'status':
        if args.job_id:
            result = check_job_status(args.job_id)
        else:
            result = load_fine_tuning_status()
        print(json.dumps(result, indent=2, default=str))
    
    elif args.command == 'list':
        jobs = list_fine_tuning_jobs()
        print(json.dumps(jobs, indent=2))
    
    elif args.command == 'models':
        models = list_fine_tuned_models()
        print(json.dumps(models, indent=2))
    
    elif args.command == 'pipeline':
        result = run_full_pipeline(
            base_model=args.model,
            wait_for_completion=args.wait
        )
        print(json.dumps(result, indent=2, default=str))

