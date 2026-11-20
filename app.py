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
# 2. MULTILINGUAL UI TRANSLATIONS (i18n)
# ==========================================
UI_TRANSLATIONS = {
    "Telugu": {
        "app_name": "🏛️ పథకం మిత్ర",
        "app_caption": "ప్రభుత్వ సంక్షేమ పథకాలు & అధికారిక నోటీసుల సులభ సహాయకుడు",
        "hero_title": "🏛️ పథకం మిత్ర (Pathakam Mitra)",
        "hero_desc": "ప్రభుత్వ సంక్షేమ పథకాలు మరియు జీవోలు/నోటీసులను సాధారణ ప్రజలకు అర్థమయ్యేలా సులభ శైలిలో వివరించడం, తక్షణ అర్హత పరిశీలన మరియు వాయిస్ సహాయం.",
        "lang_label": "🌐 భాషను ఎంచుకోండి / Preferred Language",
        "input_mode_label": "📥 సమాచార మార్గాన్ని ఎంచుకోండి",
        "mode_browse": "📚 ప్రభుత్వ సంక్షేమ పథకాలను చూడండి (190+)",
        "mode_pdf": "📄 నోటీసు / జీవో PDF అప్‌లోడ్ చేయండి",
        "mode_photo": "📸 నోటీసు ఫోటో అప్‌లోడ్ చేయండి (AI విజన్)",
        "mode_paste": "✍️ నోటీసు పాఠాన్ని పేస్ట్ చేయండి",
        "api_key_label": "🔑 జెమినీ API కీ",
        "api_key_help": "Google AI Studio నుండి ఉచిత కీని పొందండి.",
        "sidebar_tip": "**పౌరులకు సూచన:** పైన మీ భాషను ఎంచుకోండి. వివరణలు, అర్హత పరిశీలన, పత్రాల జాబితా మరియు వాయిస్ సమాధానాలు అన్నీ పూర్తిగా మీ భాషలోనే లభిస్తాయి.",
        "filter_cat_label": "వర్గం ప్రకారం ఫిల్టర్ చేయండి",
        "all_categories": "అన్ని వర్గాలు (All Categories)",
        "choose_scheme_label": "ప్రభుత్వ సంక్షేమ పథకాన్ని ఎంచుకోండి",
        "card_dept": "శాఖ",
        "card_benefit": "ప్రధాన ప్రయోజనం",
        "pdf_upload_label": "ప్రభుత్వ నోటీసు, జీవో లేదా పథకం బ్రోచర్ (PDF) అప్‌లోడ్ చేయండి",
        "pdf_loaded_msg": "విజయవంతంగా లోడ్ చేయబడింది",
        "pdf_chars": "అక్షరాలు సేకరించబడ్డాయి",
        "pdf_view_text": "సేకరించిన PDF పాఠాన్ని చూడండి",
        "pdf_no_text": "ఈ PDF లో టెక్స్ట్ కనుగొనబడలేదు. దయచేసి ఫోటో అప్‌లోడ్ ఆప్షన్ ఉపయోగించండి.",
        "photo_caption": "గ్రామ సచివాలయ నోటీసు బోర్డు, కరపత్రం లేదా ప్రభుత్వ లేఖ యొక్క స్పష్టమైన ఫోటోను అప్‌లోడ్ చేయండి.",
        "photo_upload_label": "నోటీసు చిత్రాన్ని అప్‌లోడ్ చేయండి (JPG / PNG / WEBP)",
        "photo_preview": "అప్‌లోడ్ చేసిన నోటీసు చిత్రం",
        "photo_ocr_btn": "🔍 ఫోటో నుండి టెక్స్ట్ సేకరించండి (AI విజన్ OCR)",
        "photo_ocr_spinner": "AI విజన్ ద్వారా నోటీసును చదువుతోంది...",
        "photo_ocr_success": "టెక్స్ట్ విజయవంతంగా సేకరించబడింది!",
        "photo_ocr_view": "సేకరించిన నోటీసు పాఠాన్ని చూడండి",
        "paste_label": "నోటీసు లేదా సర్క్యులర్ పాఠాన్ని క్రింద పేస్ట్ చేయండి:",
        "paste_placeholder": "ప్రభుత్వ సర్క్యులర్, అర్హత నిబంధనలు లేదా జీవో వివరాలను ఇక్కడ పేస్ట్ చేయండి...",
        "pasted_title": "పేస్ట్ చేసిన నోటీసు",
        "prompt_select": "👆 వివరణలు, అర్హత పరిశీలన, చెక్‌లిస్ట్‌లు మరియు వాయిస్ Q&A అన్‌లాక్ చేయడానికి పైన ఒక పథకాన్ని ఎంచుకోండి లేదా నోటీసును అప్‌లోడ్ చేయండి.",
        "prompt_api_key": "AI అసిస్టెంట్‌ని ఉపయోగించడానికి సైడ్‌బార్‌లో లేదా .env లో మీ GEMINI_API_KEY ని నమోదు చేయండి.",
        "tab_explain": "📖 సులభ వివరణ & ఆడియో",
        "tab_elig": "✅ అర్హత పరిశీలన",
        "tab_docs": "📋 అవసరమైన పత్రాల చెక్‌లిస్ట్",
        "tab_chat": "💬 వాయిస్ & టెక్స్ట్ ప్రశ్నలు (Q&A)",
        "explain_btn": "✨ తెలుగులో సులభంగా వివరించండి",
        "explain_caption": "గ్రామీణ పౌరులు మరియు పెద్దలకు సులభంగా అర్థమయ్యే గౌరవప్రదమైన తెలుగులో వివరిస్తుంది.",
        "explain_spinner": "తెలుగులో స్పష్టమైన వివరణను సిద్ధం చేస్తోంది...",
        "read_aloud_btn": "🔊 తెలుగులో వినండి (వాయిస్)",
        "audio_spinner": "వాయిస్ ఆడియోను రూపొందిస్తోంది...",
        "download_explain_btn": "📥 వివరణను డౌన్‌లోడ్ చేయండి (.txt)",
        "elig_header": "మీకు అర్హత ఉందో లేదో సరిచూసుకోండి",
        "elig_caption": "మీ ప్రాథమిక వివరాలను నమోదు చేయండి. పథకం లేదా నోటీసు నిబంధనల ప్రకారం పరిశీలిస్తుంది.",
        "elig_age": "వయస్సు (సంవత్సరాలు)",
        "elig_gender": "లింగం",
        "elig_genders": ["స్త్రీ (Female)", "పురుషుడు (Male)", "ట్రాన్స్‌జెండర్ (Transgender)"],
        "elig_cat": "సామాజిక వర్గం",
        "elig_cats": ["OC / జనరల్", "BC", "SC", "ST", "మైనారిటీ", "EBC / కాపు"],
        "elig_income": "వార్షిక కుటుంబ ఆదాయం (₹)",
        "elig_occupation": "వృత్తి",
        "elig_occ_placeholder": "ఉదా: రైతు, విద్యార్థి, చేనేత కార్మికుడు, ఆటో డ్రైవర్, కూలీ",
        "elig_land": "మొత్తం వ్యవసాయ భూమి (ఎకరాలు)",
        "elig_rice_card": "AP బియ్యం కార్డు (తెల్ల రేషన్ కార్డు) ఉందా?",
        "elig_govt_job": "కుటుంబంలో ప్రభుత్వ ఉద్యోగి లేదా ఆదాయపు పన్ను చెల్లింపుదారు ఉన్నారా?",
        "elig_notes": "ఇతర వివరాలు (ఐచ్ఛికం):",
        "elig_notes_placeholder": "ఉదా: వితంతువు, 45% దివ్యాంగులు, గర్భిణీ స్త్రీ, ఒంటరి మహిళ, వీధి వ్యాపారి...",
        "elig_btn": "✅ నా అర్హతను పరిశీలించండి",
        "elig_spinner": "అర్హత నిబంధనలను పరిశీలిస్తోంది...",
        "docs_header": "అవసరమైన పత్రాల చెక్‌లిస్ట్",
        "docs_caption": "గ్రామ/వార్డు సచివాలయానికి వెళ్లే ముందు లేదా దరఖాస్తు చేసే ముందు మీ వద్ద ఉన్న పత్రాలను టిక్ చేసుకోండి.",
        "docs_extract_btn": "📋 నోటీసు నుండి అవసరమైన పత్రాల జాబితాను సేకరించండి",
        "docs_extract_spinner": "అవసరమైన పత్రాలను సేకరిస్తోంది...",
        "docs_progress_text": "{ready} / {total} పత్రాలు మీ వద్ద సిద్ధంగా ఉన్నాయి",
        "docs_ready_tag": "[సిద్ధంగా ఉంది]",
        "docs_needed_tag": "[కావాలి]",
        "docs_how_apply": "ఎలా దరఖాస్తు చేసుకోవాలి:",
        "docs_official_portal": "అధికారిక పోర్టల్:",
        "docs_download_btn": "📥 నా పత్రాల చెక్‌లిస్ట్‌ను డౌన్‌లోడ్ చేసుకోండి (.txt)",
        "docs_empty_info": "పై బటన్‌ను క్లిక్ చేసి మీ అప్‌లోడ్ చేసిన నోటీసు నుండి పత్రాల జాబితాను పొందండి.",
        "chat_header": "గురించి ప్రశ్నలు అడగండి:",
        "chat_caption": "🔒 ఖచ్చితమైన అధికారిక సమాధానం: పథకం లేదా నోటీసులోని అధికారిక వివరాల ఆధారంగా మాత్రమే సమాధానం ఇవ్వబడుతుంది.",
        "chat_listen_btn": "🔊 వినండి",
        "chat_voice_expander": "🎙️ వాయిస్ ద్వారా అడగండి (తెలుగులో మాట్లాడండి)",
        "chat_voice_record": "మీ ప్రశ్నను రికార్డ్ చేయండి",
        "chat_voice_btn": "📨 వాయిస్ ప్రశ్న పంపండి",
        "chat_transcribing": "మీ వాయిస్‌ని టెక్స్ట్‌గా మారుస్తోంది...",
        "chat_input_placeholder": "మీ ప్రశ్నను ఇక్కడ తెలుగులో టైప్ చేయండి...",
        "chat_checking": "అధికారిక వివరాలను తనిఖీ చేస్తోంది...",
    },
    "Hindi": {
        "app_name": "🏛️ पथकम मित्र",
        "app_caption": "सरकारी कल्याणकारी योजनाओं और सूचनाओं का सरल सहायक",
        "hero_title": "🏛️ पथकम मित्र (Pathakam Mitra)",
        "hero_desc": "सरकारी योजनाओं और आधिकारिक सूचनाओं की सरल भाषा में व्याख्या, त्वरित पात्रता जांच और ऑडियो सहायता।",
        "lang_label": "🌐 पसंदीदा भाषा / Preferred Language",
        "input_mode_label": "📥 जानकारी स्रोत चुनें",
        "mode_browse": "📚 सरकारी कल्याणकारी योजनाएं देखें (190+)",
        "mode_pdf": "📄 नोटिस / शासनादेश PDF अपलोड करें",
        "mode_photo": "📸 नोटिस फोटो अपलोड करें (AI विजन)",
        "mode_paste": "✍️ नोटिस टेक्स्ट पेस्ट करें",
        "api_key_label": "🔑 जेमिनी API कुंजी",
        "api_key_help": "Google AI Studio से निःशुल्क कुंजी प्राप्त करें।",
        "sidebar_tip": "**नागरिकों के लिए सुझाव:** ऊपर अपनी भाषा चुनें। सभी व्याख्याएं, पात्रता परिणाम और ध्वनि उत्तर स्वचालित रूप से अनुकूलित होंगे।",
        "filter_cat_label": "श्रेणी के अनुसार फ़िल्टर करें",
        "all_categories": "सभी श्रेणियां (All Categories)",
        "choose_scheme_label": "सरकारी कल्याणकारी योजना चुनें",
        "card_dept": "विभाग",
        "card_benefit": "प्रमुख लाभ",
        "pdf_upload_label": "सरकारी नोटिस, शासनादेश या योजना विवरणिका (PDF) अपलोड करें",
        "pdf_loaded_msg": "सफलतापूर्वक लोड किया गया",
        "pdf_chars": "अक्षर निकाले गए",
        "pdf_view_text": "निकाले गए PDF टेक्स्ट को देखें",
        "pdf_no_text": "इस PDF में कोई टेक्स्ट नहीं मिला। कृपया फोटो अपलोड का उपयोग करें।",
        "photo_caption": "ग्राम सचिवालय नोटिस बोर्ड, पैम्फलेट या पत्र की स्पष्ट तस्वीर अपलोड करें।",
        "photo_upload_label": "नोटिस छवि अपलोड करें (JPG / PNG / WEBP)",
        "photo_preview": "अपलोड की गई नोटिस छवि",
        "photo_ocr_btn": "🔍 फोटो से टेक्स्ट निकालें (AI विज़न OCR)",
        "photo_ocr_spinner": "AI विज़न से नोटिस पढ़ा जा रहा है...",
        "photo_ocr_success": "टेक्स्ट सफलतापूर्वक निकाला गया!",
        "photo_ocr_view": "निकाला गया नोटिस टेक्स्ट देखें",
        "paste_label": "नोटिस या परिपत्र टेक्स्ट नीचे पेस्ट करें:",
        "paste_placeholder": "सरकारी परिपत्र, पात्रता नियम या नोटिस टेक्स्ट यहाँ पेस्ट करें...",
        "pasted_title": "पेस्ट किया गया नोटिस",
        "prompt_select": "👆 व्याख्या, पात्रता जांच, चेकलिस्ट और वॉयस Q&A अनलॉक करने के लिए ऊपर योजना चुनें या नोटिस अपलोड करें।",
        "prompt_api_key": "AI सहायक का उपयोग करने के लिए साइडबार या .env में अपनी GEMINI_API_KEY दर्ज करें।",
        "tab_explain": "📖 सरल व्याख्या और ऑडियो",
        "tab_elig": "✅ पात्रता जांच",
        "tab_docs": "📋 आवश्यक दस्तावेज़ चेकलिस्ट",
        "tab_chat": "💬 ध्वनि और टेक्स्ट प्रश्नोत्तर (Q&A)",
        "explain_btn": "✨ हिंदी में सरलता से समझाएं",
        "explain_caption": "ग्रामीण नागरिकों और बुजुर्गों के लिए सरल हिंदी में नियमों को समझाता है।",
        "explain_spinner": "हिंदी में सरल व्याख्या तैयार की जा रही है...",
        "read_aloud_btn": "🔊 हिंदी में सुनें (ऑडियो)",
        "audio_spinner": "ऑडियो तैयार किया जा रहा है...",
        "download_explain_btn": "📥 व्याख्या डाउनलोड करें (.txt)",
        "elig_header": "जांचें कि क्या आप पात्र हैं",
        "elig_caption": "नीचे अपना विवरण भरें। पथकम मित्र योजना के प्रत्येक नियम को सत्यापित करेगा।",
        "elig_age": "आयु (वर्ष)",
        "elig_gender": "लिंग",
        "elig_genders": ["महिला (Female)", "पुरुष (Male)", "ट्रांसजेंडर (Transgender)"],
        "elig_cat": "सामाजिक श्रेणी",
        "elig_cats": ["OC / सामान्य", "BC", "SC", "ST", "अल्पसंख्यक", "EBC / कापू"],
        "elig_income": "वार्षिक पारिवारिक आय (₹)",
        "elig_occupation": "व्यवसाय",
        "elig_occ_placeholder": "उदा: किसान, छात्र, बुनकर, ऑटो चालक, मजदूर",
        "elig_land": "कुल कृषि भूमि (एकड़)",
        "elig_rice_card": "क्या आपके पास AP राइस कार्ड (सफेद राशन कार्ड) है?",
        "elig_govt_job": "क्या परिवार में कोई सरकारी कर्मचारी या आयकर दाता है?",
        "elig_notes": "अन्य विवरण (वैकल्पिक):",
        "elig_notes_placeholder": "उदा: विधवा, 45% दिव्यांगता, गर्भवती महिला, स्ट्रीट वेंडर...",
        "elig_btn": "✅ मेरी पात्रता जांचें",
        "elig_spinner": "पात्रता नियमों का मूल्यांकन किया जा रहा है...",
        "docs_header": "आवश्यक दस्तावेज़ चेकलिस्ट",
        "docs_caption": "ग्राम/वार्ड सचिवालय जाने या ऑनलाइन आवेदन करने से पहले अपने पास उपलब्ध दस्तावेज़ों को टिक करें।",
        "docs_extract_btn": "📋 नोटिस से दस्तावेज़ सूची निकालें",
        "docs_extract_spinner": "आवश्यक दस्तावेज़ निकाले जा रहे हैं...",
        "docs_progress_text": "{ready} / {total} दस्तावेज़ आपके पास तैयार हैं",
        "docs_ready_tag": "[तैयार है]",
        "docs_needed_tag": "[आवश्यक]",
        "docs_how_apply": "आवेदन कैसे करें:",
        "docs_official_portal": "आधिकारिक पोर्टल:",
        "docs_download_btn": "📥 मेरी चेकलिस्ट डाउनलोड करें (.txt)",
        "docs_empty_info": "अपने अपलोड किए गए नोटिस से दस्तावेज़ सूची निकालने के लिए ऊपर दिए गए बटन पर क्लिक करें।",
        "chat_header": "के बारे में प्रश्न पूछें:",
        "chat_caption": "🔒 सख्त आधिकारिक जवाब: केवल दिए गए दस्तावेज़ के आधिकारिक तथ्यों के आधार पर उत्तर दिया जाता है।",
        "chat_listen_btn": "🔊 सुनें",
        "chat_voice_expander": "🎙️ बोलकर पूछें (हिंदी में बोलें)",
        "chat_voice_record": "अपना प्रश्न रिकॉर्ड करें",
        "chat_voice_btn": "📨 ध्वनि प्रश्न भेजें",
        "chat_transcribing": "आपकी आवाज़ को टेक्स्ट में बदला जा रहा है...",
        "chat_input_placeholder": "अपना प्रश्न यहाँ हिंदी में टाइप करें...",
        "chat_checking": "आधिकारिक विवरणों की जांच की जा रही है...",
    },
    "English": {
        "app_name": "🏛️ Pathakam Mitra",
        "app_caption": "Citizen Assistant for Government Welfare Schemes & Circulars",
        "hero_title": "🏛️ Pathakam Mitra (పథకం మిత్ర)",
        "hero_desc": "Simple, trustworthy explanations of government schemes & official notices with instant eligibility checks, checklists, and voice support.",
        "lang_label": "🌐 Preferred Language / భాష",
        "input_mode_label": "📥 Select Input Source",
        "mode_browse": "📚 Browse Welfare Schemes (190+)",
        "mode_pdf": "📄 Upload Notice / GO PDF",
        "mode_photo": "📸 Upload / Snap Notice Photo",
        "mode_paste": "✍️ Paste Notice Text",
        "api_key_label": "🔑 Gemini API Key",
        "api_key_help": "Get a free key from Google AI Studio.",
        "sidebar_tip": "**Tip for Citizens:** Select your preferred language above. Every explanation, eligibility result, and voice answer will adapt automatically.",
        "filter_cat_label": "Filter by Category",
        "all_categories": "All Categories",
        "choose_scheme_label": "Choose a Government Scheme",
        "card_dept": "Department",
        "card_benefit": "Key Benefit",
        "pdf_upload_label": "Upload a Government Notice, GO, or Scheme Brochure (PDF)",
        "pdf_loaded_msg": "Successfully loaded",
        "pdf_chars": "characters extracted",
        "pdf_view_text": "View Extracted PDF Text",
        "pdf_no_text": "No selectable text found in this PDF. Try using the photo option.",
        "photo_caption": "Upload a clear photo of a village notice board, pamphlet, or letter.",
        "photo_upload_label": "Upload Notice Image (JPG / PNG / WEBP)",
        "photo_preview": "Uploaded Notice",
        "photo_ocr_btn": "🔍 Extract Text from Photo (AI Vision OCR)",
        "photo_ocr_spinner": "Reading notice text with AI Vision...",
        "photo_ocr_success": "Text extracted successfully!",
        "photo_ocr_view": "View Extracted Notice Text",
        "paste_label": "Paste the notice or circular text below:",
        "paste_placeholder": "Paste government circular, eligibility criteria, or notice text here...",
        "pasted_title": "Pasted Notice",
        "prompt_select": "👆 Choose a scheme or upload/paste a notice above to unlock explanations, eligibility checks, checklists, and voice Q&A.",
        "prompt_api_key": "Please provide your GEMINI_API_KEY in the sidebar (or .env) to run the AI assistant.",
        "tab_explain": "📖 Simple Explanation & Audio",
        "tab_elig": "✅ Eligibility Checker",
        "tab_docs": "📋 Documents Checklist",
        "tab_chat": "💬 Voice & Text Q&A",
        "explain_btn": "✨ Explain Simply in English",
        "explain_caption": "Translates complex rules into clear, respectful language for citizens & elders.",
        "explain_spinner": "Preparing easy-to-understand explanation...",
        "read_aloud_btn": "🔊 Read Aloud (Voice)",
        "audio_spinner": "Generating voice audio...",
        "download_explain_btn": "📥 Download Explanation (.txt)",
        "elig_header": "Check Whether You Qualify",
        "elig_caption": "Fill in basic details below. Pathakam Mitra will verify each rule from the scheme/notice.",
        "elig_age": "Age (Years)",
        "elig_gender": "Gender",
        "elig_genders": ["Female", "Male", "Transgender"],
        "elig_cat": "Category",
        "elig_cats": ["OC / General", "BC", "SC", "ST", "Minority", "EBC / Kapu"],
        "elig_income": "Annual Family Income (₹)",
        "elig_occupation": "Occupation",
        "elig_occ_placeholder": "e.g. Farmer, Student, Weaver, Auto Driver, Labourer",
        "elig_land": "Total Agricultural Land (Acres)",
        "elig_rice_card": "Has AP Rice Card (White Ration Card)?",
        "elig_govt_job": "Family has Govt Employee or Income Tax Payer?",
        "elig_notes": "Any other details (optional):",
        "elig_notes_placeholder": "e.g., Widow, 45% disability, Class 10 student, Pregnant woman, Street vendor...",
        "elig_btn": "✅ Check My Eligibility",
        "elig_spinner": "Evaluating eligibility rules...",
        "docs_header": "Required Documents Checklist",
        "docs_caption": "Tick the documents you already have ready before visiting the Grama/Ward Sachivalayam or applying online.",
        "docs_extract_btn": "📋 Extract Document List from Notice",
        "docs_extract_spinner": "Extracting required documents...",
        "docs_progress_text": "{ready} of {total} documents ready",
        "docs_ready_tag": "[READY]",
        "docs_needed_tag": "[NEEDED]",
        "docs_how_apply": "How to Apply:",
        "docs_official_portal": "Official Portal:",
        "docs_download_btn": "📥 Download My Document Checklist (.txt)",
        "docs_empty_info": "Click the button above to extract a document checklist from your uploaded notice.",
        "chat_header": "Ask Questions About:",
        "chat_caption": "🔒 Strict Grounding Mode: Pathakam Mitra answers ONLY using facts from the loaded scheme or notice.",
        "chat_listen_btn": "🔊 Listen",
        "chat_voice_expander": "🎙️ Ask by Voice (Speak in Telugu, Hindi, or English)",
        "chat_voice_record": "Record your question",
        "chat_voice_btn": "📨 Send Voice Question",
        "chat_transcribing": "Transcribing your voice...",
        "chat_input_placeholder": "Type your question here...",
        "chat_checking": "Checking official details...",
    },
}

