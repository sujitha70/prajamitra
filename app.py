import io
import json
import os
import time
from pathlib import Path

import pdfplumber
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from gtts import gTTS
from PIL import Image

load_dotenv()

# ==========================================
# 1. PAGE CONFIG & CLEAN CIVIC UI STYLING
# ==========================================
st.set_page_config(
    page_title="Pathakam Mitra | పథకం మిత్ర",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .hero-banner {
        background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 100%);
        padding: 1.5rem 2rem;
        border-radius: 14px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(27, 94, 32, 0.15);
    }
    .hero-banner h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
        color: #FFFFFF;
    }
    .hero-banner p {
        margin: 0.4rem 0 0 0;
        font-size: 1.05rem;
        color: #E8F5E9;
    }
    .info-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 5px solid #2E7D32;
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }
    .badge-pill {
        display: inline-block;
        background-color: #E8F5E9;
        color: #1B5E20;
        padding: 0.25rem 0.7rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 0.4rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# 2. DATA & AI HELPER FUNCTIONS
# ==========================================
@st.cache_data
def load_schemes(path: str = "schemes.json") -> list[dict]:
    if not Path(path).exists():
        return []
    return json.loads(Path(path).read_text(encoding="utf-8"))


def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY") or st.session_state.get("user_api_key", "")
    if not api_key or api_key == "your_google_ai_studio_api_key_here":
        return None
    return genai.Client(api_key=api_key)


CANDIDATE_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.8-flash",
]


def generate_text(client, prompt: str, system_instruction: str) -> str:
    last_err = None
    for model_name in CANDIDATE_MODELS:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2,
                    ),
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                last_err = e
                time.sleep(1)
    st.error(f"⚠️ Google AI service is experiencing high demand. Please try again. ({last_err})")
    return "⚠️ సర్వీస్ ప్రస్తుతం బిజీగా ఉంది. దయచేసి కొద్దిసేపటి తర్వాత మళ్ళీ ప్రయత్నించండి. (AI Service is temporarily busy. Please try again.)"


def extract_text_from_image(client, image_bytes: bytes, mime_type: str) -> str:
    """Uses Gemini Vision to read printed/handwritten notices from photos."""
    prompt = (
        "Extract ALL text visible in this government notice or circular accurately. "
        "Preserve headings, dates, amounts, eligibility rules, and contact/website links. "
        "If the notice is in Telugu or Hindi, keep the original text and also provide a clear English translation below it."
    )
    last_err = None
    for model_name in CANDIDATE_MODELS:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        prompt,
                    ],
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                last_err = e
                time.sleep(1)
    st.error(f"⚠️ Failed to extract text from image: {last_err}")
    return ""


def transcribe_voice_query(client, audio_bytes: bytes) -> str:
    """Transcribes user's spoken Telugu/Hindi/English question using Gemini Audio."""
    last_err = None
    for model_name in CANDIDATE_MODELS:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
                        "Transcribe this spoken question accurately in the exact language spoken (Telugu, Hindi, or English). Return only the transcription.",
                    ],
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                last_err = e
                time.sleep(1)
    st.error(f"⚠️ Voice transcription error: {last_err}")
    return ""


def generate_tts_audio(text: str, lang_choice: str) -> bytes:
    """Generates spoken audio in Telugu, Hindi, or English."""
    lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en"}
    clean_text = (
        text.replace("*", "")
        .replace("#", "")
        .replace("`", "")
        .replace("|", " ")
        .strip()[:1800]
    )
    tts = gTTS(text=clean_text, lang=lang_map.get(lang_choice, "te"))
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()


# ==========================================
# 3. SIDEBAR NAVIGATION & SETTINGS
# ==========================================
schemes_data = load_schemes()

