"""
Data Collection API Endpoints
Trigger real training data collection from Hugging Face
"""
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from alibi.auth import get_current_user, User
from pathlib import Path
import asyncio
from typing import Optional

router = APIRouter(prefix="/data-collection", tags=["data_collection"])


@router.post("/collect-from-huggingface")
async def start_huggingface_collection(
    background_tasks: BackgroundTasks,
    num_coco: int = 100,
    num_open_images: int = 50,
    num_security: int = 50,
    current_user: User = Depends(get_current_user)
):
    """
    Start collecting real training data from Hugging Face datasets
    
    This will:
    - Download security-relevant images from COCO, Open Images, and security datasets
    - Process and categorize them
    - Save them ready for OpenAI fine-tuning
    
    Note: This runs in the background and may take 10-30 minutes
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Check if datasets library is available
        from alibi.data_collection import collect_training_data
    except ImportError:
        return {
            "success": False,
            "error": "Hugging Face datasets not installed",
            "install_command": "pip install datasets pillow requests"
        }
    
    # Start collection in background
    async def run_collection():
        try:
            result = await collect_training_data(
                num_coco=num_coco,
                num_open_images=num_open_images,
                num_security=num_security
            )
            print(f"✅ Collection complete: {result}")
        except Exception as e:
            print(f"❌ Collection failed: {e}")
    
    background_tasks.add_task(run_collection)
    
    return {
        "success": True,
        "message": "Data collection started in background",
        "estimated_time": "10-30 minutes",
        "target_examples": num_coco + num_open_images + num_security,
        "check_status_at": "/data-collection/status"
    }


@router.get("/status")
async def get_collection_status(current_user: User = Depends(get_current_user)):
    """Get status of data collection"""
    try:
        from alibi.data_collection import HuggingFaceCollector
        
        collector = HuggingFaceCollector()
        stats = collector.get_collection_stats()
        
        return {
            "success": True,
            "stats": stats,
            "data_directory": str(collector.output_dir)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/convert-to-openai-format")
async def convert_to_openai_format(
    include_images: bool = False,
    current_user: User = Depends(get_current_user)
):
    """
    Convert collected data to OpenAI fine-tuning format
    
    Args:
        include_images: If True, embed images as base64 (larger file, but portable)
                       If False, use file paths (smaller, requires files)
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        from alibi.data_collection.openai_formatter import convert_collected_data_to_openai
        
        result = convert_collected_data_to_openai(include_images=include_images)
        
        return result
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/download-training-dataset")
async def download_training_dataset(
    format: str = "openai",
    current_user: User = Depends(get_current_user)
):
    """
    Download the prepared training dataset
    
    Args:
        format: "openai" or "raw"
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if format == "openai":
        file_path = Path("alibi/data/hf_training_data/openai_training_dataset.jsonl")
    else:
        file_path = Path("alibi/data/hf_training_data/collected_examples.jsonl")
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Dataset not found. Run collection first."
        )
    
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/x-ndjson"
    )


@router.post("/install-dependencies")
async def install_dependencies(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Install required dependencies for data collection
    
    Installs:
    - datasets (Hugging Face)
    - pillow (image processing)
    - requests (HTTP)
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    import subprocess
    
    def install():
        try:
            subprocess.run(
                ["pip", "install", "datasets", "pillow", "requests"],
                check=True,
                capture_output=True
            )
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Installation failed: {e}")
    
    background_tasks.add_task(install)
    
    return {
        "success": True,
        "message": "Installing dependencies in background...",
        "packages": ["datasets", "pillow", "requests"]
    }
