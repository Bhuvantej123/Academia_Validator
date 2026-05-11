"""
Stitch-Aligned Streamlit Frontend Dashboard
Design System: Academic Authenticity Validator (Stitch)
"""

import time
import httpx
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

API_BASE = "http://127.0.0.1:8000/api/v1"

st.set_page_config(
    page_title="AVA | Academic Authenticity",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── Stitch Design System CSS (Light Theme) ────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');

    /* Global Typography */
    html, body, [class*="css"]  {
        font-family: 'JetBrains Mono', monospace;
        color: #e0e0e0; /* on-surface */
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
        color: #00f0ff; /* neon cyan primary */
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    
    /* Main App Background - Deep Void Black */
    .stApp {
        background-color: #050505;
        background-image: none;
    }

    /* Cyber Cards */
    .glass-card {
        background: #121212;
        border: 1px solid #333333;
        border-radius: 0px;
        padding: 24px;
        box-shadow: none;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .glass-card:hover {
        border-color: #00f0ff;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.2);
    }

    /* Custom Metrics */
    .metric-value {
        font-size: 3rem;
        font-weight: 700;
        font-family: 'Space Grotesk';
        color: #00f0ff;
        margin: 0;
        line-height: 1.1;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #b026ff; /* electric purple */
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 8px;
        font-family: 'JetBrains Mono';
        font-weight: 600;
    }

    /* Primary Action Buttons */
    .stButton>button {
        background-color: #000000 !important;
        color: #00f0ff !important;
        font-family: 'Space Grotesk' !important;
        font-weight: 600 !important;
        border-radius: 0px !important;
        padding: 12px 24px !important;
        border: 1px solid #00f0ff !important;
        box-shadow: none !important;
        text-transform: uppercase;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        background-color: #00f0ff !important;
        color: #000000 !important;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.4) !important;
    }

    /* File Uploader styling */
    .stFileUploader > div > div {
        background: #0a0a0a !important;
        border: 1px dashed #333333 !important;
        border-radius: 0px !important;
        color: #a0a0a0 !important;
    }
    
    .stFileUploader > div > div:hover {
        border-color: #00f0ff !important;
        background: #121212 !important;
    }

    /* Hide standard header */
    header {visibility: hidden;}
    
    /* Expander / Flags */
    .streamlit-expanderHeader {
        background-color: #121212 !important;
        color: #00f0ff !important;
        border-radius: 0px !important;
        border: 1px solid #333333 !important;
        font-family: 'JetBrains Mono' !important;
    }
    
    /* Dividers */
    hr {
        border-color: #333333 !important;
    }
    
    /* Progress Bar override */
    .stProgress > div > div > div > div {
        background-color: #00f0ff !important;
        border-radius: 0px !important;
    }
</style>
""", unsafe_allow_html=True)


# ─── Plotly Visualisation Helpers (Light Theme) ─────────────────────────

def create_gauge_chart(score, title):
    # Cyber Colors
    if score >= 80:
        color = "#00f0ff" # Neon Cyan (Primary/Success)
    elif score >= 50:
        color = "#b026ff" # Electric Purple (Warning/Secondary)
    else:
        color = "#ff003c" # Neon Red (Error)
        
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"<span style='font-size:0.8em;color:#b026ff;font-family:Space Grotesk'>{title}</span>"},
        number = {'font': {'size': 50, 'family': 'Space Grotesk', 'color': color}, 'suffix': "%"},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#333333", 'tickfont': {'color':'#a0a0a0'}},
            'bar': {'color': color, 'thickness': 0.25},
            'bgcolor': "#121212",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 50], 'color': "rgba(255, 0, 60, 0.15)"},
                {'range': [50, 80], 'color': "rgba(176, 38, 255, 0.15)"},
                {'range': [80, 100], 'color': "rgba(0, 240, 255, 0.15)"}
            ],
            'threshold': {
                'line': {'color': "#ffffff", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=300,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

def create_radar_chart(plag, ai, auth):
    categories = ['Originality', 'Human Generation', 'Style Consistency']
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=[max(0, 100 - plag), max(0, 100 - ai), auth],
        theta=categories,
        fill='toself',
        fillcolor='rgba(0, 240, 255, 0.2)', # neon cyan transparent
        line=dict(color='#00f0ff', width=2), # neon cyan
        name='Document Profile'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor='#333333',
                linecolor='#333333',
                tickfont=dict(color='#a0a0a0')
            ),
            angularaxis=dict(
                gridcolor='#333333',
                linecolor='#333333',
                tickfont=dict(color='#00f0ff', size=13, family='Space Grotesk')
            ),
            bgcolor='#121212'
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        height=300,
        margin=dict(l=40, r=40, t=40, b=40)
    )
    return fig


# ─── App Layout ────────────────────────────────────────────────────────

st.markdown("<h1 style='font-size: 2.5rem; margin-bottom: 0;'>AVA TERMINAL // DASHBOARD</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.1rem; color: #a0a0a0; margin-top: 0; font-family: JetBrains Mono;'>[SYSTEM] Verify originality and maintain institutional integrity.</p>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Upload Area
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Drop your documents here (PDF, DOCX, TXT)", type=["txt", "pdf", "docx"])
st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file is not None:
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        start_btn = st.button("Analyze Document", type="primary", width="stretch")
        
    if start_btn:
        with st.container():
            st.markdown("<br>", unsafe_allow_html=True)
            status_container = st.empty()
            
            try:
                # 1. Upload to FastAPI
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/octet-stream")}
                response = httpx.post(f"{API_BASE}/upload", files=files, timeout=30.0)
                
                if response.status_code == 202:
                    job_id = response.json().get("job_id")
                    
                    # 2. Poll for status
                    is_done = False
                    
                    for i in range(100):
                        time.sleep(1)
                        
                        status_res = httpx.get(f"{API_BASE}/status/{job_id}", timeout=10.0)
                        if status_res.status_code == 200:
                            status_data = status_res.json()
                            status = status_data.get("status")
                            
                            if status in ["running", "pending"]:
                                # Animate loading text
                                dots = "." * ((i % 3) + 1)
                                phases = [
                                    "ESTABLISHING SECURE CONNECTION",
                                    "EXTRACTING NEURAL EMBEDDINGS",
                                    "COMPARING AGAINST KNOWN CORPUS",
                                    "ANALYZING STYLOMETRIC FINGERPRINTS",
                                    "DETECTING SYNTHETIC ARTIFACTS",
                                    "COMPILING FINAL INTELLIGENCE REPORT"
                                ]
                                phase = phases[min(i // 4, len(phases) - 1)]
                                
                                loading_html = f"""
                                <div class="glass-card" style="text-align: center; padding: 60px 20px; border-color: #00f0ff; box-shadow: 0 0 20px rgba(0, 240, 255, 0.1);">
                                    <span class="material-symbols-outlined" style="color: #00f0ff; font-size: 48px; display: block; margin-bottom: 20px;">radar</span>
                                    <h2 style="color: #00f0ff; font-family: 'Space Grotesk'; letter-spacing: 2px;">PROCESSING DOCUMENT</h2>
                                    <p style="color: #a0a0a0; font-family: 'JetBrains Mono'; font-size: 14px; margin-top: 10px;">> {phase}{dots}</p>
                                    <div style="width: 60%; margin: 30px auto 0; height: 2px; background: #333; position: relative; overflow: hidden;">
                                        <div style="width: {min((i/15)*100, 98)}%; height: 100%; background: #00f0ff; transition: width 1s linear;"></div>
                                    </div>
                                </div>
                                """
                                status_container.markdown(loading_html, unsafe_allow_html=True)
                                
                            elif status == "done":
                                status_container.empty()
                                is_done = True
                                break
                            elif status == "error":
                                status_container.empty()
                                st.error(f"Analysis failed: {status_data.get('error_msg')}")
                                break
                    
                    # 3. Get Report
                    if is_done:
                        report_res = httpx.get(f"{API_BASE}/report/{job_id}", timeout=10.0)
                        if report_res.status_code == 200:
                            report = report_res.json()
                            s = report["summary"]
                            
                            st.markdown("<hr style='border-color: #c5c5d3;'>", unsafe_allow_html=True)
                            st.markdown("<h2>Document Insights</h2>", unsafe_allow_html=True)
                            
                            # Top row: Main Gauge and Radar
                            r1c1, r1c2 = st.columns([1, 1])
                            
                            with r1c1:
                                st.markdown('<div class="glass-card" style="text-align:center; height:100%;">', unsafe_allow_html=True)
                                st.plotly_chart(create_gauge_chart(s['authenticity_score'], "AUTHENTICITY SCORE"), width="stretch")
                                
                                txt_color = "#006c49" if s['authenticity_score'] >= 80 else "#ef9900" if s['authenticity_score'] >= 50 else "#ba1a1a"
                                st.markdown(f"<p style='color:{txt_color}; font-family:Geist; font-weight:600; font-size:1.2rem;'>{s['interpretation']}</p>", unsafe_allow_html=True)
                                st.markdown('</div>', unsafe_allow_html=True)
                                
                            with r1c2:
                                st.markdown('<div class="glass-card" style="text-align:center; height:100%;">', unsafe_allow_html=True)
                                st.markdown("<h3 style='color:#00236f; font-size:1rem; letter-spacing:1px; margin-bottom:0;'>DIMENSIONAL ANALYSIS</h3>", unsafe_allow_html=True)
                                st.plotly_chart(create_radar_chart(s['plagiarism_score'], s['ai_probability'], s['authorship_consistency']), width="stretch")
                                st.markdown('</div>', unsafe_allow_html=True)
                            
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            # Second row: Individual Risk Cards
                            r2c1, r2c2, r2c3 = st.columns(3)
                            
                            def make_risk_card(score, label, is_risk=True):
                                if is_risk:
                                    col = "#ff003c" if score > 50 else "#b026ff" if score > 20 else "#00f0ff"
                                else:
                                    col = "#00f0ff" if score > 70 else "#b026ff" if score > 40 else "#ff003c"
                                    
                                return f"""
                                <div class="glass-card" style="text-align:center; border-top: 2px solid {col};">
                                    <div class="metric-value" style="color: {col};">{score:.1f}%</div>
                                    <div class="metric-label">{label}</div>
                                </div>
                                """

                            with r2c1:
                                st.markdown(make_risk_card(s['plagiarism_score'], "PLAGIARISM RISK", True), unsafe_allow_html=True)
                            with r2c2:
                                st.markdown(make_risk_card(s['ai_probability'], "AI PROBABILITY", True), unsafe_allow_html=True)
                            with r2c3:
                                st.markdown(make_risk_card(s['authorship_consistency'], "STYLE CONSISTENCY", False), unsafe_allow_html=True)
                                
                            
                            # Third row: Detailed Breakdown
                            st.markdown("<br><h2 style='text-transform: uppercase;'>Forensic Breakdown</h2>", unsafe_allow_html=True)
                            
                            tab1, tab2, tab3 = st.tabs(["[PLAGIARISM]", "[AI_TRACES]", "[AUTHORSHIP]"])
                            
                            def render_flagged(section_data, title, border_color):
                                st.markdown(f"<p style='color:#a0a0a0; font-size:1rem; font-family: JetBrains Mono;'>{section_data['explanation']}</p>", unsafe_allow_html=True)
                                flagged = section_data["flagged_sections"]
                                if not flagged:
                                    st.success(f"System Check: Clean. No anomalous {title} detected.")
                                else:
                                    for item in flagged:
                                        with st.container():
                                            st.markdown(f"""
                                            <div style="background:#0a0a0a; border: 1px solid #333333; border-left:4px solid {border_color}; padding:16px; border-radius:0px; margin-bottom:12px;">
                                                <p style="margin:0; font-family:'JetBrains Mono'; color:#e0e0e0; font-weight:600;">> {item.get('sentence') or item.get('text_snippet')}</p>
                                                <div style="margin-top:8px; font-size:0.9rem; color:#a0a0a0; font-family: 'JetBrains Mono';">
                                                    <span style="color:{border_color}">[REF]</span> {item.get('matched_reference', 'N/A')} <br>
                                                    <span style="color:{border_color}">[LOG]</span> {item.get('explanation')}
                                                </div>
                                            </div>
                                            """, unsafe_allow_html=True)

                            with tab1:
                                render_flagged(report["details"]["plagiarism"], "plagiarism", "#ff003c")
                            with tab2:
                                render_flagged(report["details"]["ai_detection"], "AI generation", "#00f0ff")
                            with tab3:
                                render_flagged(report["details"]["authorship"], "style deviations", "#b026ff")
                                
                else:
                    st.error(f"Failed to upload: {response.text}")
                    
            except httpx.ConnectError:
                st.error("Failed to connect to backend. Make sure FastAPI is running on port 8000.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
