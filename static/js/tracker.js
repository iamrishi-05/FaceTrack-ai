/**
 * FaceTrack AI - Live Target Scanner & Detection Engine
 * High-performance WebRTC webcam frame streaming & HTML5 canvas bounding box overlay renderer.
 */

let videoElement = null;
let canvasElement = null;
let canvasCtx = null;
let isScanning = false;
let currentStream = null;

let lastFrameTime = performance.now();
let fpsCounter = 0;
let frameCount = 0;

// Web Audio API Chime Synth for Target Detection
let audioCtx = null;

function initAudioSynth() {
    try {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
    } catch (e) {
        console.warn("AudioContext not supported");
    }
}

function playTargetChime() {
    const audioToggle = document.getElementById('audioAlertToggle');
    if (audioToggle && !audioToggle.checked) return;
    
    try {
        initAudioSynth();
        if (!audioCtx) return;
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
        
        const now = audioCtx.currentTime;
        
        // Two-tone cheerful chime (E5 -> A5)
        const osc1 = audioCtx.createOscillator();
        const gain1 = audioCtx.createGain();
        osc1.type = 'sine';
        osc1.frequency.setValueAtTime(659.25, now); // E5
        osc1.frequency.setValueAtTime(880.00, now + 0.12); // A5
        
        gain1.gain.setValueAtTime(0.15, now);
        gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.4);
        
        osc1.connect(gain1);
        gain1.connect(audioCtx.destination);
        
        osc1.start(now);
        osc1.stop(now + 0.4);
    } catch (e) {
        console.log("Audio chime error:", e);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    videoElement = document.getElementById('webcamVideo');
    canvasElement = document.getElementById('overlayCanvas');
    if (canvasElement) {
        canvasCtx = canvasElement.getContext('2d');
    }

    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const cameraSelect = document.getElementById('cameraSelect');

    if (startBtn) startBtn.addEventListener('click', startScanner);
    if (stopBtn) stopBtn.addEventListener('click', stopScanner);

    populateCameras();

    // Unlock Web Audio API on user click
    document.addEventListener('click', () => {
        initAudioSynth();
    }, { once: true });
});

async function populateCameras() {
    const cameraSelect = document.getElementById('cameraSelect');
    if (!cameraSelect) return;

    try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(d => d.kind === 'videoinput');

        cameraSelect.innerHTML = '';
        if (videoDevices.length === 0) {
            cameraSelect.innerHTML = '<option value="">No camera detected</option>';
            return;
        }

        videoDevices.forEach((device, index) => {
            const option = document.createElement('option');
            option.value = device.deviceId;
            option.text = device.label || `Camera ${index + 1}`;
            cameraSelect.appendChild(option);
        });
    } catch (err) {
        console.warn("Could not enumerate camera devices:", err);
    }
}

async function startScanner() {
    if (isScanning) return;

    const cameraSelect = document.getElementById('cameraSelect');
    const deviceId = cameraSelect ? cameraSelect.value : null;

    const constraints = {
        video: {
            deviceId: deviceId ? { exact: deviceId } : undefined,
            width: { ideal: 1280 },
            height: { ideal: 720 },
            facingMode: 'user'
        }
    };

    try {
        currentStream = await navigator.mediaDevices.getUserMedia(constraints);
        videoElement.srcObject = currentStream;

        videoElement.onloadedmetadata = () => {
            videoElement.play();
            resizeCanvas();
            isScanning = true;

            // UI updates
            document.getElementById('cameraPlaceholder').classList.add('d-none');
            document.getElementById('startBtn').classList.add('d-none');
            document.getElementById('stopBtn').classList.remove('d-none');
            document.getElementById('cameraPulseDot').style.display = 'inline-block';
            
            const badge = document.getElementById('scannerStatusBadge');
            if (badge) {
                badge.className = 'badge bg-emerald text-dark fw-bold px-2 py-1 extra-small';
                badge.innerText = 'Scanning Live';
            }
            const statusText = document.getElementById('scannerStatusText');
            if (statusText) statusText.innerText = 'Active Tracking';

            // Start processing loop
            requestAnimationFrame(processFrameLoop);
        };
    } catch (err) {
        alert("Camera Access Error: " + err.message + "\nPlease allow camera permissions.");
        console.error("Camera getUserMedia error:", err);
    }
}

function stopScanner() {
    isScanning = false;
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;
    }

    if (canvasCtx && canvasElement) {
        canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    }

    document.getElementById('cameraPlaceholder').classList.remove('d-none');
    document.getElementById('startBtn').classList.remove('d-none');
    document.getElementById('stopBtn').classList.add('d-none');
    document.getElementById('cameraPulseDot').style.display = 'none';

    const badge = document.getElementById('scannerStatusBadge');
    if (badge) {
        badge.className = 'badge bg-secondary text-light px-2 py-1 extra-small';
        badge.innerText = 'Paused';
    }
    const statusText = document.getElementById('scannerStatusText');
    if (statusText) statusText.innerText = 'Camera Inactive';
}

function resizeCanvas() {
    if (!videoElement || !canvasElement) return;
    canvasElement.width = videoElement.clientWidth || videoElement.videoWidth || 640;
    canvasElement.height = videoElement.clientHeight || videoElement.videoHeight || 480;
}

window.addEventListener('resize', resizeCanvas);

let isSendingFrame = false;

