"""avatar.py - a pretty animated cartoon avatar with lip-sync, blinking and motion."""
import base64

import streamlit.components.v1 as components


def _b64_audio(audio_bytes: bytes) -> str:
    return base64.b64encode(audio_bytes).decode()


def avatar_card(name: str = "Mistake-to-Mastery",
                subtitle: str = "Your AI presenter",
                audio_bytes: bytes | None = None,
                autoplay: bool = False):
    audio_b64 = _b64_audio(audio_bytes) if audio_bytes else ""
    autoplay_attr = "autoplay" if (audio_bytes and autoplay) else ""

    html = f"""
    <div class="wrap">
      <div class="stage">
        <div class="halo"></div>

        <svg class="girl" id="girl" viewBox="0 0 220 260" xmlns="http://www.w3.org/2000/svg">
          <!-- back hair -->
          <path id="hairBack"
                d="M55,70 C30,90 22,150 28,205 C32,235 44,250 60,255
                   L160,255 C176,250 188,235 192,205 C198,150 190,90 165,70 Z"
                fill="#3a2419"/>
          <path d="M60,90 C42,120 40,170 48,215" stroke="#4b2f22" stroke-width="3"
                fill="none" opacity="0.6"/>

          <!-- shoulders / body -->
          <g id="body">
            <path d="M62,190 C48,200 38,220 36,260 L184,260 C182,220 172,200 158,190 Z"
                  fill="#2e2e44"/>
            <g fill="#f7b6c9" opacity="0.9">
              <circle cx="70" cy="215" r="4"/>
              <circle cx="98" cy="228" r="4"/>
              <circle cx="128" cy="213" r="4"/>
              <circle cx="152" cy="232" r="4"/>
              <circle cx="86" cy="245" r="3"/>
              <circle cx="118" cy="248" r="3"/>
            </g>
            <g fill="#c77b95" opacity="0.8">
              <circle cx="82" cy="222" r="2"/>
              <circle cx="112" cy="235" r="2"/>
              <circle cx="140" cy="225" r="2"/>
            </g>
            <path d="M97,175 Q110,185 123,175 L124,195 Q110,200 96,195 Z" fill="#e8b48a"/>
          </g>

          <!-- left arm (waves) -->
          <g id="armL">
            <path d="M60,205 Q30,215 20,245" stroke="#f0c39b" stroke-width="13"
                  stroke-linecap="round" fill="none"/>
            <circle cx="18" cy="248" r="7" fill="#f0c39b"/>
          </g>
          <!-- right arm -->
          <g id="armR">
            <path d="M160,205 Q190,215 200,245" stroke="#f0c39b" stroke-width="13"
                  stroke-linecap="round" fill="none"/>
            <circle cx="202" cy="248" r="7" fill="#f0c39b"/>
          </g>

          <!-- head group -->
          <g id="head">
            <!-- face -->
            <ellipse cx="110" cy="110" rx="42" ry="50" fill="#f2c69f"/>
            <path d="M78,128 Q110,160 142,128" fill="#f2c69f"/>

            <!-- ears + earrings -->
            <ellipse cx="70" cy="112" rx="6" ry="9" fill="#eab88e"/>
            <ellipse cx="150" cy="112" rx="6" ry="9" fill="#eab88e"/>
            <circle cx="70" cy="124" r="2.4" fill="#c9c9d6"/>
            <circle cx="150" cy="124" r="2.4" fill="#c9c9d6"/>

            <!-- front hair -->
            <path d="M66,100 C64,60 78,42 110,42 C142,42 156,60 154,100
                     C150,74 138,60 110,60 C82,60 70,74 66,100 Z" fill="#3a2419"/>
            <path d="M66,90 C74,68 94,60 118,64 C100,68 86,78 78,96 Z" fill="#4b2f22"/>
            <path d="M148,80 Q158,110 152,150" stroke="#3a2419" stroke-width="4"
                  fill="none" stroke-linecap="round"/>

            <!-- eyebrows (raised, friendly) -->
            <path d="M84,92 Q92,86 100,91" stroke="#3a2419" stroke-width="2.8"
                  fill="none" stroke-linecap="round"/>
            <path d="M120,91 Q128,86 136,92" stroke="#3a2419" stroke-width="2.8"
                  fill="none" stroke-linecap="round"/>

            <!-- eyes: blinks + glances -->
            <g id="eyes">
              <path d="M78,101 Q88,95 98,101" stroke="#2a1a12" stroke-width="2.4"
                    fill="none" stroke-linecap="round"/>
              <path d="M122,101 Q132,95 142,101" stroke="#2a1a12" stroke-width="2.4"
                    fill="none" stroke-linecap="round"/>
              <ellipse cx="88" cy="109" rx="9" ry="8" fill="#ffffff"/>
              <ellipse cx="132" cy="109" rx="9" ry="8" fill="#ffffff"/>
              <g id="irises">
                <circle cx="89" cy="110" r="5.8" fill="#5a3a22"/>
                <circle cx="133" cy="110" r="5.8" fill="#5a3a22"/>
                <circle cx="90.5" cy="108.5" r="1.7" fill="#ffffff"/>
                <circle cx="134.5" cy="108.5" r="1.7" fill="#ffffff"/>
              </g>
              <ellipse id="lidL" cx="88" cy="109" rx="9" ry="8" fill="#f2c69f" opacity="0"/>
              <ellipse id="lidR" cx="132" cy="109" rx="9" ry="8" fill="#f2c69f" opacity="0"/>
            </g>

            <!-- blush -->
            <ellipse id="blushL" cx="82" cy="126" rx="9" ry="5.5" fill="#ef8a8a" opacity="0.45"/>
            <ellipse id="blushR" cx="138" cy="126" rx="9" ry="5.5" fill="#ef8a8a" opacity="0.45"/>

            <!-- nose -->
            <path d="M110,118 L110,127 Q111,130 115,129" stroke="#d29a72"
                  stroke-width="1.8" fill="none" stroke-linecap="round"/>

            <!-- lips: warm smiling mouth with teeth -->
            <g id="mouth" transform="translate(110,140)">
              <path class="lipLine"
                    d="M-14,-1 Q-7,-6 0,-3 Q7,-6 14,-1"
                    stroke="#b04b5d" stroke-width="2.2" fill="none" stroke-linecap="round"/>
              <path d="M-9,0 Q0,3 9,0 L8,2 Q0,5 -8,2 Z" fill="#fff5f5" opacity="0.9"/>
              <path d="M-10,1 Q0,7 10,1 Q0,10 -10,1 Z" fill="#b04b5d" opacity="0.85"/>
              <ellipse class="lipOpen" cx="0" cy="3" rx="8" ry="0" fill="#7d2b3b"/>
            </g>
          </g>

          <!-- sparkles while speaking -->
          <g id="sparkles" opacity="0">
            <circle class="sp s1" cx="30" cy="60" r="3" fill="#fbbf24"/>
            <circle class="sp s2" cx="190" cy="80" r="3" fill="#a78bfa"/>
            <circle class="sp s3" cx="40" cy="180" r="2.5" fill="#f472b6"/>
            <circle class="sp s4" cx="195" cy="200" r="2.5" fill="#60a5fa"/>
          </g>
        </svg>

        <div class="ring"></div>
      </div>

      <div class="name">{name}</div>
      <div class="subtitle">{subtitle}</div>
      <div class="row">
        {"<button id='play'>🔊 Listen</button>" if audio_b64 else ""}
        <span class="status" id="status">idle</span>
      </div>
      {"<audio id='aud' " + autoplay_attr + " src='data:audio/mp3;base64," + audio_b64 + "'></audio>" if audio_b64 else ""}
    </div>

    <style>
    * {{ box-sizing: border-box; }}
    .wrap {{
      font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
      text-align: center;
      padding: 16px 12px 8px;
      background: linear-gradient(180deg,#f6f4ff 0%,#ffffff 100%);
      border-radius: 18px;
      border: 1px solid #ede9fe;
    }}
    .stage {{ position: relative; width: 240px; height: 290px; margin: 0 auto 10px; }}

    .halo {{
      position: absolute; inset: -20px; border-radius: 50%;
      background: radial-gradient(circle at 50% 45%,
                 rgba(167,139,250,.55), rgba(167,139,250,0) 68%);
      filter: blur(10px); z-index: 0;
    }}
    .girl {{
      position: relative; z-index: 2; width: 100%; height: 100%;
      filter: drop-shadow(0 14px 20px rgba(79,70,229,.25));
      animation: breathe 4s ease-in-out infinite;
      transform-origin: 50% 82%;
    }}
    @keyframes breathe {{
      0%,100% {{ transform: translateY(0) scale(1); }}
      50%     {{ transform: translateY(-3px) scale(1.008); }}
    }}

    #head {{ transform-origin: 110px 175px; animation: nod 5.5s ease-in-out infinite; }}
    @keyframes nod {{
      0%,100% {{ transform: rotate(0deg) translateY(0); }}
      50%     {{ transform: rotate(1.4deg) translateY(-2px); }}
    }}

    #hairBack {{ transform-origin: 110px 60px; animation: sway 5s ease-in-out infinite; }}
    @keyframes sway {{
      0%,100% {{ transform: rotate(-1.2deg); }}
      50%     {{ transform: rotate(1.2deg); }}
    }}

    #irises {{ animation: glance 7s ease-in-out infinite; }}
    @keyframes glance {{
      0%, 45%, 100% {{ transform: translateX(0); }}
      55%, 65%       {{ transform: translateX(1.5px); }}
      75%, 85%       {{ transform: translateX(-1.5px); }}
    }}

    #lidL, #lidR {{ animation: blink 5.2s infinite; }}
    @keyframes blink {{
      0%, 91%, 100% {{ opacity: 0; }}
      93%, 96%       {{ opacity: 1; }}
    }}

    /* speaking mode */
    .girl.speaking {{ animation: talkBob 0.55s ease-in-out infinite; }}
    @keyframes talkBob {{
      0%,100% {{ transform: translateY(0) rotate(-0.6deg); }}
      50%     {{ transform: translateY(-7px) rotate(0.6deg); }}
    }}

    .girl.speaking #mouth .lipOpen {{
      animation: lipTalk 0.24s ease-in-out infinite;
    }}
    @keyframes lipTalk {{
      0%,100% {{ ry: 0.6; }}
      50%     {{ ry: 4.2; }}
    }}
    .girl.speaking .lipLine {{
      animation: lipShift 0.4s ease-in-out infinite;
    }}
    @keyframes lipShift {{
      0%,100% {{ transform: translateX(0); }}
      50%     {{ transform: translateX(0.6px); }}
    }}

    .girl.speaking #blushL, .girl.speaking #blushR {{
      animation: blush 1s ease-in-out infinite;
    }}
    @keyframes blush {{
      0%,100% {{ opacity: 0.45; }}
      50%     {{ opacity: 0.7; }}
    }}

    .girl.speaking #armL {{
      animation: waveL 0.85s ease-in-out infinite;
      transform-origin: 60px 205px;
    }}
    .girl.speaking #armR {{
      animation: waveR 1.1s ease-in-out infinite;
      transform-origin: 160px 205px;
    }}
    @keyframes waveL {{
      0%,100% {{ transform: rotate(0deg); }}
      50%     {{ transform: rotate(-16deg); }}
    }}
    @keyframes waveR {{
      0%,100% {{ transform: rotate(0deg); }}
      50%     {{ transform: rotate(10deg); }}
    }}

    .girl.speaking #sparkles {{ opacity: 1; }}
    .girl.speaking .sp {{ animation: sparkle 1.4s ease-in-out infinite; }}
    .girl.speaking .s2 {{ animation-delay:.35s; }}
    .girl.speaking .s3 {{ animation-delay:.7s; }}
    .girl.speaking .s4 {{ animation-delay:1.05s; }}
    @keyframes sparkle {{
      0%,100% {{ opacity: 0; transform: scale(.4); }}
      45%     {{ opacity: 1; transform: scale(1.3); }}
    }}

    .ring {{
      position: absolute; inset: -10px; border-radius: 50%;
      border: 2px dashed rgba(124,58,237,.38); z-index: 1;
      animation: spin 26s linear infinite;
      pointer-events: none;
    }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}

    .name {{ font-weight: 800; font-size: 1.05rem; color:#1f2937; }}
    .subtitle {{ color:#6b7280; font-size:.82rem; margin-bottom: 8px; }}
    .row {{ display:flex; justify-content:center; align-items:center; gap:10px; margin-top:4px; }}
    #play {{
      border:none; background:#4f46e5; color:#fff; font-weight:700;
      padding:8px 16px; border-radius:10px; cursor:pointer;
      box-shadow:0 6px 16px rgba(79,70,229,.3);
      transition: transform .12s ease, background .12s ease;
    }}
    #play:hover {{ background:#4338ca; transform: translateY(-1px); }}
    .status {{ font-size:.75rem; color:#9ca3af; }}
    </style>

    <script>
    const girl   = document.getElementById('girl');
    const aud    = document.getElementById('aud');
    const play   = document.getElementById('play');
    const status = document.getElementById('status');

    function setSpeaking(on) {{
      girl.classList.toggle('speaking', on);
      status.textContent = on ? 'speaking…' : 'idle';
    }}

    if (aud) {{
      aud.addEventListener('play',  () => setSpeaking(true));
      aud.addEventListener('ended', () => setSpeaking(false));
      aud.addEventListener('pause', () => setSpeaking(false));
      if (play) play.addEventListener('click', () => {{ aud.currentTime = 0; aud.play(); }});
      if ({str(autoplay).lower()}) {{
        aud.play().catch(() => setSpeaking(false));
      }}
    }}
    </script>
    """
    components.html(html, height=400)


def render_presenter_avatar(audio_bytes: bytes | None = None, autoplay: bool = False):
    avatar_card(
        name="Mistake-to-Mastery",
        subtitle="Your AI presenter · speaking",
        audio_bytes=audio_bytes,
        autoplay=autoplay,
    )