# ==========================================
# 3. DATA & AI HELPER FUNCTIONS
# ==========================================
CANDIDATE_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.8-flash",
]


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
# 4. SIDEBAR NAVIGATION & SETTINGS
# ==========================================
schemes_data = load_schemes()

with st.sidebar:
    language = st.selectbox(
        "🌐 Preferred Language / భాష",
        ["Telugu", "Hindi", "English"],
        index=0,
    )
    T = UI_TRANSLATIONS.get(language, UI_TRANSLATIONS["Telugu"])

    st.markdown(f"## {T['app_name']}")
    st.caption(T["app_caption"])
    st.divider()

    mode_options = [
        T["mode_browse"],
        T["mode_pdf"],
        T["mode_photo"],
        T["mode_paste"],
    ]
    input_mode = st.radio(T["input_mode_label"], mode_options)

    st.divider()
    if not get_gemini_client():
        st.text_input(
            T["api_key_label"],
            type="password",
            key="user_api_key",
            help=T["api_key_help"],
        )

    st.info(T["sidebar_tip"])


# ==========================================
# 5. HERO BANNER
# ==========================================
st.markdown(
    f"""
    <div class="hero-banner">
        <h1>{T['hero_title']}</h1>
        <p>{T['hero_desc']}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

client = get_gemini_client()

# ==========================================
# 6. INPUT SELECTION & EXTRACTION PANEL
# ==========================================
context_title = ""
context_text = ""
selected_scheme_obj = None

with st.container(border=True):
    if input_mode == T["mode_browse"]:
        if not schemes_data:
            st.error("`schemes.json` not found. Run `python parse_schemes.py` in your project folder first.")
            st.stop()

        categories = [T["all_categories"]] + sorted(
            list({s.get("category", "General Welfare") for s in schemes_data})
        )
        col_cat, col_sch = st.columns([1, 2])

        with col_cat:
            chosen_cat = st.selectbox(T["filter_cat_label"], categories)

        filtered_schemes = (
            schemes_data
            if chosen_cat == T["all_categories"]
            else [s for s in schemes_data if s.get("category") == chosen_cat]
        )

        scheme_labels = [f"{s['scheme_number']}. {s['name']}" for s in filtered_schemes]
        with col_sch:
            chosen_label = st.selectbox(T["choose_scheme_label"], scheme_labels)

        selected_scheme_obj = filtered_schemes[scheme_labels.index(chosen_label)]
        context_title = selected_scheme_obj["name"]
        context_text = json.dumps(selected_scheme_obj, indent=2, ensure_ascii=False)

        st.markdown(
            f"""
            <div class="info-card">
                <span class="badge-pill">{selected_scheme_obj.get('state_or_central', 'State')}</span>
                <span class="badge-pill">{selected_scheme_obj.get('category', 'Welfare')}</span>
                <h4 style="margin: 0.6rem 0 0.3rem 0;">{selected_scheme_obj['name']}</h4>
                <p style="margin:0; color:#475569;"><strong>{T['card_dept']}:</strong> {selected_scheme_obj['department']}</p>
                <p style="margin:0.3rem 0 0 0; color:#1B5E20;"><strong>{T['card_benefit']}:</strong> {selected_scheme_obj['benefits']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif input_mode == T["mode_pdf"]:
        pdf_file = st.file_uploader(T["pdf_upload_label"], type=["pdf"])
        if pdf_file:
            with pdfplumber.open(pdf_file) as pdf:
                extracted = "\n".join(page.extract_text() or "" for page in pdf.pages).strip()
            if extracted:
                context_title = pdf_file.name
                context_text = extracted
                st.success(f"{T['pdf_loaded_msg']} `{pdf_file.name}` ({len(extracted)} {T['pdf_chars']}).")
                with st.expander(T["pdf_view_text"]):
                    st.text(extracted[:3000])
            else:
                st.warning(T["pdf_no_text"])

    elif input_mode == T["mode_photo"]:
        st.caption(T["photo_caption"])
        img_file = st.file_uploader(T["photo_upload_label"], type=["jpg", "jpeg", "png", "webp"])
        if img_file:
            col_img, col_ocr = st.columns([1, 1.5])
            with col_img:
                st.image(Image.open(img_file), caption=T["photo_preview"], use_container_width=True)
            with col_ocr:
                if not client:
                    st.warning(T["prompt_api_key"])
                else:
                    if st.button(T["photo_ocr_btn"], type="primary"):
                        with st.spinner(T["photo_ocr_spinner"]):
                            ocr_text = extract_text_from_image(
                                client, img_file.getvalue(), img_file.type or "image/jpeg"
                            )
                            st.session_state["ocr_extracted_text"] = ocr_text
                            st.session_state["ocr_file_name"] = img_file.name

                    if st.session_state.get("ocr_file_name") == img_file.name and st.session_state.get("ocr_extracted_text"):
                        context_title = img_file.name
                        context_text = st.session_state["ocr_extracted_text"]
                        st.success(T["photo_ocr_success"])
                        with st.expander(T["photo_ocr_view"], expanded=True):
                            st.markdown(context_text)

    elif input_mode == T["mode_paste"]:
        pasted_text = st.text_area(
            T["paste_label"],
            height=160,
            placeholder=T["paste_placeholder"],
        )
        if pasted_text.strip():
            context_title = T["pasted_title"]
            context_text = pasted_text.strip()

if not context_text:
    st.info(T["prompt_select"])
    st.stop()

if not client:
    st.warning(T["prompt_api_key"])
    st.stop()

# Reset cached outputs when user switches scheme/document
if st.session_state.get("active_context") != context_title:
    st.session_state["active_context"] = context_title
    st.session_state["summary_text"] = ""
    st.session_state["summary_lang"] = ""
    st.session_state["audio_bytes"] = None
    st.session_state["chat_history"] = []


# ==========================================
# 7. FEATURE TABS (Fully Multilingual)
# ==========================================
tab_explain, tab_elig, tab_docs, tab_chat = st.tabs(
    [
        T["tab_explain"],
        T["tab_elig"],
        T["tab_docs"],
        T["tab_chat"],
    ]
)

# ------------------------------------------
# TAB 1: PLAIN-LANGUAGE EXPLANATION & VOICE
# ------------------------------------------
with tab_explain:
    col_btn, col_info = st.columns([1.3, 2.7])
    with col_btn:
        explain_clicked = st.button(
            T["explain_btn"],
            type="primary",
            use_container_width=True,
        )
    with col_info:
        st.caption(T["explain_caption"])

    if explain_clicked or (
        st.session_state.get("summary_text") and st.session_state.get("summary_lang") != language
    ):
        with st.spinner(T["explain_spinner"]):
            if language == "Telugu":
                sys_prompt = (
                    "మీరు 'పథకం మిత్ర' అనే నమ్మకమైన ప్రజా సహాయకులు. "
                    "గ్రామీణ పౌరులు, వృద్ధులు మరియు నిరక్షరాస్యులకు సులభంగా అర్థమయ్యే తేలికైన నిత్యజీవిత తెలుగులో "
                    "అందించిన పథకం లేదా నోటీసును వివరించండి. కల్పించకుండా అధికారిక వివరాలను మాత్రమే రాయండి."
                )
                prompt = f"""
ఈ క్రింది పథకం లేదా నోటీసును స్పష్టమైన తెలుగులో వివరించండి. తప్పనిసరిగా ఈ శీర్షికలను ఉపయోగించండి:

### 1. ఈ పథకం / నోటీసు ఏమిటి?
### 2. ఎవరు అర్హులు? (ఎవరికి వర్తిస్తుంది?)
### 3. మీకు ఎంత ప్రయోజనం / ఆర్థిక సహాయం లభిస్తుంది?
### 4. ఏయే పత్రాలు (డాక్యుమెంట్లు) అవసరం?
### 5. ఎలా దరఖాస్తు చేసుకోవాలి (దశల వారీ విధానం)?
### 6. ముఖ్యమైన తేదీలు & అధికారిక వెబ్‌సైట్ లింక్

సమాచార మూలం (SOURCE CONTENT):
{context_text}
"""
            elif language == "Hindi":
                sys_prompt = (
                    "आप 'पथकम मित्र' नामक एक सहायक हैं। "
                    "प्रदान की गई सरकारी योजना या नोटिस को सरल और स्पष्ट हिंदी में समझाएं। "
                    "केवल आधिकारिक तथ्यों का ही उपयोग करें।"
                )
                prompt = f"""
निम्नलिखित योजना या नोटिस को स्पष्ट हिंदी में समझाएं। इन शीर्षकों का उपयोग करें:

### 1. यह योजना / नोटिस क्या है?
### 2. कौन पात्र है?
### 3. कितना लाभ / वित्तीय सहायता मिलती है?
### 4. कौन से दस्तावेज़ आवश्यक हैं?
### 5. आवेदन कैसे करें (कदम दर कदम)?
### 6. महत्वपूर्ण तिथियां और आधिकारिक वेबसाइट लिंक

स्रोत सामग्री (SOURCE CONTENT):
{context_text}
"""
            else:
                sys_prompt = (
                    f"You are Pathakam Mitra, a warm, trustworthy civic helper. "
                    f"Explain the provided scheme or government notice in simple, everyday English "
                    f"so rural citizens and senior citizens can understand without confusion. "
                    f"Stick strictly to the facts provided."
                )
                prompt = f"""
Explain the following scheme or notice in simple English using these clear headings:

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
            if st.button(T["read_aloud_btn"], use_container_width=True):
                with st.spinner(T["audio_spinner"]):
                    st.session_state["audio_bytes"] = generate_tts_audio(
                        st.session_state["summary_text"], language
                    )
            if st.session_state.get("audio_bytes"):
                st.audio(st.session_state["audio_bytes"], format="audio/mp3")

        with c_dl:
            st.download_button(
                label=T["download_explain_btn"],
                data=st.session_state["summary_text"],
                file_name=f"Pathakam_Mitra_{context_title[:25].replace(' ', '_')}_{language}.txt",
                mime="text/plain",
                use_container_width=True,
            )


# ------------------------------------------
# TAB 2: ELIGIBILITY CHECKER (Fully Multilingual)
# ------------------------------------------
with tab_elig:
    st.subheader(T["elig_header"])
    st.caption(T["elig_caption"])

    with st.form("eligibility_checker_form"):
        r1c1, r1c2, r1c3 = st.columns(3)
        age = r1c1.number_input(T["elig_age"], min_value=0, max_value=120, value=32)
        gender = r1c2.selectbox(T["elig_gender"], T["elig_genders"])
        social_cat = r1c3.selectbox(T["elig_cat"], T["elig_cats"])

        r2c1, r2c2, r2c3 = st.columns(3)
        annual_income = r2c1.number_input(T["elig_income"], min_value=0, step=10000, value=100000)
        occupation = r2c2.text_input(T["elig_occupation"], value="Farmer", placeholder=T["elig_occ_placeholder"])
        land_acres = r2c3.number_input(T["elig_land"], min_value=0.0, step=0.5, value=1.0)

        r3c1, r3c2 = st.columns(2)
        has_rice_card = r3c1.checkbox(T["elig_rice_card"], value=True)
        has_govt_job_or_tax = r3c2.checkbox(T["elig_govt_job"], value=False)

        special_notes = st.text_input(
            T["elig_notes"],
            placeholder=T["elig_notes_placeholder"],
        )

        check_btn = st.form_submit_button(T["elig_btn"], type="primary")

    if check_btn:
        with st.spinner(T["elig_spinner"]):
            if language == "Telugu":
                sys_prompt = (
                    "మీరు అర్హత పరిశీలనా సహాయకులు. పౌరుడి వివరాలను పథకం/నోటీసులోని అర్హతా నిబంధనలతో ఖచ్చితంగా పోల్చండి. "
                    "సమాధానాన్ని పూర్తిగా స్పష్టమైన తెలుగులో రాయండి."
                )
                eval_prompt = f"""
అందించిన పథకం లేదా నోటీసు ఆధారంగా మాత్రమే ఈ పౌరుడు అర్హుడా కాదా అని విశ్లేషించండి.

కింది శీర్షికలతో స్పష్టమైన తెలుగులో రాయండి:
1. **తీర్పు (Verdict):** ప్రారంభంలో **✅ అర్హత ఉండే అవకాశం ఉంది (Likely Eligible)**, **❌ అర్హత లేదు (Not Eligible)**, లేదా **⚠️ మరిన్ని వివరాలు అవసరం (Needs Verification)** అని స్పష్టంగా తెలపండి.
2. **నిబంధనల వారీ పరిశీలన (Rule-by-Rule Check):** పథకం నిబంధనలతో పౌరుడి వివరాలను సరిపోల్చే బుల్లెట్ పాయింట్లు.
3. **తదుపరి దశ (Next Step):** అర్హులైతే వారు ఏమి చేయాలి, ఎక్కడ దరఖాస్తు చేసుకోవాలి.

పౌరుడి వివరాలు (CITIZEN PROFILE):
- రాష్ట్రం: ఆంధ్రప్రదేశ్
- వయస్సు: {age}
- లింగం: {gender}
- సామాజిక వర్గం: {social_cat}
- వార్షిక కుటుంబ ఆదాయం: ₹{annual_income} (నెలకు సుమారు ₹{annual_income // 12})
- వృత్తి: {occupation}
- వ్యవసాయ భూమి: {land_acres} ఎకరాలు
- AP బియ్యం కార్డు (తెల్ల రేషన్ కార్డు): {"ఉంది (Yes)" if has_rice_card else "లేదు (No)"}
- కుటుంబంలో ప్రభుత్వ ఉద్యోగి / పన్ను చెల్లింపుదారు: {"ఉన్నారు (Yes)" if has_govt_job_or_tax else "లేరు (No)"}
- ఇతర ప్రత్యేక వివరాలు: {special_notes or "ఏమీ లేవు"}

పథకం / నోటీసు వివరాలు (SCHEME / NOTICE DATA):
{context_text}
"""
            else:
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
    st.subheader(T["docs_header"])
    st.caption(T["docs_caption"])

    if selected_scheme_obj and selected_scheme_obj.get("documents_required"):
        docs_list = selected_scheme_obj["documents_required"]
    else:
        if st.button(T["docs_extract_btn"]):
            with st.spinner(T["docs_extract_spinner"]):
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
        progress_text = T["docs_progress_text"].format(ready=ready_count, total=len(checked_status))
        st.progress(ready_count / len(checked_status), text=progress_text)

        checklist_export = f"{T['app_name']} - {T['docs_header']}\n{context_title}\n\n"
        for doc, status in checked_status:
            mark = T["docs_ready_tag"] if status else T["docs_needed_tag"]
            checklist_export += f"{mark} {doc}\n"

        if selected_scheme_obj:
            checklist_export += f"\n{T['docs_how_apply']}\n{selected_scheme_obj['how_to_apply']}\n"
            checklist_export += f"\n{T['docs_official_portal']}\n{selected_scheme_obj['official_website']}\n"

        st.download_button(
            label=T["docs_download_btn"],
            data=checklist_export,
            file_name=f"Checklist_{context_title[:25].replace(' ', '_')}_{language}.txt",
            mime="text/plain",
        )
    else:
        st.info(T["docs_empty_info"])


# ------------------------------------------
# TAB 4: STRICTLY GROUNDED Q&A (TEXT + VOICE)
# ------------------------------------------
with tab_chat:
    st.subheader(f"{T['chat_header']} {context_title}")
    st.caption(T["chat_caption"])

    for i, msg in enumerate(st.session_state.get("chat_history", [])):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                if st.button(T["chat_listen_btn"], key=f"tts_chat_{i}"):
                    aud = generate_tts_audio(msg["content"], language)
                    st.audio(aud, format="audio/mp3")

    with st.expander(T["chat_voice_expander"], expanded=False):
        recorded_audio = st.audio_input(T["chat_voice_record"])
        if recorded_audio and st.button(T["chat_voice_btn"], type="primary"):
            with st.spinner(T["chat_transcribing"]):
                transcribed_q = transcribe_voice_query(client, recorded_audio.getvalue())
                st.session_state["pending_voice_q"] = transcribed_q

    typed_q = st.chat_input(T["chat_input_placeholder"])
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
            with st.spinner(T["chat_checking"]):
                answer = generate_text(client, qa_prompt, strict_sys_prompt)
                st.markdown(answer)

        st.session_state["chat_history"].append({"role": "assistant", "content": answer})
        st.rerun()