async function processFrameLoop() {
    if (!isScanning) return;

    // Calculate FPS
    frameCount++;
    const now = performance.now();
    if (now - lastFrameTime >= 1000) {
        fpsCounter = Math.round((frameCount * 1000) / (now - lastFrameTime));
        frameCount = 0;
        lastFrameTime = now;
        const fpsEl = document.getElementById('fpsCounter');
        if (fpsEl) fpsEl.innerText = fpsCounter;
    }

    if (!isSendingFrame && videoElement.videoWidth > 0) {
        isSendingFrame = true;
        const startTime = performance.now();

        // Create temporary offscreen canvas to capture compressed JPEG frame
        const offCanvas = document.createElement('canvas');
        offCanvas.width = 640; // Scale frame for ultra-fast API processing
        offCanvas.height = Math.round((videoElement.videoHeight / videoElement.videoWidth) * 640) || 360;
        const offCtx = offCanvas.getContext('2d');
        offCtx.drawImage(videoElement, 0, 0, offCanvas.width, offCanvas.height);

        const base64Data = offCanvas.toDataURL('image/jpeg', 0.75);

        try {
            const response = await fetch('/api/recognize_frame', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: base64Data })
            });

            const data = await response.json();
            const latency = Math.round(performance.now() - startTime);

            const latencyEl = document.getElementById('latencyCounter');
            if (latencyEl) latencyEl.innerText = `${latency}ms`;

            if (data.success) {
                renderOverlay(data.results, offCanvas.width, offCanvas.height);
                handleDetectionResults(data.results);
            }
        } catch (err) {
            console.error("Frame recognition API error:", err);
        } finally {
            isSendingFrame = false;
        }
    }

    if (isScanning) {
        setTimeout(() => requestAnimationFrame(processFrameLoop), 80); // ~12 FPS throttle
    }
}

function renderOverlay(results, frameW, frameH) {
    if (!canvasCtx || !canvasElement) return;

    resizeCanvas();
    const displayW = canvasElement.width;
    const displayH = canvasElement.height;

    canvasCtx.clearRect(0, 0, displayW, displayH);

    const scaleX = displayW / frameW;
    const scaleY = displayH / frameH;

    const facesCountEl = document.getElementById('facesCount');
    if (facesCountEl) facesCountEl.innerText = results ? results.length : 0;

    if (!results || results.length === 0) return;

    results.forEach(res => {
        const { top, right, bottom, left } = res.location;

        const x = left * scaleX;
        const y = top * scaleY;
        const w = (right - left) * scaleX;
        const h = (bottom - top) * scaleY;

        const isMatched = res.matched;
        const color = isMatched ? '#10b981' : '#ef4444'; // Emerald Green vs Crimson Red

        // 1. Draw Glowing Bounding Box
        canvasCtx.save();
        canvasCtx.strokeStyle = color;
        canvasCtx.lineWidth = 3;
        canvasCtx.shadowColor = color;
        canvasCtx.shadowBlur = 12;
        canvasCtx.strokeRect(x, y, w, h);
        canvasCtx.restore();

        // 2. Corner Target Accents
        const cornerLen = Math.min(w, h) * 0.2;
        canvasCtx.strokeStyle = color;
        canvasCtx.lineWidth = 4;
        
        // Top-Left corner
        canvasCtx.beginPath();
        canvasCtx.moveTo(x, y + cornerLen);
        canvasCtx.lineTo(x, y);
        canvasCtx.lineTo(x + cornerLen, y);
        canvasCtx.stroke();

        // Top-Right corner
        canvasCtx.beginPath();
        canvasCtx.moveTo(x + w - cornerLen, y);
        canvasCtx.lineTo(x + w, y);
        canvasCtx.lineTo(x + w, y + cornerLen);
        canvasCtx.stroke();

        // 3. Name & Confidence Badge Tag
        canvasCtx.fillStyle = color;
        const labelText = isMatched ? `${res.name} (${res.confidence}%)` : `UNKNOWN`;
        canvasCtx.font = 'bold 14px "Outfit", sans-serif';
        const textWidth = canvasCtx.measureText(labelText).width;

        const badgeH = 26;
        const badgeW = textWidth + 20;
        const badgeY = Math.max(0, y - badgeH - 6);

        canvasCtx.fillRect(x, badgeY, badgeW, badgeH);

        canvasCtx.fillStyle = '#000000';
        canvasCtx.fillText(labelText, x + 10, badgeY + 18);
    });
}

let lastMatchTargetID = null;

function handleDetectionResults(results) {
    if (!results) return;

    const matchedTarget = results.find(r => r.matched);

    const matchContent = document.getElementById('matchContent');
    const noMatchContent = document.getElementById('noMatchContent');

    if (matchedTarget) {
        if (noMatchContent) noMatchContent.classList.add('d-none');
        if (matchContent) matchContent.classList.remove('d-none');

        document.getElementById('matchTargetName').innerText = matchedTarget.name;
        document.getElementById('matchTargetID').innerText = matchedTarget.target_id;
        document.getElementById('matchConfidenceBadge').innerText = `Match: ${matchedTarget.confidence}%`;

        if (matchedTarget.photo_path) {
            document.getElementById('matchTargetPhoto').src = matchedTarget.photo_path;
        }

        const liv = matchedTarget.liveness || {};
        document.getElementById('matchEmotion').innerText = liv.emotion || 'neutral';
        document.getElementById('matchMask').innerText = liv.mask_detected ? 'Mask On 😷' : 'No Mask';
        document.getElementById('matchSmile').innerText = liv.smile_detected ? 'Smiling 😊' : 'Neutral';

        document.getElementById('matchTimestamp').innerText = new Date().toLocaleTimeString();

        // Trigger chime audio alert when target appears
        if (lastMatchTargetID !== matchedTarget.target_id) {
            lastMatchTargetID = matchedTarget.target_id;
            playTargetChime();
        }
    }
}
