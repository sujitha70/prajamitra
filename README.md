# Pathakam Mitra (పథకం మిత్ర)

An AI-powered citizen assistant that simplifies Andhra Pradesh government welfare schemes and official notices into plain **Telugu**, **Hindi**, and **English**, checks eligibility, generates downloadable document checklists, and answers questions strictly grounded in official data.

## Core Features
- **90+ AP & Central Welfare Schemes:** Searchable and filterable by category.
- **Multi-Modal Input:** Browse schemes, upload PDF notices, upload/snap notice photos (Gemini Vision OCR), or paste raw text.
- **Plain-Language Simplifier + Audio:** Clear summaries in Telugu, Hindi, or English with one-click voice playback (`gTTS`).
- **Eligibility Checker:** Rule-by-rule check based on age, gender, category, income, occupation, landholding, and AP Rice Card status.
- **Interactive Document Checklist:** Tick off ready documents and download a `.txt` checklist.
- **Strictly Grounded Voice & Text Q&A:** Ask questions via text or voice recording; answers come strictly from the loaded document.

## Local Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Add your `GEMINI_API_KEY` to `.env`.
3. Parse the 90-scheme Markdown dataset into JSON:
   ```bash
   python parse_schemes.py
   ```
4. Launch the app:
   ```bash
   streamlit run app.py
   ```
