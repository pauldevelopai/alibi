"""
Simple camera test page for debugging camera access issues
"""

CAMERA_TEST_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Camera Test</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: #000;
            color: #fff;
            padding: 20px;
        }
        h1 { margin-bottom: 20px; font-size: 24px; }
        video {
            width: 100%;
            max-width: 640px;
            background: #222;
            border: 2px solid #0f0;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        button {
            background: #0f0;
            color: #000;
            border: none;
            padding: 15px 30px;
            font-size: 18px;
            border-radius: 10px;
            margin: 5px;
            cursor: pointer;
        }
        #log {
            background: #222;
            padding: 15px;
            border-radius: 10px;
            font-size: 12px;
            max-height: 300px;
            overflow-y: auto;
            margin-top: 20px;
        }
        .error { color: #f00; }
        .success { color: #0f0; }
        .info { color: #0af; }
    </style>
</head>
<body>
    <h1>📷 Camera Test</h1>
    
    <video id="video" autoplay playsinline></video>
    
    <button onclick="testCamera()">Start Camera</button>
    <button onclick="testPermissions()">Check Permissions</button>
    <button onclick="clearLog()">Clear Log</button>
    
    <div id="log"></div>
    
    <script>
        const video = document.getElementById('video');
        const logDiv = document.getElementById('log');
        
        function log(message, type = 'info') {
            const time = new Date().toLocaleTimeString();
            const entry = document.createElement('div');
            entry.className = type;
            entry.textContent = `[${time}] ${message}`;
            logDiv.appendChild(entry);
            logDiv.scrollTop = logDiv.scrollHeight;
            console.log(`[${type}] ${message}`);
        }
        
        function clearLog() {
            logDiv.innerHTML = '';
        }
        
        async function testPermissions() {
            log('Testing camera permissions...', 'info');
            
            try {
                // Check if getUserMedia is available
                if (!navigator.mediaDevices) {
                    log('❌ navigator.mediaDevices not available', 'error');
                    log('This usually means: not HTTPS or not supported', 'error');
                    return;
                }
                
                log('✅ navigator.mediaDevices is available', 'success');
                
                // Check if getUserMedia exists
                if (!navigator.mediaDevices.getUserMedia) {
                    log('❌ getUserMedia not available', 'error');
                    return;
                }
                
                log('✅ getUserMedia is available', 'success');
                
                // Try to enumerate devices
                const devices = await navigator.mediaDevices.enumerateDevices();
                const videoDevices = devices.filter(d => d.kind === 'videoinput');
                log(`✅ Found ${videoDevices.length} camera(s)`, 'success');
                
                videoDevices.forEach((device, i) => {
                    log(`  Camera ${i+1}: ${device.label || 'Unknown'}`, 'info');
                });
                
                // Check permissions API if available
                if (navigator.permissions) {
                    try {
                        const result = await navigator.permissions.query({ name: 'camera' });
                        log(`Camera permission state: ${result.state}`, result.state === 'granted' ? 'success' : 'info');
                    } catch (e) {
                        log('Permissions API not fully supported', 'info');
                    }
                }
                
            } catch (error) {
                log(`❌ Error: ${error.message}`, 'error');
            }
        }
        
        async function testCamera() {
            log('Requesting camera access...', 'info');
            
            try {
                const constraints = {
                    video: {
                        facingMode: 'environment',
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                    }
                };
                
                log('Calling getUserMedia...', 'info');
                const stream = await navigator.mediaDevices.getUserMedia(constraints);
                
                log('✅ Camera access granted!', 'success');
                
                const track = stream.getVideoTracks()[0];
                const settings = track.getSettings();
                log(`Camera: ${track.label}`, 'success');
                log(`Resolution: ${settings.width}x${settings.height}`, 'info');
                log(`Facing mode: ${settings.facingMode}`, 'info');
                
                video.srcObject = stream;
                log('✅ Video stream started!', 'success');
                
            } catch (error) {
                log(`❌ Camera error: ${error.name}`, 'error');
                log(`   Message: ${error.message}`, 'error');
                
                if (error.name === 'NotAllowedError') {
                    log('', 'error');
                    log('🛑 Camera permission was DENIED', 'error');
                    log('', 'error');
                    log('To fix:', 'info');
                    log('1. Tap the "aA" icon in address bar', 'info');
                    log('2. Tap "Website Settings"', 'info');
                    log('3. Set Camera to "Allow"', 'info');
                    log('4. Refresh this page', 'info');
                }
                else if (error.name === 'NotFoundError') {
                    log('🛑 No camera found on device', 'error');
                }
                else if (error.name === 'NotReadableError') {
                    log('🛑 Camera is in use by another app', 'error');
                }
            }
        }
        
        // Auto-run on load
        window.addEventListener('load', () => {
            log('🚀 Camera Test Page Loaded', 'success');
            log('Safari version: ' + navigator.userAgent, 'info');
            log('', 'info');
            setTimeout(() => testPermissions(), 500);
        });
    </script>
</body>
</html>
"""
