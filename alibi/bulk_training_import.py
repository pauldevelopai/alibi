"""
Bulk Training Data Import System
Handles ingestion of large datasets (GBs) for improving AI vision
"""
import asyncio
import json
import gzip
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, AsyncIterator
from datetime import datetime
from dataclasses import dataclass, asdict
import base64
from io import BytesIO

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from alibi.auth import get_current_user, User
from alibi.training_agent import get_training_agent, SecurityTrainingExample


router = APIRouter(prefix="/training", tags=["bulk_import"])


class BulkImportStatus(BaseModel):
    """Status of a bulk import job"""
    job_id: str
    status: str  # "processing", "completed", "failed"
    total_items: int
    processed_items: int
    success_count: int
    error_count: int
    started_at: str
    completed_at: Optional[str] = None
    errors: List[str] = []


class ImportProgress:
    """Track import progress"""
    def __init__(self):
        self.jobs: Dict[str, BulkImportStatus] = {}
    
    def create_job(self, job_id: str) -> BulkImportStatus:
        """Create a new import job"""
        status = BulkImportStatus(
            job_id=job_id,
            status="processing",
            total_items=0,
            processed_items=0,
            success_count=0,
            error_count=0,
            started_at=datetime.utcnow().isoformat(),
            errors=[]
        )
        self.jobs[job_id] = status
        return status
    
    def update(self, job_id: str, **kwargs):
        """Update job status"""
        if job_id in self.jobs:
            for key, value in kwargs.items():
                setattr(self.jobs[job_id], key, value)
    
    def get(self, job_id: str) -> Optional[BulkImportStatus]:
        """Get job status"""
        return self.jobs.get(job_id)


# Global progress tracker
_import_progress = ImportProgress()


@router.post("/bulk-import")
async def bulk_import_training_data(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Import large training dataset
    
    Supports:
    - JSONL files (plain or .gz compressed)
    - Up to several GB
    - Background processing
    - Progress tracking
    
    Expected format per line:
    {
        "image_base64": "...",  // Or "image_url"
        "description": "Person entering building",
        "category": "baseline",  // Or "suspicious_activity", etc.
        "security_relevance": "Normal entry pattern",
        "confidence": 0.85
    }
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate file type
    filename = file.filename or ""
    if not (filename.endswith('.jsonl') or filename.endswith('.jsonl.gz')):
        raise HTTPException(
            status_code=400,
            detail="Only JSONL or JSONL.GZ files supported"
        )
    
    # Create job
    job_id = f"import-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    job = _import_progress.create_job(job_id)
    
    # Read file content
    content = await file.read()
    
    # Process in background
    background_tasks.add_task(
        process_bulk_import,
        job_id,
        content,
        filename.endswith('.gz')
    )
    
    return {
        "success": True,
        "job_id": job_id,
        "message": f"Import started. Check /training/import-status/{job_id} for progress."
    }


@router.get("/import-status/{job_id}")
async def get_import_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of a bulk import job"""
    status = _import_progress.get(job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return status


async def process_bulk_import(job_id: str, content: bytes, is_compressed: bool):
    """Process bulk import in background"""
    try:
        agent = get_training_agent()
        
        # Decompress if needed
        if is_compressed:
            content = gzip.decompress(content)
        
        # Decode to string
        text = content.decode('utf-8')
        lines = text.strip().split('\n')
        
        _import_progress.update(job_id, total_items=len(lines))
        
        success = 0
        errors = []
        
        for i, line in enumerate(lines):
            try:
                data = json.loads(line)
                
                # Convert to SecurityTrainingExample
                example = SecurityTrainingExample(
                    example_id=f"{job_id}-{i}",
                    timestamp=datetime.utcnow().isoformat(),
                    category=data.get('category', 'baseline'),
                    scene_description=data['description'],
                    objects_detected=data.get('objects', []),
                    activities=data.get('activities', []),
                    security_relevance=data.get('security_relevance', 'Training data'),
                    confidence_score=data.get('confidence', 0.8),
                    image_hash=hashlib.md5(line.encode()).hexdigest(),
                    metadata=data.get('metadata', {})
                )
                
                # Save to store
                agent._save_example(example)
                success += 1
                
            except Exception as e:
                errors.append(f"Line {i}: {str(e)}")
                if len(errors) > 100:  # Cap error logging
                    errors.append(f"... and {len(lines) - i} more errors")
                    break
            
            # Update progress every 100 items
            if i % 100 == 0:
                _import_progress.update(
                    job_id,
                    processed_items=i,
                    success_count=success,
                    error_count=len(errors)
                )
        
        # Final update
        _import_progress.update(
            job_id,
            status="completed",
            processed_items=len(lines),
            success_count=success,
            error_count=len(errors),
            completed_at=datetime.utcnow().isoformat(),
            errors=errors[:100]  # Keep first 100 errors
        )
        
    except Exception as e:
        _import_progress.update(
            job_id,
            status="failed",
            completed_at=datetime.utcnow().isoformat(),
            errors=[str(e)]
        )


@router.get("/export-bulk-dataset")
async def export_bulk_dataset(
    format: str = "jsonl.gz",
    min_confidence: float = 0.7,
    current_user: User = Depends(get_current_user)
):
    """
    Export training dataset in bulk format
    
    Returns compressed JSONL for efficient transfer
    Optimized for multi-GB datasets
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    agent = get_training_agent()
    examples = agent.load_examples(min_confidence=min_confidence)
    
    if not examples:
        raise HTTPException(status_code=404, detail="No training data available")
    
    # Generate JSONL
    lines = []
    for ex in examples:
        line = json.dumps(asdict(ex), ensure_ascii=False)
        lines.append(line)
    
    content = '\n'.join(lines).encode('utf-8')
    
    # Compress
    if format == "jsonl.gz":
        buffer = BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='wb') as gz:
            gz.write(content)
        content = buffer.getvalue()
        media_type = "application/gzip"
        filename = f"training_data_{datetime.utcnow().strftime('%Y%m%d')}.jsonl.gz"
    else:
        media_type = "application/x-ndjson"
        filename = f"training_data_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
    
    return StreamingResponse(
        BytesIO(content),
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(content))
        }
    )


