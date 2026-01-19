"""
Debug endpoint for training page
"""
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from alibi.auth import get_current_user, User
import json
from pathlib import Path

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/training-endpoint")
async def debug_training_endpoint(current_user: User = Depends(get_current_user)):
    """Debug what the training stats endpoint returns"""
    from alibi.training_agent import get_training_agent, get_history_manager
    
    try:
        agent = get_training_agent()
        history_mgr = get_history_manager()
        
        # Get automatic collection stats
        auto_stats = agent.get_collection_stats()
        
        # Get fine-tuning history
        history = history_mgr.get_history()
        deployed_version = history_mgr.get_deployed_version()
        
        # Get manual feedback stats
        FEEDBACK_FILE = Path("alibi/data/vision_feedback.jsonl")
        manual_feedback = 0
        if FEEDBACK_FILE.exists():
            feedbacks = []
            with open(FEEDBACK_FILE, 'r') as f:
                for line in f:
                    try:
                        feedbacks.append(json.loads(line))
                    except:
                        continue
            manual_feedback = len(feedbacks)
        
        # Build response
        response = {
            "success": True,
            "user": {
                "username": current_user.username,
                "role": current_user.role
            },
            "auto_collection": auto_stats,
            "manual_feedback_count": manual_feedback,
            "fine_tuning_history_count": len(history),
            "deployed_version": deployed_version.version if deployed_version else None,
            "raw_data": {
                "auto_stats": auto_stats,
                "history": [
                    {
                        "version": job.version,
                        "status": job.status,
                        "created_at": job.created_at
                    }
                    for job in history[:5]
                ],
                "deployed_version_details": {
                    "version": deployed_version.version,
                    "model_name": deployed_version.model_name,
                    "deployed_at": deployed_version.created_at
                } if deployed_version else None
            }
        }
        
        return response
        
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "user": {
                    "username": current_user.username,
                    "role": current_user.role
                }
            }
        )


@router.get("/training-page-test", response_class=HTMLResponse)
async def debug_training_page():
    """Test page that debugs the training data endpoint"""
    return HTMLResponse(content=DEBUG_HTML)


