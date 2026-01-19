"""
Training Data Management
Collect and manage data to improve OpenAI Vision for South African context
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import datetime
from typing import Dict, List
import json
from pathlib import Path
from alibi.auth import get_current_user, User

router = APIRouter(prefix="/camera", tags=["training"])

# Path for training data feedback
FEEDBACK_FILE = Path("alibi/data/vision_feedback.jsonl")
FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)


@router.get("/training", response_class=HTMLResponse)
async def training_page():
    """Training Data page - Improve AI vision"""
    return HTMLResponse(content=TRAINING_HTML)


@router.get("/training/stats")
async def get_training_stats(current_user: User = Depends(get_current_user)):
    """Get training data statistics"""
    import sys
    print(f"[TRAINING_STATS] Called by user: {current_user.username} ({current_user.role})", file=sys.stderr)
    
    from alibi.training_agent import get_training_agent, get_history_manager
    
    agent = get_training_agent()
    print(f"[TRAINING_STATS] Agent loaded", file=sys.stderr)
    
    history_mgr = get_history_manager()
    print(f"[TRAINING_STATS] History manager loaded", file=sys.stderr)
    
    # Get automatic collection stats
    auto_stats = agent.get_collection_stats()
    print(f"[TRAINING_STATS] Auto stats: {auto_stats}", file=sys.stderr)
    
    # Get fine-tuning history
    history = history_mgr.get_history()
    deployed_version = history_mgr.get_deployed_version()
    print(f"[TRAINING_STATS] History count: {len(history)}, Deployed: {deployed_version is not None}", file=sys.stderr)
    
    # Get manual feedback stats
    manual_feedback = 0
    manual_avg_accuracy = 0
    if FEEDBACK_FILE.exists():
        feedbacks = []
        with open(FEEDBACK_FILE, 'r') as f:
            for line in f:
                try:
                    feedbacks.append(json.loads(line))
                except:
                    continue
        manual_feedback = len(feedbacks)
        if feedbacks:
            accuracies = [f.get("accuracy_rating", 0) for f in feedbacks if f.get("accuracy_rating")]
            manual_avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
    
    # Load all feedback if file exists
    feedbacks = []
    if FEEDBACK_FILE.exists():
        with open(FEEDBACK_FILE, 'r') as f:
            for line in f:
                try:
                    feedbacks.append(json.loads(line))
                except:
                    continue
    
    # If no data at all, return empty state
    if not feedbacks and auto_stats["total_examples"] == 0:
        return {
            "total_feedback": 0,
            "avg_accuracy": 0,
            "top_corrections": [],
            "recent_feedback": [],
            "readiness": {
                "ready_for_fine_tuning": False,
                "feedback_needed": 100,
                "progress": 0
            },
            "auto_collection": auto_stats,
            "fine_tuning_history": history,
            "deployed_version": deployed_version
        }
    
    # Calculate stats
    total = len(feedbacks)
    accuracies = [f.get("accuracy_rating", 0) for f in feedbacks if f.get("accuracy_rating")]
    avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
    
    # Most common corrections
    from collections import Counter
    sa_contexts = []
    for f in feedbacks:
        if f.get("sa_context_notes"):
            sa_contexts.append(f["sa_context_notes"])
    
    # Recent feedback
    recent = sorted(feedbacks, key=lambda x: x.get("timestamp", ""), reverse=True)[:10]
    
    # Combined total (manual + automatic)
    combined_total = manual_feedback + auto_stats["total_examples"]
    
    # Readiness for fine-tuning (50 examples minimum)
    ready = combined_total >= 50
    progress = min(100, int((combined_total / 100) * 100))
    
    return {
        "total_feedback": total,
        "avg_accuracy": round(avg_accuracy, 2),
        "top_corrections": sa_contexts[:10],
        "recent_feedback": [
            {
                "timestamp": f.get("timestamp"),
                "corrected_description": f.get("corrected_description", "")[:100],
                "accuracy": f.get("accuracy_rating", 0)
            }
            for f in recent
        ],
        "readiness": {
            "ready_for_fine_tuning": ready,
            "feedback_needed": max(0, 50 - combined_total),
            "progress": progress,
            "recommendation": "Ready for fine-tuning!" if ready else f"Collect {50 - combined_total} more examples",
            "combined_total": combined_total
        },
        "auto_collection": auto_stats,
        "fine_tuning_history": [
            {
                "version": job.version,
                "created_at": job.created_at,
                "status": job.status,
                "model_name": job.model_name,
                "training_examples": job.training_examples,
                "deployed": job.deployed,
                "improvements": job.improvements
            }
            for job in history[:10]  # Last 10 jobs
        ],
        "deployed_version": {
            "version": deployed_version.version,
            "model_name": deployed_version.model_name,
            "deployed_at": deployed_version.created_at
        } if deployed_version else None
    }


@router.post("/training/export-dataset")
async def export_training_dataset(current_user: User = Depends(get_current_user)):
    """Export training dataset in OpenAI fine-tuning format (includes automatic collection)"""
    from alibi.training_agent import get_training_agent
    
    # Only admins can export
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    agent = get_training_agent()
    
    # Export automatically collected security-focused data
    result = agent.export_training_dataset(min_confidence=0.7)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Export failed"))
    
    return result


@router.post("/training/record-job")
async def record_fine_tuning_job(job_data: Dict, current_user: User = Depends(get_current_user)):
    """Record a new fine-tuning job"""
    from alibi.training_agent import get_history_manager, FineTuningJob
    from datetime import datetime
    
    # Only admins can record jobs
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    history_mgr = get_history_manager()
    
    # Create job record
    job = FineTuningJob(
        job_id=job_data.get("job_id", f"ft-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"),
        created_at=datetime.utcnow().isoformat(),
        status=job_data.get("status", "pending"),
        model_name=job_data.get("model_name", ""),
        base_model=job_data.get("base_model", "gpt-4-vision-preview"),
        training_examples=job_data.get("training_examples", 0),
        version=history_mgr.get_latest_version(),
        improvements=job_data.get("improvements", []),
        performance_metrics=job_data.get("performance_metrics", {}),
        deployed=False,
        notes=job_data.get("notes", "")
    )
    
    history_mgr.record_job(job)
    
    return {
        "success": True,
        "job_id": job.job_id,
        "version": job.version,
        "message": f"Recorded fine-tuning job {job.version}"
    }


@router.post("/training/deploy-version")
async def deploy_version(job_id: str, current_user: User = Depends(get_current_user)):
    """Mark a model version as deployed"""
    from alibi.training_agent import get_history_manager
    
    # Only admins can deploy
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    history_mgr = get_history_manager()
    history_mgr.mark_deployed(job_id)
    
    return {
        "success": True,
        "message": f"Version deployed: {job_id}"
    }


@router.get("/training/collection-stats")
async def get_collection_stats(current_user: User = Depends(get_current_user)):
    """Get automatic collection agent statistics"""
    from alibi.training_agent import get_training_agent
    
    agent = get_training_agent()
    stats = agent.get_collection_stats()
    
    # Get recent examples to show what's being collected
    examples = agent.load_examples(min_confidence=0.6)
    recent_examples = sorted(examples, key=lambda x: x.timestamp, reverse=True)[:10]
    
    return {
        "success": True,
        "stats": stats,
        "agent_status": "running",
        "recent_examples": [
            {
                "timestamp": ex.timestamp,
                "category": ex.category,
                "scene_description": ex.scene_description[:100] + "..." if len(ex.scene_description) > 100 else ex.scene_description,
                "security_relevance": ex.security_relevance,
                "confidence": ex.confidence_score
            }
            for ex in recent_examples
        ]
    }


TRAINING_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Training Data - Alibi</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .header h1 {
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .header .subtitle {
            color: #666;
            font-size: 14px;
        }
        
        .back-btn {
            background: rgba(255,255,255,0.2);
            backdrop-filter: blur(10px);
            border: none;
            color: white;
            padding: 12px 20px;
            border-radius: 12px;
            font-size: 16px;
            cursor: pointer;
            margin-bottom: 20px;
            display: inline-block;
            text-decoration: none;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .progress-bar {
            background: #e5e7eb;
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
            margin: 15px 0;
        }
        
        .progress-fill {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            height: 100%;
            transition: width 0.5s ease;
        }
        
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 12px;
            opacity: 0.9;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            background: #667eea;
            color: white;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            width: 100%;
            margin-top: 10px;
        }
        
        .btn:active {
            opacity: 0.8;
        }
        
        .btn-secondary {
            background: #6b7280;
        }
        
        .status-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            margin-top: 10px;
        }
        
        .status-ready {
            background: #10b981;
            color: white;
        }
        
        .status-collecting {
            background: #f59e0b;
            color: white;
        }
        
        .feedback-item {
            padding: 15px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        
        .feedback-item .timestamp {
            font-size: 12px;
            color: #6b7280;
            margin-bottom: 5px;
        }
        
        .feedback-item .description {
            font-size: 14px;
            color: #333;
            margin-bottom: 5px;
        }
        
        .feedback-item .rating {
            font-size: 12px;
            color: #667eea;
            font-weight: 600;
        }
        
        .section-title {
            font-size: 18px;
            font-weight: 600;
            color: #333;
            margin: 20px 0 15px 0;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .info-box {
            background: #f3f4f6;
            border-left: 4px solid #667eea;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
        }
        
        .info-box p {
            color: #374151;
            font-size: 14px;
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-btn">← Back to Home</a>
        
        <div class="header">
            <h1>🎓 Training Data</h1>
            <p class="subtitle">Improve AI vision for South African context</p>
        </div>
        
        <div class="card">
            <h2 style="margin-bottom: 15px;">🤖 24/7 Collection Agent</h2>
            <div class="info-box" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none;">
                <p><strong>🟢 Agent Status: ACTIVE</strong></p>
                <p>Automatically collecting security-relevant training data 24/7</p>
            </div>
            <div id="agentStats" style="margin-top: 15px;">
                <div class="loading">Loading agent stats...</div>
            </div>
        </div>
        
        
        <div class="card">
            <h2 style="margin-bottom: 15px;">📊 Training Progress</h2>
            <div id="progressSection">
                <div class="loading">Loading stats...</div>
            </div>
        </div>
        
        
        <div class="card">
            <h2 class="section-title">📝 Recent Feedback</h2>
            <div id="recentFeedback">
                <div class="loading">Loading recent feedback...</div>
            </div>
        </div>
        
        <div class="card" id="adminSection">
            <h2 class="section-title">🔧 Admin Controls</h2>
            
            <h3 style="margin: 20px 0 10px 0;">🌍 Collect REAL Crime & Security Data from Around the World</h3>
            <div class="info-box" style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; border: none;">
                <p><strong>🚨 REAL DATA COLLECTION!</strong></p>
                <p style="margin-top: 10px;">Automatically scrape and process:</p>
                <ul style="margin: 10px 0 10px 20px;">
                    <li><strong>Crime & Attacks:</strong> People, weapons, suspicious activities</li>
                    <li><strong>Security Events:</strong> Crowds, loitering, aggression patterns</li>
                    <li><strong>Vehicles & Plates:</strong> Cars, trucks, motorcycles, license plates</li>
                    <li><strong>South African Context:</strong> Taxis, townships, local scenarios</li>
                </ul>
                <p style="font-size: 13px; margin-top: 10px; opacity: 0.95;">
                    🎯 This pulls REAL visual data + descriptions from public datasets worldwide
                </p>
                <p style="font-size: 12px; margin-top: 5px; opacity: 0.9;">
                    ⏱️ Takes 10-30 minutes depending on number of examples
                </p>
            </div>
            <div style="margin: 15px 0;">
                <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                    🎯 COCO Dataset (People, vehicles, weapons, tools):
                </label>
                <input type="number" id="numCoco" value="200" min="10" max="1000" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px;">
                <p style="font-size: 11px; color: #666; margin-top: 3px;">
                    330K images with labeled objects - great for security contexts
                </p>
                
                <label style="display: block; margin: 15px 0 5px 0; font-weight: 600;">
                    🌍 Open Images (Diverse real-world scenarios):
                </label>
                <input type="number" id="numOpenImages" value="100" min="10" max="500" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px;">
                <p style="font-size: 11px; color: #666; margin-top: 3px;">
                    9M images from around the world - adds global context
                </p>
                
                <label style="display: block; margin: 15px 0 5px 0; font-weight: 600;">
                    🚨 Security Datasets (Crowds, anomalies, activities):
                </label>
                <input type="number" id="numSecurity" value="100" min="10" max="500" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px;">
                <p style="font-size: 11px; color: #666; margin-top: 3px;">
                    Specialized security-focused datasets for crime detection
                </p>
            </div>
            <button class="btn" onclick="collectFromHuggingFace()">
                🚀 Start Data Collection
            </button>
            <div id="collectionResult" style="margin-top: 15px;"></div>
            
            <h3 style="margin: 30px 0 10px 0;">Export Dataset</h3>
            <div class="info-box">
                <p>Export automatically collected security-focused training data.</p>
                <p>Minimum 50 examples required (includes manual + automatic collection).</p>
            </div>
            <button class="btn" onclick="exportDataset()">
                💾 Export Training Dataset
            </button>
            <div id="exportResult" style="margin-top: 15px;"></div>
            
            <div class="info-box" style="background: #f0fdf4; border-left-color: #10b981;">
                <h3 style="margin: 0 0 10px 0; color: #047857;">✅ Simple Workflow</h3>
                <ol style="margin: 0; padding-left: 20px; line-height: 1.8;">
                    <li><strong>Collect:</strong> Click "Start Data Collection" above (happens automatically in background)</li>
                    <li><strong>Export:</strong> Click "Export Training Dataset" when ready</li>
                    <li><strong>Upload:</strong> Go to <a href="https://platform.openai.com/finetune" target="_blank" style="color: #2563eb;">OpenAI Dashboard</a> → Upload your JSONL → Start fine-tuning</li>
                    <li><strong>Done:</strong> Model improves automatically once training completes!</li>
                </ol>
                <p style="margin: 15px 0 0 0; font-size: 12px; color: #047857;">
                    💡 No need to record anything back here - OpenAI tracks it for you!
                </p>
            </div>
        </div>
    </div>
    
    <script>
        const token = localStorage.getItem('alibi_token');
        let user = {};
        
        // Safely parse user data
        try {
            const userStr = localStorage.getItem('alibi_user');
            if (userStr && userStr !== 'undefined' && userStr !== 'null') {
                user = JSON.parse(userStr);
            }
        } catch (e) {
            console.error('[ERROR] Failed to parse user data:', e);
            // Clear corrupted data
            localStorage.removeItem('alibi_user');
        }
        
        // Show admin section for admins
        if (user && user.role === 'admin') {
            document.getElementById('adminSection').style.display = 'block';
        }
        
        async function loadStats() {
            console.log('[loadStats] Starting...');
            console.log('[loadStats] Token exists:', !!token);
            
            // Check for token FIRST - don't make API calls without it
            if (!token) {
                console.log('[loadStats] No token found');
                document.getElementById('progressSection').innerHTML = 
                    `<div class="info-box" style="border-left-color: #ef4444; background: #fef2f2;">
                        <p style="color: #991b1b; font-size: 18px; font-weight: 600;">🔐 Please Login</p>
                        <p style="color: #991b1b; margin-top: 10px;">You need to login to access training data.</p>
                        <a href="/camera/login" style="display: inline-block; margin-top: 15px; padding: 12px 24px; background: #dc2626; color: white; text-decoration: none; border-radius: 8px; font-weight: 600;">
                            Go to Login →
                        </a>
                    </div>`;
                document.getElementById('agentStats').innerHTML = '';
                return;
            }
            
            // Clear "Loading..." messages
            document.getElementById('progressSection').innerHTML = '<p style="color: #6b7280;">Connecting to server...</p>';
            document.getElementById('agentStats').innerHTML = '<p style="color: #6b7280;">Loading agent data...</p>';
            
            try {
                const response = await fetch('/camera/training/stats', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                console.log('[loadStats] Response status:', response.status);
                
                if (response.status === 401 || response.status === 403) {
                    console.error('[loadStats] Authentication failed');
                    throw new Error('Authentication failed (401/403)');
                }
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    console.error('[loadStats] Error response:', errorData);
                    throw new Error(errorData.detail || `HTTP ${response.status}`);
                }
                
                const data = await response.json();
                console.log('[loadStats] Stats loaded successfully:', data);
                
                // Display stats
                try {
                    displayStats(data);
                } catch (e) {
                    console.error('[loadStats] Error in displayStats:', e);
                    document.getElementById('progressSection').innerHTML = 
                        `<p style="color: #ef4444;">Error displaying stats: ${e.message}</p>`;
                }
                
                try {
                    displayAgentStats(data.auto_collection || {total_examples: 0, by_category: {}});
                } catch (e) {
                    console.error('[loadStats] Error in displayAgentStats:', e);
                    document.getElementById('agentStats').innerHTML = 
                        `<p style="color: #ef4444;">Error displaying agent stats: ${e.message}</p>`;
                }
                
                // Load recent agent activity
                try {
                    loadCollectionExamples();
                } catch (e) {
                    console.error('[loadStats] Error in loadCollectionExamples:', e);
                }
            } catch (error) {
                console.error('[loadStats] Exception:', error);
                
                // Check if it's an auth error
                if (error.message.includes('401') || error.message.includes('403') || error.message.includes('Unauthorized')) {
                    document.getElementById('progressSection').innerHTML = 
                        `<div class="info-box" style="border-left-color: #ef4444; background: #fef2f2;">
                            <p style="color: #991b1b; font-size: 18px; font-weight: 600;">🔐 Please Login</p>
                            <p style="color: #991b1b; margin-top: 10px;">Your session has expired.</p>
                            <a href="/camera/login" style="display: inline-block; margin-top: 15px; padding: 12px 24px; background: #dc2626; color: white; text-decoration: none; border-radius: 8px; font-weight: 600;">
                                Go to Login →
                            </a>
                        </div>`;
                    document.getElementById('agentStats').innerHTML = '';
                } else {
                    document.getElementById('progressSection').innerHTML = 
                        `<div class="info-box" style="border-left-color: #ef4444;">
                            <p style="color: #ef4444;"><strong>Error loading stats:</strong> ${error.message}</p>
                            <button onclick="location.reload()" style="margin-top: 10px; padding: 8px 16px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer;">
                                🔄 Retry
                            </button>
                        </div>`;
                    document.getElementById('agentStats').innerHTML = 
                        `<p style="color: #ef4444;">Failed to load agent stats</p>`;
                }
            }
        }
        
        function displayAgentStats(autoStats) {
            console.log('[displayAgentStats] Called with:', autoStats);
            
            // Always show something, even if no data
            if (!autoStats || typeof autoStats !== 'object') {
                console.log('[displayAgentStats] No autoStats, showing startup message');
                document.getElementById('agentStats').innerHTML = 
                    '<p style="color: #6b7280;">Agent starting up... No data collected yet.</p>';
                return;
            }
            
            const categories = autoStats.by_category || {};
            let categoryHtml = '';
            
            for (const [category, count] of Object.entries(categories)) {
                const categoryName = category.replace(/_/g, ' ').toUpperCase();
                categoryHtml += `
                    <div class="list-item">
                        <span>${categoryName}</span>
                        <span class="badge">${count}</span>
                    </div>
                `;
            }
            
            const html = `
                <div class="stat-grid">
                    <div class="stat-card" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">
                        <div class="stat-value">${autoStats.total_examples || 0}</div>
                        <div class="stat-label">Examples Collected</div>
                    </div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);">
                        <div class="stat-value">${autoStats.high_confidence_examples || 0}</div>
                        <div class="stat-label">High Confidence</div>
                    </div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);">
                        <div class="stat-value">${Object.keys(categories).length}</div>
                        <div class="stat-label">Categories</div>
                    </div>
                </div>
                
                ${categoryHtml ? `
                    <h3 style="margin: 20px 0 10px 0;">Security Categories</h3>
                    ${categoryHtml}
                ` : '<p style="color: #6b7280;">Collecting data...</p>'}
                
                <p style="color: #6b7280; margin-top: 15px; font-size: 12px;">
                    Agent monitors camera footage 24/7 for security-relevant patterns
                </p>
            `;
            
            document.getElementById('agentStats').innerHTML = html;
        }
        
        async function loadCollectionExamples() {
            console.log('[loadCollectionExamples] Starting...');
            try {
                const response = await fetch('/camera/training/collection-stats', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                
                console.log('[loadCollectionExamples] Response status:', response.status);
                
                if (response.status === 401 || response.status === 403) {
                    console.warn('[loadCollectionExamples] Not authenticated');
                    return;
                }
                
                if (!response.ok) {
                    console.warn('[loadCollectionExamples] Request failed:', response.status);
                    return;
                }
                
                const data = await response.json();
                console.log('[loadCollectionExamples] Data received:', data);
                
                if (data.recent_examples && data.recent_examples.length > 0) {
                    displayRecentExamples(data.recent_examples);
                } else {
                    console.log('[loadCollectionExamples] No recent examples');
                }
            } catch (error) {
                console.error('[loadCollectionExamples] Exception:', error);
            }
        }
        
        function displayRecentExamples(examples) {
            const html = `
                <h3 style="margin: 20px 0 10px 0;">Recent Activity (What Agent is Collecting)</h3>
                ${examples.map(ex => `
                    <div class="feedback-item" style="margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                            <span class="badge" style="background: #667eea;">${ex.category.replace(/_/g, ' ')}</span>
                            <span style="font-size: 12px; color: #666;">${new Date(ex.timestamp).toLocaleString()}</span>
                        </div>
                        <div class="description" style="margin-bottom: 5px;">${ex.scene_description}</div>
                        <div style="font-size: 12px; color: #666; font-style: italic;">
                            Why: ${ex.security_relevance}
                        </div>
                        <div style="font-size: 12px; color: #666;">
                            Confidence: ${(ex.confidence * 100).toFixed(0)}%
                        </div>
                    </div>
                `).join('')}
            `;
            
            // Insert after the categories section
            const agentStats = document.getElementById('agentStats');
            if (agentStats && !document.getElementById('recentExamples')) {
                const div = document.createElement('div');
                div.id = 'recentExamples';
                div.innerHTML = html;
                agentStats.appendChild(div);
            }
        }
        
        function displayHistory(history, deployedVersion) {
            console.log('[displayHistory] Called with:', history, deployedVersion);
            
            if (!history || !Array.isArray(history) || history.length === 0) {
                document.getElementById('historySection').innerHTML = `
                    <p style="color: #6b7280;">No fine-tuning jobs recorded yet.</p>
                    <p style="color: #6b7280; font-size: 12px; margin-top: 10px;">
                        Once you export a dataset and start a fine-tuning job with OpenAI, 
                        record it here to track model versions.
                    </p>
                `;
                return;
            }
            
            let html = '';
            
            // Show deployed version prominently
            if (deployedVersion) {
                html += `
                    <div class="info-box" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; margin-bottom: 20px;">
                        <p><strong>🚀 Currently Deployed: ${deployedVersion.version}</strong></p>
                        <p style="font-size: 12px; margin-top: 5px;">${deployedVersion.model_name}</p>
                        <p style="font-size: 12px; opacity: 0.9;">Deployed: ${new Date(deployedVersion.deployed_at).toLocaleDateString()}</p>
                    </div>
                `;
            }
            
            html += '<h3 style="margin: 20px 0 10px 0;">Version History</h3>';
            
            history.forEach(job => {
                const statusColor = {
                    'completed': '#10b981',
                    'running': '#f59e0b',
                    'failed': '#ef4444',
                    'pending': '#6b7280'
                }[job.status] || '#6b7280';
                
                const improvements = job.improvements && job.improvements.length > 0
                    ? job.improvements.map(imp => `• ${imp}`).join('<br>')
                    : 'General improvements';
                
                html += `
                    <div class="feedback-item" style="${job.deployed ? 'border: 2px solid #10b981;' : ''}">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <strong style="font-size: 16px;">${job.version}</strong>
                            <span style="background: ${statusColor}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600;">
                                ${job.status.toUpperCase()}
                            </span>
                        </div>
                        <div class="timestamp">${new Date(job.created_at).toLocaleString()}</div>
                        <div class="description" style="margin: 8px 0;">
                            <strong>Model:</strong> ${job.model_name || 'Unknown'}<br>
                            <strong>Examples:</strong> ${job.training_examples}<br>
                            <strong>Improvements:</strong><br>
                            <span style="font-size: 12px; color: #666;">${improvements}</span>
                        </div>
                        ${job.deployed ? '<div style="color: #10b981; font-weight: 600; margin-top: 8px;">✓ DEPLOYED</div>' : ''}
                    </div>
                `;
            });
            
            document.getElementById('historySection').innerHTML = html;
        }
        
        function displayStats(data) {
            console.log('[displayStats] Called with:', data);
            
            if (!data || !data.readiness) {
                console.error('[displayStats] Invalid data structure:', data);
                document.getElementById('progressSection').innerHTML = 
                    '<p style="color: #ef4444;">Invalid data received from server</p>';
                return;
            }
            
            const readiness = data.readiness;
            const statusClass = readiness.ready_for_fine_tuning ? 'status-ready' : 'status-collecting';
            const statusText = readiness.ready_for_fine_tuning ? '✅ Ready for Fine-Tuning!' : '⏳ Collecting Data';
            
            let html = `
                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="stat-value">${data.total_feedback}</div>
                        <div class="stat-label">Feedback Collected</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${data.avg_accuracy}★</div>
                        <div class="stat-label">Avg Accuracy</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${readiness.feedback_needed}</div>
                        <div class="stat-label">Needed for Fine-Tuning</div>
                    </div>
                </div>
                
                <div style="margin: 20px 0;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span style="font-weight: 600;">Progress to Fine-Tuning</span>
                        <span style="font-weight: 600;">${readiness.progress}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${readiness.progress}%"></div>
                    </div>
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </div>
                
                <p style="color: #6b7280; margin-top: 15px;">${readiness.recommendation}</p>
            `;
            
            document.getElementById('progressSection').innerHTML = html;
        }
        
        async function exportDataset() {
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = 'Exporting...';
            
            try {
                const response = await fetch('/camera/training/export-dataset', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.detail || 'Export failed');
                }
                
                // Show detailed breakdown
                let categoryBreakdown = '';
                if (data.by_category) {
                    for (const [cat, count] of Object.entries(data.by_category)) {
                        categoryBreakdown += `<br>  • ${cat.replace(/_/g, ' ')}: ${count} examples`;
                    }
                }
                
                document.getElementById('exportResult').innerHTML = `
                    <div class="info-box" style="border-left-color: #10b981;">
                        <p><strong>✅ Export Successful!</strong></p>
                        <p><strong>File:</strong> ${data.dataset_file}</p>
                        <p><strong>Examples:</strong> ${data.examples_exported}</p>
                        <p><strong>Avg Confidence:</strong> ${(data.avg_confidence * 100).toFixed(1)}%</p>
                        ${categoryBreakdown ? `<p><strong>Categories:</strong>${categoryBreakdown}</p>` : ''}
                        <p style="margin-top: 10px; font-size: 12px;">
                            <strong>Next Steps:</strong><br>
                            1. Upload ${data.dataset_file} to OpenAI<br>
                            2. Start fine-tuning job<br>
                            3. Record the job below once started
                        </p>
                    </div>
                `;
            } catch (error) {
                document.getElementById('exportResult').innerHTML = `
                    <div class="info-box" style="border-left-color: #ef4444;">
                        <p style="color: #ef4444;"><strong>❌ Error:</strong> ${error.message}</p>
                    </div>
                `;
            } finally {
                btn.disabled = false;
                btn.textContent = '💾 Export Training Dataset';
            }
        }
        
        async function recordJob() {
            const btn = event.target;
            const jobId = document.getElementById('jobId').value.trim();
            const improvementsText = document.getElementById('improvements').value.trim();
            const trainingExamples = parseInt(document.getElementById('trainingExamples').value) || 0;
            
            if (!jobId || !improvementsText || !trainingExamples) {
                document.getElementById('recordResult').innerHTML = `
                    <div class="info-box" style="border-left-color: #ef4444;">
                        <p style="color: #ef4444;">Please fill in all fields</p>
                    </div>
                `;
                return;
            }
            
            btn.disabled = true;
            btn.textContent = 'Recording...';
            
            try {
                const response = await fetch('/camera/training/record-job', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        job_id: jobId,
                        model_name: 'gpt-4-vision-preview',  // Always the same model
                        training_examples: trainingExamples,
                        improvements: [improvementsText],  // Just the description as-is
                        status: 'pending'
                    })
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.detail || 'Failed to record job');
                }
                
                document.getElementById('recordResult').innerHTML = `
                    <div class="info-box" style="border-left-color: #10b981;">
                        <p><strong>✅ Training Batch Recorded!</strong></p>
                        <p>Batch #${data.version}</p>
                        <p>Job ID: ${data.job_id}</p>
                        <p style="margin-top: 10px; font-size: 12px;">
                            Model improves once OpenAI completes training.
                        </p>
                    </div>
                `;
                
                // Clear form
                document.getElementById('jobId').value = '';
                document.getElementById('improvements').value = '';
                document.getElementById('trainingExamples').value = '';
                
                // Reload stats after 2 seconds
                setTimeout(loadStats, 2000);
                
            } catch (error) {
                document.getElementById('recordResult').innerHTML = `
                    <div class="info-box" style="border-left-color: #ef4444;">
                        <p style="color: #ef4444;"><strong>❌ Error:</strong> ${error.message}</p>
                    </div>
                `;
            } finally {
                btn.disabled = false;
                btn.textContent = '✅ Record Training Batch';
            }
        }
        
        async function collectFromHuggingFace() {
            const btn = event.target;
            const numCoco = parseInt(document.getElementById('numCoco').value) || 100;
            const numOpenImages = parseInt(document.getElementById('numOpenImages').value) || 50;
            const numSecurity = parseInt(document.getElementById('numSecurity').value) || 50;
            
            btn.disabled = true;
            btn.textContent = '⏳ Starting collection...';
            
            try {
                const response = await fetch('/data-collection/collect-from-huggingface', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        num_coco: numCoco,
                        num_open_images: numOpenImages,
                        num_security: numSecurity
                    })
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    if (data.error && data.install_command) {
                        document.getElementById('collectionResult').innerHTML = `
                            <div class="info-box" style="border-left-color: #f59e0b;">
                                <p style="color: #f59e0b;"><strong>⚠️ Missing Dependencies</strong></p>
                                <p>${data.error}</p>
                                <p style="margin-top: 10px;">Install with:</p>
                                <pre style="background: #1e1e1e; color: #d4d4d4; padding: 10px; border-radius: 4px; overflow-x: auto;">${data.install_command}</pre>
                                <button onclick="installDependencies()" class="btn" style="margin-top: 10px;">
                                    📦 Auto-Install Dependencies
                                </button>
                            </div>
                        `;
                    } else {
                        throw new Error(data.detail || 'Collection failed');
                    }
                } else {
                    document.getElementById('collectionResult').innerHTML = `
                        <div class="info-box" style="border-left-color: #10b981;">
                            <p><strong>✅ Collection Started!</strong></p>
                            <p>Collecting ${data.target_examples} examples from Hugging Face...</p>
                            <p style="margin-top: 10px; font-size: 12px;">
                                ⏱️ Estimated time: ${data.estimated_time}
                            </p>
                            <p style="margin-top: 10px; font-size: 12px;">
                                This is running in the background. Refresh this page in ${data.estimated_time} to see results!
                            </p>
                            <button onclick="checkCollectionStatus()" class="btn" style="margin-top: 10px;">
                                📊 Check Status
                            </button>
                        </div>
                    `;
                }
                
            } catch (error) {
                document.getElementById('collectionResult').innerHTML = `
                    <div class="info-box" style="border-left-color: #ef4444;">
                        <p style="color: #ef4444;"><strong>❌ Error:</strong> ${error.message}</p>
                    </div>
                `;
            } finally {
                btn.disabled = false;
                btn.textContent = '🚀 Start Data Collection';
            }
        }
        
        async function installDependencies() {
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = '⏳ Installing...';
            
            try {
                const response = await fetch('/data-collection/install-dependencies', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    document.getElementById('collectionResult').innerHTML = `
                        <div class="info-box" style="border-left-color: #10b981;">
                            <p><strong>✅ Installing Dependencies...</strong></p>
                            <p>Installing: ${data.packages.join(', ')}</p>
                            <p style="margin-top: 10px; font-size: 12px;">
                                This will take 2-5 minutes. Refresh the page when done.
                            </p>
                        </div>
                    `;
                }
            } catch (error) {
                alert('Installation failed: ' + error.message);
            } finally {
                btn.disabled = false;
                btn.textContent = '📦 Auto-Install Dependencies';
            }
        }
        
        async function checkCollectionStatus() {
            try {
                const response = await fetch('/data-collection/status', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                const data = await response.json();
                
                if (response.ok && data.stats) {
                    const stats = data.stats;
                    document.getElementById('collectionResult').innerHTML = `
                        <div class="info-box" style="border-left-color: #667eea;">
                            <p><strong>📊 Collection Status</strong></p>
                            <p>Total examples collected: <strong>${stats.total_examples}</strong></p>
                            <p>By source: ${JSON.stringify(stats.by_source)}</p>
                            <p>By category: ${JSON.stringify(stats.by_category)}</p>
                            <p style="margin-top: 10px; font-size: 12px;">
                                Latest: ${stats.latest_collection || 'None yet'}
                            </p>
                        </div>
                    `;
                }
            } catch (error) {
                alert('Failed to check status: ' + error.message);
            }
        }
        
        // Simple load - no auto-redirects
        loadStats();
    </script>
</body>
</html>
"""
