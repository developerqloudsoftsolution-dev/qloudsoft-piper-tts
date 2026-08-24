"""
Interactive Web Dashboard & Playground for Realistic Hindi Neural TTS Studio.
Provides a modern, responsive UI at root ('/') to test speech synthesis in real-time.
"""

def get_dashboard_html(model_name: str, sample_rate: int, max_length: int, auth_enabled: bool) -> str:
    auth_badge_text = "Bearer Auth Required" if auth_enabled else "Open Access (Dev Mode)"
    auth_badge_class = "badge-warning" if auth_enabled else "badge-success"
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Realistic Hindi Neural TTS Studio • Qloudflow</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #090D16;
            --bg-secondary: #0F172A;
            --bg-card: rgba(17, 24, 39, 0.85);
            --bg-card-hover: rgba(30, 41, 59, 0.8);
            --border-color: rgba(255, 255, 255, 0.08);
            --border-focus: rgba(236, 72, 153, 0.6);
            --text-main: #F8FAFC;
            --text-muted: #94A3B8;
            --text-dim: #64748B;
            --accent-primary: #EC4899;
            --accent-primary-hover: #DB2777;
            --accent-gradient: linear-gradient(135deg, #EC4899 0%, #8B5CF6 50%, #3B82F6 100%);
            --accent-emerald: #10B981;
            --accent-cyan: #06B6D4;
            --accent-amber: #F59E0B;
            --radius-lg: 16px;
            --radius-md: 10px;
            --radius-sm: 6px;
            --shadow-glow: 0 0 30px rgba(236, 72, 153, 0.25);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            background-image: 
                radial-gradient(at 0% 0%, rgba(236, 72, 153, 0.12) 0px, transparent 50%),
                radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.12) 0px, transparent 50%),
                radial-gradient(at 50% 100%, rgba(6, 182, 212, 0.08) 0px, transparent 50%);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }}

        .container {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 2.5rem 1.5rem 4rem;
            width: 100%;
        }}

        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2.5rem;
            flex-wrap: wrap;
            gap: 1rem;
        }}

        .brand {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .brand-icon {{
            width: 52px;
            height: 52px;
            background: var(--accent-gradient);
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: var(--shadow-glow);
        }}

        .brand-icon svg {{
            width: 28px;
            height: 28px;
            color: #FFFFFF;
        }}

        .brand-text h1 {{
            font-size: 1.6rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #FFFFFF 30%, #F472B6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .brand-text p {{
            font-size: 0.88rem;
            color: var(--text-muted);
        }}

        .nav-actions {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.35rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }}

        .badge-success {{
            background: rgba(16, 185, 129, 0.15);
            color: #34D399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}

        .badge-star {{
            background: linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(139, 92, 246, 0.2));
            color: #F472B6;
            border: 1px solid rgba(236, 72, 153, 0.4);
        }}

        .badge-dot {{
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: currentColor;
            box-shadow: 0 0 6px currentColor;
        }}

        .grid-layout {{
            display: grid;
            grid-template-columns: 1.2fr 0.8fr;
            gap: 1.75rem;
        }}

        @media (max-width: 900px) {{
            .grid-layout {{
                grid-template-columns: 1fr;
            }}
        }}

        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 1.75rem;
            backdrop-filter: blur(16px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
            transition: border-color 0.2s, box-shadow 0.2s;
        }}

        .card:hover {{
            border-color: rgba(255, 255, 255, 0.12);
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.25rem;
        }}

        .card-title {{
            font-size: 1.1rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .form-group {{
            margin-bottom: 1.25rem;
        }}

        .form-label {{
            display: block;
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
        }}

        .form-control {{
            width: 100%;
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 0.85rem 1rem;
            color: var(--text-main);
            font-family: inherit;
            font-size: 0.95rem;
            transition: all 0.2s;
            outline: none;
        }}

        .form-control:focus {{
            border-color: var(--border-focus);
            box-shadow: 0 0 0 3px rgba(236, 72, 153, 0.2);
        }}

        textarea.form-control {{
            min-height: 120px;
            resize: vertical;
            line-height: 1.6;
        }}

        .sample-pills {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.6rem;
        }}

        .sample-pill {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 9999px;
            padding: 0.35rem 0.75rem;
            font-size: 0.78rem;
            color: var(--text-muted);
            cursor: pointer;
            transition: all 0.15s ease;
            user-select: none;
        }}

        .sample-pill:hover {{
            background: rgba(236, 72, 153, 0.15);
            border-color: rgba(236, 72, 153, 0.3);
            color: #F472B6;
            transform: translateY(-1px);
        }}

        .voice-select-box {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 0.6rem;
            margin-bottom: 1.25rem;
        }}

        .voice-card {{
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 0.75rem;
            cursor: pointer;
            transition: all 0.2s;
            position: relative;
        }}

        .voice-card:hover {{
            border-color: rgba(236, 72, 153, 0.4);
            background: rgba(30, 41, 59, 0.8);
        }}

        .voice-card.active {{
            border-color: #EC4899;
            background: rgba(236, 72, 153, 0.12);
            box-shadow: 0 0 15px rgba(236, 72, 153, 0.2);
        }}

        .voice-card-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.25rem;
        }}

        .voice-card-name {{
            font-weight: 700;
            font-size: 0.9rem;
        }}

        .voice-card-sub {{
            font-size: 0.75rem;
            color: var(--text-dim);
        }}

        .controls-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-bottom: 1.25rem;
        }}

        .slider-wrap {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .slider-wrap input[type="range"] {{
            flex: 1;
            accent-color: #EC4899;
        }}

        .slider-val {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            color: var(--text-muted);
            min-width: 45px;
        }}

        .btn-primary {{
            width: 100%;
            background: var(--accent-gradient);
            border: none;
            border-radius: var(--radius-md);
            padding: 0.95rem 1.5rem;
            color: #FFFFFF;
            font-family: inherit;
            font-weight: 700;
            font-size: 1rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.6rem;
            box-shadow: 0 4px 20px rgba(236, 72, 153, 0.35);
            transition: all 0.2s;
        }}

        .btn-primary:hover {{
            opacity: 0.95;
            transform: translateY(-1px);
            box-shadow: 0 6px 25px rgba(236, 72, 153, 0.45);
        }}

        .btn-primary:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }}

        .audio-player-card {{
            margin-top: 1.5rem;
            background: rgba(15, 23, 42, 0.95);
            border: 1px solid rgba(236, 72, 153, 0.3);
            border-radius: var(--radius-md);
            padding: 1.25rem;
            display: none;
            animation: fadeIn 0.3s ease;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .player-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }}

        .player-info {{
            font-size: 0.85rem;
            color: var(--text-muted);
        }}

        audio {{
            width: 100%;
            border-radius: 8px;
            outline: none;
        }}

        .meta-list {{
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }}

        .meta-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.6rem 0.85rem;
            background: rgba(15, 23, 42, 0.6);
            border-radius: var(--radius-sm);
            font-size: 0.85rem;
        }}

        .meta-label {{
            color: var(--text-muted);
        }}

        .meta-val {{
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            color: var(--text-main);
        }}

        .code-box {{
            background: rgba(10, 15, 29, 0.95);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 1rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            color: #E2E8F0;
            overflow-x: auto;
            line-height: 1.5;
            margin-top: 1rem;
        }}

        .tab-nav {{
            display: flex;
            gap: 0.5rem;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
        }}

        .tab-btn {{
            background: none;
            border: none;
            color: var(--text-muted);
            font-family: inherit;
            font-size: 0.85rem;
            font-weight: 600;
            padding: 0.4rem 0.8rem;
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: all 0.2s;
        }}

        .tab-btn.active {{
            background: rgba(236, 72, 153, 0.15);
            color: #F472B6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="brand">
                <div class="brand-icon">
                    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 100-6 3 3 0 000 6z" />
                    </svg>
                </div>
                <div class="brand-text">
                    <h1>Realistic Hindi Neural Voice Studio</h1>
                    <p>Powered by Studio-Grade Azure Neural Models (Swara & Madhur) • Ultra-Human Prosody</p>
                </div>
            </div>
            <div class="nav-actions">
                <span class="badge badge-star">
                    <span class="badge-dot"></span>
                    🇮🇳 Swara Neural Active
                </span>
                <span class="badge {auth_badge_class}">
                    {auth_badge_text}
                </span>
            </div>
        </div>

        <!-- Main Workspace -->
        <div class="grid-layout">
            <!-- Left Column: Synthesizer Studio -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">
                        <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="#EC4899">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        Voice Synthesizer
                    </div>
                </div>

                <!-- Voice Selection -->
                <div class="form-group">
                    <label class="form-label">Select Voice Character</label>
                    <div class="voice-select-box" id="voiceSelector">
                        <!-- Swara (Default Star) -->
                        <div class="voice-card active" onclick="selectVoice('hi-IN-SwaraNeural', this)">
                            <div class="voice-card-top">
                                <span class="voice-card-name">🇮🇳 Swara (Female)</span>
                                <span class="badge badge-star" style="padding: 0.15rem 0.4rem; font-size: 0.65rem;">Star</span>
                            </div>
                            <div class="voice-card-sub">Ultra-Realistic Hindi / Hinglish</div>
                        </div>
                        <!-- Madhur -->
                        <div class="voice-card" onclick="selectVoice('hi-IN-MadhurNeural', this)">
                            <div class="voice-card-top">
                                <span class="voice-card-name">🇮🇳 Madhur (Male)</span>
                                <span class="badge badge-success" style="padding: 0.15rem 0.4rem; font-size: 0.65rem;">HD</span>
                            </div>
                            <div class="voice-card-sub">Clear Confident Hindi Male</div>
                        </div>
                        <!-- Neerja -->
                        <div class="voice-card" onclick="selectVoice('en-IN-NeerjaNeural', this)">
                            <div class="voice-card-top">
                                <span class="voice-card-name">🇮🇳 Neerja (English)</span>
                            </div>
                            <div class="voice-card-sub">Fluent Indian Accent Female</div>
                        </div>
                        <!-- Prabhat -->
                        <div class="voice-card" onclick="selectVoice('en-IN-PrabhatNeural', this)">
                            <div class="voice-card-top">
                                <span class="voice-card-name">🇮🇳 Prabhat (English)</span>
                            </div>
                            <div class="voice-card-sub">Professional Indian Male</div>
                        </div>
                    </div>
                </div>

                <!-- Text Input -->
                <div class="form-group">
                    <label class="form-label">Speech Text (Hindi / Hinglish / English)</label>
                    <textarea id="ttsTextInput" class="form-control" placeholder="Type or paste Hindi / Hinglish text here...">नमस्ते! Qloudflow व्हाट्सएप ऑटोमेशन में आपका स्वागत है। आपका ऑर्डर सफलतापूर्वक कन्फर्म हो गया है।</textarea>
                    
                    <div class="sample-pills">
                        <span class="sample-pill" onclick="setSample(1)">🇮🇳 Pure Hindi Welcome</span>
                        <span class="sample-pill" onclick="setSample(2)">🇮🇳 Hinglish Order Confirm</span>
                        <span class="sample-pill" onclick="setSample(3)">🇮🇳 WhatsApp Support Prompt</span>
                        <span class="sample-pill" onclick="setSample(4)">🇮🇳 Indian English Corporate</span>
                    </div>
                </div>

                <!-- Speech Controls -->
                <div class="controls-row">
                    <div class="form-group">
                        <label class="form-label">Speed / Rate</label>
                        <div class="slider-wrap">
                            <input type="range" id="rateRange" min="-20" max="40" step="5" value="0" oninput="updateRateLabel(this.value)">
                            <span class="slider-val" id="rateVal">+0%</span>
                        </div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Pitch Adjustment</label>
                        <div class="slider-wrap">
                            <input type="range" id="pitchRange" min="-10" max="10" step="2" value="0" oninput="updatePitchLabel(this.value)">
                            <span class="slider-val" id="pitchVal">+0Hz</span>
                        </div>
                    </div>
                </div>

                <!-- Action Button -->
                <button id="generateBtn" class="btn-primary" onclick="generateSpeech()">
                    <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Synthesize Realistic Speech
                </button>

                <!-- Audio Output Card -->
                <div id="audioCard" class="audio-player-card">
                    <div class="player-header">
                        <div class="player-info" id="playerInfo">Ready • Swara Neural (24kHz HD)</div>
                        <span class="badge badge-success" id="latencyBadge">⚡ 120ms</span>
                    </div>
                    <audio id="audioElement" controls autoplay></audio>
                </div>
            </div>

            <!-- Right Column: API & Integration Details -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">
                        <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="#8B5CF6">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                        </svg>
                        API Integration
                    </div>
                </div>

                <div class="meta-list">
                    <div class="meta-item">
                        <span class="meta-label">Primary Voice Engine</span>
                        <span class="meta-val" style="color: #F472B6;">Microsoft Azure Neural (Swara)</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Default Audio Format</span>
                        <span class="meta-val">MP3 (High Fidelity)</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Offline Fallback Engine</span>
                        <span class="meta-val">Piper ONNX (Local)</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">API Key Required</span>
                        <span class="meta-val" style="color: #34D399;">No (100% Free & Open)</span>
                    </div>
                </div>

                <div style="margin-top: 1.5rem;">
                    <div class="tab-nav">
                        <button class="tab-btn active" onclick="switchTab('curl', this)">cURL</button>
                        <button class="tab-btn" onclick="switchTab('php', this)">PHP (Laravel)</button>
                        <button class="tab-btn" onclick="switchTab('js', this)">JavaScript</button>
                    </div>

                    <div id="codeTabCurl" class="code-box">
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{{"text": "नमस्ते! आपका स्वागत है।", "voice": "hi-IN-SwaraNeural"}}' \
  --output speech.mp3
                    </div>

                    <div id="codeTabPhp" class="code-box" style="display: none;">
$response = Http::post('http://localhost:8000/tts', [
    'text'  => 'Namaste! Aapka order confirm ho gaya hai.',
    'voice' => 'hi-IN-SwaraNeural'
]);

if ($response->successful()) {{
    $audioMp3 = $response->body();
}}
                    </div>

                    <div id="codeTabJs" class="code-box" style="display: none;">
const res = await fetch('http://localhost:8000/tts', {{
  method: 'POST',
  headers: {{ 'Content-Type': 'application/json' }},
  body: JSON.stringify({{
    text: 'Namaste! How can I help you today?',
    voice: 'hi-IN-SwaraNeural'
  }})
}});
const audioBlob = await res.blob();
const audioUrl = URL.createObjectURL(audioBlob);
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentVoice = 'hi-IN-SwaraNeural';
        let currentRate = '+0%';
        let currentPitch = '+0Hz';

        const SAMPLES = {{
            1: "नमस्ते! Qloudflow व्हाट्सएप ऑटोमेशन में आपका स्वागत है। हम आपकी क्या सहायता कर सकते हैं?",
            2: "Namaste! Aapka order successfully confirm ho gaya hai. Tracking link WhatsApp par send kar di gayi hai.",
            3: "Hello! Hamari support team aapki ticket process kar rahi hai. Kripya thoda intezaar karein.",
            4: "Welcome to Qloudflow Solutions. Your daily report has been successfully generated and dispatched."
        }};

        function selectVoice(voiceId, elem) {{
            currentVoice = voiceId;
            document.querySelectorAll('.voice-card').forEach(c => c.classList.remove('active'));
            elem.classList.add('active');
        }}

        function setSample(index) {{
            document.getElementById('ttsTextInput').value = SAMPLES[index];
        }}

        function updateRateLabel(val) {{
            const sign = parseInt(val) >= 0 ? '+' : '';
            currentRate = sign + val + '%';
            document.getElementById('rateVal').innerText = currentRate;
        }}

        function updatePitchLabel(val) {{
            const sign = parseInt(val) >= 0 ? '+' : '';
            currentPitch = sign + val + 'Hz';
            document.getElementById('pitchVal').innerText = currentPitch;
        }}

        async function generateSpeech() {{
            const text = document.getElementById('ttsTextInput').value.trim();
            if (!text) {{
                alert('Please enter text to synthesize.');
                return;
            }}

            const btn = document.getElementById('generateBtn');
            const audioCard = document.getElementById('audioCard');
            const audioElem = document.getElementById('audioElement');
            const latencyBadge = document.getElementById('latencyBadge');
            const playerInfo = document.getElementById('playerInfo');

            btn.disabled = true;
            btn.innerHTML = '<span class="badge-dot" style="margin-right: 8px;"></span> Generating Speech...';

            const startTime = performance.now();

            try {{
                const res = await fetch('/tts', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        text: text,
                        voice: currentVoice,
                        rate: currentRate,
                        pitch: currentPitch,
                        format: 'mp3'
                    }})
                }});

                if (!res.ok) {{
                    const err = await res.json();
                    throw new Error(err.detail || 'Synthesis failed');
                }}

                const blob = await res.blob();
                const latency = Math.round(performance.now() - startTime);

                const audioUrl = URL.createObjectURL(blob);
                audioElem.src = audioUrl;
                audioCard.style.display = 'block';
                latencyBadge.innerText = '⚡ ' + latency + 'ms';
                playerInfo.innerText = currentVoice + ' (' + (blob.size / 1024).toFixed(1) + ' KB)';
                audioElem.play();
            }} catch (e) {{
                alert('TTS Error: ' + e.message);
            }} finally {{
                btn.disabled = false;
                btn.innerHTML = `
                    <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Synthesize Realistic Speech
                `;
            }}
        }}

        function switchTab(tab, elem) {{
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            elem.classList.add('active');

            document.getElementById('codeTabCurl').style.display = tab === 'curl' ? 'block' : 'none';
            document.getElementById('codeTabPhp').style.display = tab === 'php' ? 'block' : 'none';
            document.getElementById('codeTabJs').style.display = tab === 'js' ? 'block' : 'none';
        }}
    </script>
</body>
</html>
"""
    return html
