"""
Training Page Fix - Auto-clears corrupted localStorage
"""

FIX_PAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Fixing Training Page...</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }
        .container {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            max-width: 500px;
        }
        h1 { font-size: 32px; margin-bottom: 20px; }
        p { font-size: 16px; margin: 10px 0; }
        .status { font-size: 48px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="status">🔧</div>
        <h1>Fixing Training Data Page...</h1>
        <p id="status">Clearing corrupted data...</p>
    </div>
    
    <script>
        // Clear ALL localStorage to fix corrupted data
        localStorage.clear();
        
        // Update status
        document.getElementById('status').textContent = '✅ Fixed! Redirecting to login...';
        
        // Redirect to login after 2 seconds
        setTimeout(() => {
            window.location.href = '/camera/login';
        }, 2000);
    </script>
</body>
</html>
"""