with st.sidebar:
    st.markdown("## 🏛️ Pathakam Mitra")
    st.caption("ప్రభుత్వ పథకాలు & నోటీసుల సులభ సహాయకుడు")
    st.divider()

    language = st.selectbox(
        "🌐 Preferred Language / భాష",
        ["Telugu", "Hindi", "English"],
        index=0,
    )

    input_mode = st.radio(
        "📥 Select Input Source",
        [
            "📚 Browse AP Schemes (90+)",
            "📄 Upload Notice PDF",
            "📸 Upload / Snap Notice Photo",
            "✍️ Paste Notice Text",
        ],
    )

    st.divider()
    if not get_gemini_client():
        st.text_input(
            "🔑 Gemini API Key",
            type="password",
            key="user_api_key",
            help="Get a free key from Google AI Studio.",
        )

    st.info(
        "**Tip for Citizens:** Select your preferred language above. Every explanation, eligibility result, and voice answer will adapt automatically."
    )


# ==========================================
# 4. HERO BANNER
# ==========================================
st.markdown(
    """
    <div class="hero-banner">
        <h1>🏛️ Pathakam Mitra (పథకం మిత్ర)</h1>
        <p>Simple, trustworthy explanations of government schemes & notices in Telugu, Hindi, and English — with instant eligibility checks and voice support.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

client = get_gemini_client()

# ==========================================
# 5. INPUT SELECTION & EXTRACTION PANEL
# ==========================================
context_title = ""
context_text = ""
selected_scheme_obj = None

with st.container(border=True):
    if input_mode == "📚 Browse AP Schemes (90+)":
        if not schemes_data:
            st.error("`schemes.json` not found. Run `python parse_schemes.py` in your project folder first.")
            st.stop()

        categories = ["All Categories"] + sorted(
            list({s.get("category", "General Welfare") for s in schemes_data})
        )
        col_cat, col_sch = st.columns([1, 2])

        with col_cat:
            chosen_cat = st.selectbox("Filter by Category", categories)

        filtered_schemes = (
            schemes_data
            if chosen_cat == "All Categories"
            else [s for s in schemes_data if s.get("category") == chosen_cat]
        )

        scheme_labels = [f"{s['scheme_number']}. {s['name']}" for s in filtered_schemes]
        with col_sch:
            chosen_label = st.selectbox("Choose a Government Scheme", scheme_labels)

        selected_scheme_obj = filtered_schemes[scheme_labels.index(chosen_label)]
        context_title = selected_scheme_obj["name"]
        context_text = json.dumps(selected_scheme_obj, indent=2, ensure_ascii=False)

        st.markdown(
            f"""
            <div class="info-card">
                <span class="badge-pill">{selected_scheme_obj.get('state_or_central', 'State')}</span>
                <span class="badge-pill">{selected_scheme_obj.get('category', 'Welfare')}</span>
                <h4 style="margin: 0.6rem 0 0.3rem 0;">{selected_scheme_obj['name']}</h4>
                <p style="margin:0; color:#475569;"><strong>Department:</strong> {selected_scheme_obj['department']}</p>
                <p style="margin:0.3rem 0 0 0; color:#1B5E20;"><strong>Key Benefit:</strong> {selected_scheme_obj['benefits']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif input_mode == "📄 Upload Notice PDF":
        pdf_file = st.file_uploader("Upload a Government Notice, GO, or Scheme Brochure (PDF)", type=["pdf"])
        if pdf_file:
            with pdfplumber.open(pdf_file) as pdf:
                extracted = "\n".join(page.extract_text() or "" for page in pdf.pages).strip()
            if extracted:
                context_title = pdf_file.name
                context_text = extracted
                st.success(f"Loaded `{pdf_file.name}` ({len(extracted)} characters extracted).")
                with st.expander("View Extracted PDF Text"):
                    st.text(extracted[:3000])
            else:
                st.warning("No selectable text found in this PDF. Try taking a screenshot/photo and using the **Upload / Snap Notice Photo** option.")

    elif input_mode == "📸 Upload / Snap Notice Photo":
        st.caption("Upload a clear photo of a village notice board, pamphlet, or letter.")
        img_file = st.file_uploader("Upload Notice Image (JPG / PNG / WEBP)", type=["jpg", "jpeg", "png", "webp"])
        if img_file:
            col_img, col_ocr = st.columns([1, 1.5])
            with col_img:
                st.image(Image.open(img_file), caption="Uploaded Notice", use_container_width=True)
            with col_ocr:
                if not client:
                    st.warning("Add your `GEMINI_API_KEY` in the sidebar to read text from images.")
                else:
                    if st.button("🔍 Extract Text from Photo (OCR)", type="primary"):
                        with st.spinner("Reading notice text with AI Vision..."):
                            ocr_text = extract_text_from_image(
                                client, img_file.getvalue(), img_file.type or "image/jpeg"
                            )
                            st.session_state["ocr_extracted_text"] = ocr_text
                            st.session_state["ocr_file_name"] = img_file.name

                    if st.session_state.get("ocr_file_name") == img_file.name and st.session_state.get("ocr_extracted_text"):
                        context_title = img_file.name
                        context_text = st.session_state["ocr_extracted_text"]
                        st.success("Text extracted successfully!")
                        with st.expander("View Extracted Notice Text", expanded=True):
                            st.markdown(context_text)

    elif input_mode == "✍️ Paste Notice Text":
        pasted_text = st.text_area(
            "Paste the English or Telugu notice text below:",
            height=160,
            placeholder="Paste government circular, eligibility criteria, or notice text here...",
        )
        if pasted_text.strip():
            context_title = "Pasted Notice"
            context_text = pasted_text.strip()

if not context_text:
    st.info("👆 Choose a scheme or upload/paste a notice above to unlock explanations, eligibility checks, checklists, and voice Q&A.")
    st.stop()

if not client:
    st.warning("Please provide your `GEMINI_API_KEY` in the sidebar (or `.env`) to run the AI assistant.")
    st.stop()

# Reset cached outputs when user switches scheme/document
if st.session_state.get("active_context") != context_title:
    st.session_state["active_context"] = context_title
    st.session_state["summary_text"] = ""
    st.session_state["summary_lang"] = ""
    st.session_state["audio_bytes"] = None
    st.session_state["chat_history"] = []


# ==========================================
# 6. FEATURE TABS
# ==========================================
tab_explain, tab_elig, tab_docs, tab_chat = st.tabs(
    [
        "📖 Simple Explanation & Audio",
        "✅ Eligibility Checker",
        "📋 Documents Checklist",
        "💬 Voice & Text Q&A",
    ]
)

# ------------------------------------------
# TAB 1: PLAIN-LANGUAGE EXPLANATION & VOICE
# ------------------------------------------
with tab_explain:
    col_btn, col_info = st.columns([1.3, 2.7])
    with col_btn:
        explain_clicked = st.button(
            f"✨ Explain Simply in {language}",
            type="primary",
            use_container_width=True,
        )
    with col_info:
        st.caption(f"Translates complex rules into clear, respectful {language} for citizens & elders.")

    if explain_clicked or (
        st.session_state.get("summary_text") and st.session_state.get("summary_lang") != language
    ):
        with st.spinner(f"Preparing easy-to-understand explanation in {language}..."):
            sys_prompt = (
                f"You are Pathakam Mitra, a warm, trustworthy civic helper. "
                f"Explain the provided scheme or government notice in simple, everyday {language} "
                f"so rural citizens and senior citizens can understand without confusion. "
                f"Stick strictly to the facts provided."
            )
            prompt = f"""
Explain the following scheme or notice in simple {language} using these clear headings:

### 1. What is this scheme / notice?
### 2. Who is eligible?
### 3. How much benefit / support do you get?
### 4. What documents are needed?
### 5. How to apply (Step-by-Step)
### 6. Important Dates & Official Link

SOURCE CONTENT:
{context_text}
"""
            st.session_state["summary_text"] = generate_text(client, prompt, sys_prompt)
            st.session_state["summary_lang"] = language
            st.session_state["audio_bytes"] = None

    if st.session_state.get("summary_text"):
        with st.container(border=True):
            st.markdown(st.session_state["summary_text"])

        c_aud, c_dl = st.columns(2)
        with c_aud:
            if st.button(f"🔊 Read Aloud in {language}", use_container_width=True):
                with st.spinner("Generating voice audio..."):
                    st.session_state["audio_bytes"] = generate_tts_audio(
                        st.session_state["summary_text"], language
                    )
            if st.session_state.get("audio_bytes"):
                st.audio(st.session_state["audio_bytes"], format="audio/mp3")

        with c_dl:
            st.download_button(
                label="📥 Download Explanation (.txt)",
                data=st.session_state["summary_text"],
                file_name=f"Pathakam_Mitra_{context_title[:25].replace(' ', '_')}_{language}.txt",
                mime="text/plain",
                use_container_width=True,
            )


# ------------------------------------------
# TAB 2: ELIGIBILITY CHECKER
# ------------------------------------------
with tab_elig:
    st.subheader("Check Whether You Qualify")
    st.caption("Fill in basic details below. Pathakam Mitra will verify each rule from the scheme/notice.")

    with st.form("eligibility_checker_form"):
        r1c1, r1c2, r1c3 = st.columns(3)
        age = r1c1.number_input("Age (Years)", min_value=0, max_value=120, value=32)
        gender = r1c2.selectbox("Gender", ["Female", "Male", "Transgender"])
        social_cat = r1c3.selectbox("Category", ["OC / General", "BC", "SC", "ST", "Minority", "EBC / Kapu"])

        r2c1, r2c2, r2c3 = st.columns(3)
        annual_income = r2c1.number_input("Annual Family Income (₹)", min_value=0, step=10000, value=100000)
        occupation = r2c2.text_input("Occupation", value="Farmer", placeholder="e.g. Farmer, Student, Weaver, Auto Driver")
        land_acres = r2c3.number_input("Total Agricultural Land (Acres)", min_value=0.0, step=0.5, value=1.0)

        r3c1, r3c2 = st.columns(2)
        has_rice_card = r3c1.checkbox("Has AP Rice Card (White Ration Card)", value=True)
        has_govt_job_or_tax = r3c2.checkbox("Family has Govt Employee / Income Tax Payer", value=False)

        special_notes = st.text_input(
            "Any other details (optional):",
            placeholder="e.g., Widow, 45% disability, Class 10 student, Pregnant woman, Street vendor...",
        )

        check_btn = st.form_submit_button("✅ Check My Eligibility", type="primary")

    if check_btn:
        with st.spinner("Evaluating eligibility rules..."):
            sys_prompt = (
                f"You are an eligibility verification assistant. Compare the citizen's profile strictly "
                f"against the eligibility criteria in the provided scheme/notice. Write your response in simple {language}."
            )
            eval_prompt = f"""
Evaluate whether this citizen qualifies based ONLY on the provided scheme/notice.

Format your output clearly in {language}:
1. **Verdict:** Start with **✅ Likely Eligible**, **❌ Not Eligible**, or **⚠️ Needs Verification (Additional Info Needed)**.
2. **Rule-by-Rule Check:** Bullet points comparing the citizen's details against each condition in the scheme.
3. **Next Step:** What they should do next if eligible.

CITIZEN PROFILE:
- State: Andhra Pradesh
- Age: {age}
- Gender: {gender}
- Social Category: {social_cat}
- Annual Family Income: ₹{annual_income} (Approx ₹{annual_income // 12}/month)
- Occupation: {occupation}
- Landholding: {land_acres} acres
- AP Rice Card Holder: {"Yes" if has_rice_card else "No"}
- Govt Employee / Taxpayer in Family: {"Yes" if has_govt_job_or_tax else "No"}
- Additional Notes: {special_notes or "None"}

SCHEME / NOTICE DATA:
{context_text}
"""
            verdict_md = generate_text(client, eval_prompt, sys_prompt)
            with st.container(border=True):
                st.markdown(verdict_md)


# ------------------------------------------
# TAB 3: INTERACTIVE DOCUMENTS CHECKLIST
# ------------------------------------------
with tab_docs:
    st.subheader("Required Documents Checklist")
    st.caption("Tick the documents you already have ready before visiting the Grama/Ward Sachivalayam or applying online.")

    if selected_scheme_obj and selected_scheme_obj.get("documents_required"):
        docs_list = selected_scheme_obj["documents_required"]
    else:
        if st.button("📋 Extract Document List from Notice"):
            with st.spinner("Extracting required documents..."):
                doc_prompt = (
                    "List ONLY the required documents mentioned in the text below, one per line, without bullets or numbers. "
                    "If none are mentioned, write 'No specific documents mentioned in notice.'\n\n"
                    f"{context_text}"
                )
                raw_docs = generate_text(
                    client, doc_prompt, "Extract exact required documents only."
                )
                st.session_state["custom_docs_list"] = [
                    d.strip("-• ") for d in raw_docs.splitlines() if d.strip()
                ]
        docs_list = st.session_state.get("custom_docs_list", [])

    if docs_list:
        checked_status = []
        with st.container(border=True):
            for idx, doc in enumerate(docs_list):
                is_ready = st.checkbox(doc, key=f"doc_chk_{context_title}_{idx}")
                checked_status.append((doc, is_ready))

        ready_count = sum(1 for _, status in checked_status if status)
        st.progress(ready_count / len(checked_status), text=f"{ready_count} of {len(checked_status)} documents ready")

        checklist_export = f"PATHAKAM MITRA - DOCUMENT CHECKLIST\nScheme/Notice: {context_title}\n\n"
        for doc, status in checked_status:
            mark = "[READY]" if status else "[NEEDED]"
            checklist_export += f"{mark} {doc}\n"

        if selected_scheme_obj:
            checklist_export += f"\nHow to Apply:\n{selected_scheme_obj['how_to_apply']}\n"
            checklist_export += f"\nOfficial Portal: {selected_scheme_obj['official_website']}\n"

        st.download_button(
            label="📥 Download My Document Checklist (.txt)",
            data=checklist_export,
            file_name=f"Checklist_{context_title[:25].replace(' ', '_')}.txt",
            mime="text/plain",
        )
    else:
        st.info("Click the button above to extract a document checklist from your uploaded notice.")


# ------------------------------------------
# TAB 4: STRICTLY GROUNDED Q&A (TEXT + VOICE)
# ------------------------------------------
with tab_chat:
    st.subheader(f"Ask Questions About: {context_title}")
    st.caption(
        "🔒 Strict Grounding Mode: Pathakam Mitra answers ONLY using facts from the loaded scheme or notice."
    )

    for i, msg in enumerate(st.session_state.get("chat_history", [])):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                if st.button("🔊 Listen", key=f"tts_chat_{i}"):
                    aud = generate_tts_audio(msg["content"], language)
                    st.audio(aud, format="audio/mp3")

    with st.expander("🎙️ Ask by Voice (Speak in Telugu, Hindi, or English)", expanded=False):
        recorded_audio = st.audio_input("Record your question")
        if recorded_audio and st.button("📨 Send Voice Question", type="primary"):
            with st.spinner("Transcribing your voice..."):
                transcribed_q = transcribe_voice_query(client, recorded_audio.getvalue())
                st.session_state["pending_voice_q"] = transcribed_q

    typed_q = st.chat_input(f"Type your question in {language}, Telugu, or English...")
    active_question = st.session_state.pop("pending_voice_q", None) or typed_q

    if active_question:
        st.session_state["chat_history"].append({"role": "user", "content": active_question})
        with st.chat_message("user"):
            st.markdown(active_question)

        strict_sys_prompt = (
            f"You are Pathakam Mitra. Answer the user's question in simple {language} using ONLY the information "
            f"explicitly present in the PROVIDED SOURCE DOCUMENT below. "
            f"Do NOT invent rules, dates, or amounts. If the answer is not present in the document, "
            f"politely state in {language} that this detail is not mentioned in the provided notice/scheme."
        )
        qa_prompt = f"PROVIDED SOURCE DOCUMENT:\n{context_text}\n\nCITIZEN QUESTION:\n{active_question}"

        with st.chat_message("assistant"):
            with st.spinner("Checking official details..."):
                answer = generate_text(client, qa_prompt, strict_sys_prompt)
                st.markdown(answer)

        st.session_state["chat_history"].append({"role": "assistant", "content": answer})
        st.rerun()