@router.post("/import-from-url")
async def import_from_url(
    url: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Import training data from a URL
    Useful for importing from cloud storage, S3, etc.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    import httpx
    
    # Create job
    job_id = f"import-url-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    job = _import_progress.create_job(job_id)
    
    # Download and process in background
    async def download_and_process():
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                content = response.content
                
                is_compressed = url.endswith('.gz')
                await process_bulk_import(job_id, content, is_compressed)
                
        except Exception as e:
            _import_progress.update(
                job_id,
                status="failed",
                completed_at=datetime.utcnow().isoformat(),
                errors=[f"Download failed: {str(e)}"]
            )
    
    background_tasks.add_task(download_and_process)
    
    return {
        "success": True,
        "job_id": job_id,
        "message": f"Import from URL started. Check /training/import-status/{job_id} for progress."
    }


@router.delete("/clear-training-data")
async def clear_training_data(
    confirm: str,
    current_user: User = Depends(get_current_user)
):
    """
    Clear all training data (use with caution!)
    Requires confirmation string "DELETE_ALL_TRAINING_DATA"
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if confirm != "DELETE_ALL_TRAINING_DATA":
        raise HTTPException(
            status_code=400,
            detail="Must provide confirmation string: DELETE_ALL_TRAINING_DATA"
        )
    
    from alibi.training_agent import TRAINING_AGENT_DATA
    
    if TRAINING_AGENT_DATA.exists():
        # Backup before deleting
        backup_path = TRAINING_AGENT_DATA.parent / f"training_agent_backup_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.jsonl"
        TRAINING_AGENT_DATA.rename(backup_path)
        
        return {
            "success": True,
            "message": f"Training data cleared. Backup saved to: {backup_path.name}"
        }
    
    return {
        "success": True,
        "message": "No training data to clear"
    }
