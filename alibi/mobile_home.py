"""
Mobile Home Page - Main entry point for iPhone/mobile access
Provides access to all Alibi features from a single mobile-friendly page
"""

MOBILE_HOME_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>Alibi Mobile</title>
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
            max-width: 500px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            padding: 30px 0;
        }
        
        .header h1 {
            font-size: 36px;
            margin-bottom: 10px;
        }
        
        .header .subtitle {
            font-size: 16px;
            opacity: 0.9;
        }
        
        .user-info {
            background: rgba(255,255,255,0.15);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 15px 20px;
            margin-bottom: 20px;
            color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .user-info .name {
            font-weight: 600;
        }
        
        .user-info .role {
            background: rgba(255,255,255,0.2);
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .logout-btn {
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            padding: 8px 16px;
            border-radius: 12px;
            font-size: 14px;
            cursor: pointer;
        }
        
        .card-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 15px;
        }
        
        .card {
            background: white;
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-decoration: none;
            color: inherit;
            display: flex;
            align-items: center;
            gap: 20px;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .card:active {
            transform: scale(0.98);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .card-icon {
            font-size: 40px;
            width: 60px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            flex-shrink: 0;
        }
        
        .card-content {
            flex: 1;
        }
        
        .card-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 5px;
            color: #333;
        }
        
        .card-description {
            font-size: 14px;
            color: #666;
            line-height: 1.4;
        }
        
        .card-badge {
            background: #ef4444;
            color: white;
            padding: 4px 8px;
            border-radius: 8px;
            font-size: 11px;
            font-weight: 600;
        }
        
        .featured {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .featured .card-icon {
            background: rgba(255,255,255,0.2);
        }
        
        .featured .card-title,
        .featured .card-description {
            color: white;
        }
        
        .section-title {
            color: white;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 30px 0 15px 0;
            opacity: 0.9;
        }
        
        .footer {
            text-align: center;
            color: white;
            padding: 30px 0;
            font-size: 12px;
            opacity: 0.7;
        }
        
        .admin-only {
            position: relative;
        }
        
        .admin-only::after {
            content: 'ADMIN';
            position: absolute;
            top: 10px;
            right: 10px;
            background: #ef4444;
            color: white;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 10px;
            font-weight: 600;
        }
        
        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎥 Alibi</h1>
            <p class="subtitle">Mobile Command Center</p>
        </div>
        
        <div class="user-info">
            <div>
                <div class="name" id="userName">User</div>
                <div class="role" id="userRole"></div>
            </div>
            <button class="logout-btn" onclick="logout()">Logout</button>
        </div>
        
        <!-- Featured: Enhanced Security Camera -->
        <a href="/camera/secure-stream" class="card featured">
            <div class="card-icon">🔒</div>
            <div class="card-content">
                <div class="card-title">Security Camera</div>
                <div class="card-description">Real-time threat detection with red flag capability</div>
            </div>
        </a>
        
        <div class="section-title">📊 Operations</div>
        
        <div class="card-grid">
            <a href="/camera/history" class="card">
                <div class="card-icon">📸💥</div>
                <div class="card-content">
                    <div class="card-title">Camera History</div>
                    <div class="card-description">Browse analyzed snapshots and AI descriptions</div>
                </div>
            </a>
            
            <a href="/camera/insights" class="card">
                <div class="card-icon">🧠</div>
                <div class="card-content">
                    <div class="card-title">Insights & Reports</div>
                    <div class="card-description">AI-powered insights from camera footage</div>
                </div>
            </a>
            
            <a href="/camera/training" class="card">
                <div class="card-icon">🎓</div>
                <div class="card-content">
                    <div class="card-title">Training Data</div>
                    <div class="card-description">Improve AI vision for South African context</div>
                </div>
            </a>
        </div>
        
        <div class="section-title">⚙️ Administration</div>
        
        <div class="card-grid">
            <a href="/docs" class="card">
                <div class="card-icon">📚</div>
                <div class="card-content">
                    <div class="card-title">API Documentation</div>
                    <div class="card-description">Interactive API testing and docs</div>
                </div>
            </a>
        </div>
        
        <div class="footer">
            Alibi Police Oversight System<br>
            Namibia Pilot Deployment 2026
        </div>
    </div>
    
    <script>
        // Check if logged in
        const token = localStorage.getItem('alibi_token');
        const user = localStorage.getItem('alibi_user');
        
        if (!token) {
            // Redirect to login
            window.location.href = '/camera/login';
        } else {
            // Display user info
            let userData = null;
            
            try {
                // Safely parse user data
                if (user && user !== 'undefined' && user !== 'null') {
                    userData = JSON.parse(user);
                }
            } catch (e) {
                console.error('Error parsing user data:', e);
                // Clear corrupted data
                localStorage.removeItem('alibi_user');
            }
            
            // Update UI with user data
            if (userData && userData.username) {
                document.getElementById('userName').textContent = userData.full_name || userData.username;
                document.getElementById('userRole').textContent = userData.role || 'user';
            } else {
                // Default values if no valid data
                document.getElementById('userName').textContent = 'User';
                document.getElementById('userRole').textContent = 'guest';
            }
        }
        
        function logout() {
            localStorage.removeItem('alibi_token');
            localStorage.removeItem('alibi_user');
            window.location.href = '/camera/login';
        }
        
        function openConsole(path) {
            // Build console URL with current host but port 5173
            const host = window.location.hostname;
            const consoleUrl = `http://${host}:5173${path}`;
            window.location.href = consoleUrl;
        }
        
        // Add to home screen prompt
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
        });
    </script>
</body>
</html>
"""
