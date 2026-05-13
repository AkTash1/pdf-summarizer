import streamlit as st
import fitz
import easyocr
import os
import re
import tempfile
from groq import Groq
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import PIL.Image
import pytesseract
from PIL import Image

# ── Page config ──────────────────────────────────────────
st.set_page_config(
    page_title="Document Summarizer",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Document Summarizer")
st.caption("Upload a scanned PDF to get summaries and selectable text")

# ── Groq client ──────────────────────────────────────────
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ── Cache OCR reader ─────────────────────────────────────
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])


# ── Helper functions ─────────────────────────────────────
def pdf_to_images(pdf_path, output_folder):
    pdf = fitz.open(pdf_path)
    image_paths = []
    for i in range(len(pdf)):
        page = pdf[i]
        mat = fitz.Matrix(300/72, 300/72)
        img = page.get_pixmap(matrix=mat)
        path = os.path.join(output_folder, f"page_{i+1}.png")
        img.save(path)
        image_paths.append(path)
    return image_paths

def clean_text(text):
    text = re.sub(r'-\s+', '', text)
    text = re.sub(r'[|\\•§©®™]', '', text)
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'^\d+$', '', text, flags=re.MULTILINE)
    return text.strip()

def run_ocr(image_paths, reader):
    full_text = ""
    for path in image_paths:
        img = Image.open(path)
        text = pytesseract.image_to_string(img)
        full_text += text + "\n"
    return full_text

def create_selectable_pdf(image_paths, output_path, reader):
    c = canvas.Canvas(output_path, pagesize=A4)
    page_width, page_height = A4
    for path in image_paths:
        img = Image.open(path)
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        for i, text in enumerate(data['text']):
            if text.strip() and int(data['conf'][i]) > 40:
                x = (data['left'][i] / img.width) * page_width
                y = page_height - (data['top'][i] / img.height) * page_height
                c.setFont("Helvetica", 10)
                c.drawString(x, y, text)
        c.showPage()
    c.save()

def call_llm(prompt):
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=4000
    )
    return response.choices[0].message.content

# ── Main UI ───────────────────────────────────────────────
uploaded_file = st.file_uploader("Upload your scanned PDF", type="pdf")

if uploaded_file:
    st.success(f"✅ Uploaded: {uploaded_file.name}")

    if st.button("🚀 Process Document", type="primary"):
        reader = load_ocr()
        with tempfile.TemporaryDirectory() as tmpdir:

            # Save uploaded PDF
            pdf_path = os.path.join(tmpdir, "input.pdf")
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.read())

            # Stage 1 — PDF to images
            with st.status("Converting PDF to images..."):
                image_paths = pdf_to_images(pdf_path, tmpdir)
                st.write(f"✅ {len(image_paths)} pages found")

            # Stage 2 — OCR
            with st.status("Running OCR on all pages..."):
                full_text = run_ocr(image_paths, reader)
                st.write(f"✅ OCR complete — {len(full_text)} characters extracted")

            # Stage 3 — Selectable PDF
            with st.status("Creating selectable PDF..."):
                selectable_pdf_path = os.path.join(tmpdir, "selectable.pdf")
                create_selectable_pdf(image_paths, selectable_pdf_path, reader)
                with open(selectable_pdf_path, "rb") as f:
                    selectable_pdf_bytes = f.read()
                st.write("✅ Selectable PDF created")

            # Stage 4 — LLM Summaries
            with st.status("Generating Quick Summary..."):
                quick_summary = call_llm(f"""
Extract 10-15 most important key points from this document.
Group them under relevant headings.
Each point should be one clear sentence.
Document: {full_text}
""")
                st.write("✅ Quick summary done")

            with st.status("Generating Deep Summary..."):
                deep_summary = call_llm(f"""
You are a senior analyst. Write a comprehensive 2000+ word summary of this document covering:
1. Executive Overview
2. Background & Context
3. Section-by-Section Breakdown
4. Key Findings & Insights
5. Data, Statistics & Numbers
6. Recommendations & Decisions
7. Risks, Challenges & Concerns
8. Action Items & Next Steps
9. Notable Observations
10. Final Conclusion
Write in full paragraphs. Be thorough.
Document: {full_text}
""")
                st.write("✅ Deep summary done")

            with st.status("Expanding Covenants & Schedules..."):
                covenant_summary = call_llm(f"""
You are a legal analyst. Find ALL covenants and schedules in this document.
For each covenant: explain what it requires, who is bound, consequences of breach, timelines. Minimum 200 words each.
For each schedule: explain contents, purpose, every item listed, significance. Minimum 200 words each.
Write in full paragraphs. Be exhaustive.
Document: {full_text}
""")
                st.write("✅ Covenants & Schedules done")

        # ── Display Results ───────────────────────────────
        st.divider()
        st.subheader("📥 Downloads")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.download_button(
                "📄 Selectable PDF",
                data=selectable_pdf_bytes,
                file_name="selectable_document.pdf",
                mime="application/pdf"
            )
        with col2:
            st.download_button(
                "⚡ Quick Summary",
                data=quick_summary,
                file_name="quick_summary.md",
                mime="text/markdown"
            )
        with col3:
            st.download_button(
                "📋 Deep Summary",
                data=deep_summary,
                file_name="deep_summary.md",
                mime="text/markdown"
            )
        with col4:
            st.download_button(
                "⚖️ Covenants & Schedules",
                data=covenant_summary,
                file_name="covenants_schedules.md",
                mime="text/markdown"
            )

        st.divider()

        # ── Display summaries in tabs ─────────────────────
        tab1, tab2, tab3 = st.tabs([
            "⚡ Quick Summary",
            "📋 Deep Summary",
            "⚖️ Covenants & Schedules"
        ])

        with tab1:
            st.markdown(quick_summary)
        with tab2:
            st.markdown(deep_summary)
        with tab3:
            st.markdown(covenant_summary)