DEBUG_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Training Data Debug</title>
    <style>
        body {
            font-family: monospace;
            padding: 20px;
            background: #1e1e1e;
            color: #d4d4d4;
        }
        .section {
            background: #252526;
            border: 1px solid #3e3e42;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .success { color: #4ec9b0; }
        .error { color: #f48771; }
        .warning { color: #dcdcaa; }
        pre {
            background: #1e1e1e;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            border: 1px solid #3e3e42;
        }
        button {
            background: #0e639c;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin: 5px;
        }
        button:hover {
            background: #1177bb;
        }
        .step {
            margin: 10px 0;
            padding: 10px;
            background: #2d2d30;
            border-left: 3px solid #007acc;
        }
        h1, h2 { color: #4ec9b0; }
    </style>
</head>
<body>
    <h1>🔍 Training Data Endpoint Debugger</h1>
    
    <div class="section">
        <h2>Step 1: Check Authentication</h2>
        <div id="auth-status">Checking...</div>
        <button onclick="checkAuth()">🔄 Recheck Auth</button>
    </div>
    
    <div class="section">
        <h2>Step 2: Test Training Stats Endpoint</h2>
        <button onclick="testTrainingStats()">🧪 Test /camera/training/stats</button>
        <div id="stats-result"></div>
    </div>
    
    <div class="section">
        <h2>Step 3: Test Debug Endpoint</h2>
        <button onclick="testDebugEndpoint()">🔬 Test /debug/training-endpoint</button>
        <div id="debug-result"></div>
    </div>
    
    <div class="section">
        <h2>Step 4: Console Logs</h2>
        <div id="console-logs"></div>
    </div>
    
    <script>
        const logs = [];
        
        function log(message, type = 'info') {
            const timestamp = new Date().toISOString().substr(11, 12);
            logs.push({timestamp, message, type});
            console.log(`[${timestamp}] ${message}`);
            updateConsoleLogs();
        }
        
        function updateConsoleLogs() {
            const el = document.getElementById('console-logs');
            el.innerHTML = logs.slice(-20).map(l => 
                `<div class="step ${l.type}">[${l.timestamp}] ${l.message}</div>`
            ).join('');
        }
        
        async function checkAuth() {
            log('Checking authentication...', 'info');
            
            const token = localStorage.getItem('alibi_token');
            const userStr = localStorage.getItem('alibi_user');
            
            const authDiv = document.getElementById('auth-status');
            
            if (!token) {
                authDiv.innerHTML = '<span class="error">❌ NO TOKEN FOUND</span><br>' +
                    '<a href="/camera/login" style="color: #4ec9b0;">Go to Login</a>';
                log('No token found in localStorage', 'error');
                return false;
            }
            
            log('Token found: ' + token.substring(0, 20) + '...', 'success');
            
            if (!userStr) {
                authDiv.innerHTML = '<span class="warning">⚠️ TOKEN EXISTS but NO USER DATA</span>';
                log('User data missing from localStorage', 'warning');
            } else {
                try {
                    const user = JSON.parse(userStr);
                    authDiv.innerHTML = `<span class="success">✅ LOGGED IN</span><br>` +
                        `User: ${user.username}<br>` +
                        `Role: ${user.role}`;
                    log(`Logged in as: ${user.username} (${user.role})`, 'success');
                } catch (e) {
                    authDiv.innerHTML = '<span class="error">❌ INVALID USER DATA</span>';
                    log('Error parsing user data: ' + e.message, 'error');
                    return false;
                }
            }
            
            return true;
        }
        
        async function testTrainingStats() {
            log('Testing /camera/training/stats...', 'info');
            
            const token = localStorage.getItem('alibi_token');
            if (!token) {
                alert('Please login first!');
                return;
            }
            
            const resultDiv = document.getElementById('stats-result');
            resultDiv.innerHTML = '<div class="warning">Loading...</div>';
            
            try {
                const response = await fetch('/camera/training/stats', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                log(`Response status: ${response.status}`, response.ok ? 'success' : 'error');
                
                const data = await response.json();
                
                if (response.ok) {
                    resultDiv.innerHTML = `<div class="success">✅ SUCCESS</div>` +
                        `<pre>${JSON.stringify(data, null, 2)}</pre>`;
                    log('Endpoint returned valid data', 'success');
                } else {
                    resultDiv.innerHTML = `<div class="error">❌ ERROR ${response.status}</div>` +
                        `<pre>${JSON.stringify(data, null, 2)}</pre>`;
                    log(`Error: ${data.detail || 'Unknown error'}`, 'error');
                }
            } catch (error) {
                resultDiv.innerHTML = `<div class="error">❌ EXCEPTION: ${error.message}</div>`;
                log('Exception: ' + error.message, 'error');
            }
        }
        
        async function testDebugEndpoint() {
            log('Testing /debug/training-endpoint...', 'info');
            
            const token = localStorage.getItem('alibi_token');
            if (!token) {
                alert('Please login first!');
                return;
            }
            
            const resultDiv = document.getElementById('debug-result');
            resultDiv.innerHTML = '<div class="warning">Loading...</div>';
            
            try {
                const response = await fetch('/debug/training-endpoint', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                log(`Response status: ${response.status}`, response.ok ? 'success' : 'error');
                
                const data = await response.json();
                
                if (response.ok) {
                    resultDiv.innerHTML = `<div class="success">✅ SUCCESS</div>` +
                        `<pre>${JSON.stringify(data, null, 2)}</pre>`;
                    log('Debug endpoint returned data', 'success');
                } else {
                    resultDiv.innerHTML = `<div class="error">❌ ERROR ${response.status}</div>` +
                        `<pre>${JSON.stringify(data, null, 2)}</pre>`;
                    log(`Error: ${data.detail || 'Unknown error'}`, 'error');
                }
            } catch (error) {
                resultDiv.innerHTML = `<div class="error">❌ EXCEPTION: ${error.message}</div>`;
                log('Exception: ' + error.message, 'error');
            }
        }
        
        // Auto-run auth check on load
        window.onload = () => {
            log('Debug page loaded', 'info');
            checkAuth();
        };
    </script>
</body>
</html>
"""
