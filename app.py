import os
import json
from io import BytesIO
from typing import List, Tuple
import time

import altair as alt
import openai
import pandas as pd
import streamlit as st
from docx import Document
from docx.shared import Inches
from fpdf import FPDF
import matplotlib.pyplot as plt
import tempfile

# Set your OpenAI API key via environment variable
openai.api_key = os.getenv("OPENAI_API_KEY", "")
MODEL = "gpt-4o-mini"

CATEGORIES = [
    "Search/Navigation", "Resource Mention", "User Question", "Translation Mention",
    "User Suggestion", "Pain Point", "AI", "Competitor", "Site Error", "Social Media",
    "Phonics", "Price Mention", "Accidental Purchase", "Resource Preview",
    "Resource Request", "Editing/Adapting Resource", "Resource Quality", "EDI", "SEND",
    "Partnership", "Parental Leave", "Email", "Email Verification", "Not Used Enough",
    "Legal", "Glassdoor", "GDPR", "Free Resources", "Download Issues", "Content Errors",
    "Account Access", "Already Cancelled", "Auto-renewal", "Book Club",
    "Cancellation Difficulty", "CS General", "CS Negative", "CS Positive",
    "Negative Words", "Positive Words"
]

# ----------------------------- Utility Functions -----------------------------

def translate_text(text: str) -> Tuple[str, str]:
    """Detect language and translate text to English using GPT-4o-mini."""
    if not text or not text.strip():
        return "", ""
    prompt = (
        "Detect the language of the following text and translate it to English. "
        "Respond in JSON with keys 'language' and 'translation'.\nText: " + text
    )
    try:
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return data.get("translation", "").strip(), data.get("language", "")
    except Exception as e:
        st.error(f"Translation failed: {e}")
        return text, ""


def categorize_text(text: str) -> List[str]:
    """Categorize text using GPT-4o-mini."""
    if not text:
        return []
    categories_str = ", ".join(CATEGORIES)
    system_prompt = (
        "You are a helpful assistant that tags survey comments with all relevant "
        "categories from the provided list. Return a comma-separated list of "
        "matching categories. If none apply, return 'None'."
    )
    user_prompt = f"Categories: {categories_str}\nComment: {text}"
    try:
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0
        )
        result = response.choices[0].message.content.strip()
        if result.lower() == "none":
            return []
        return [c.strip() for c in result.split(',')]
    except Exception as e:
        st.error(f"Categorization failed: {e}")
        return []


def generate_pivot(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Return value counts with percentage and total row."""
    pivot = df[column].value_counts(dropna=False).reset_index()
    pivot.columns = ["Response", "Count"]
    total = pivot["Count"].sum()
    pivot["Percent"] = (pivot["Count"] / total * 100).round(1)
    total_row = pd.DataFrame({"Response": ["Total"], "Count": [total], "Percent": [100.0]})
    pivot = pd.concat([pivot, total_row], ignore_index=True)
    return pivot


def bar_chart(pivot: pd.DataFrame, title: str):
    chart = alt.Chart(pivot).mark_bar().encode(
        x=alt.X('Response:N', sort='-y'),
        y='Count:Q',
        tooltip=['Response', 'Count']
    ).properties(title=title, height=300)
    st.altair_chart(chart, use_container_width=True)


def chart_to_png(pivot: pd.DataFrame, title: str) -> BytesIO:
    """Create a bar chart as a PNG image and return the bytes."""
    plot_df = pivot[pivot["Response"] != "Total"].copy()
    fig, ax = plt.subplots()
    ax.bar(plot_df["Response"].astype(str), plot_df["Count"])
    ax.set_title(title)
    ax.set_xlabel("Response")
    ax.set_ylabel("Count")
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf


def download_link(df: pd.DataFrame, filename: str, label: str):
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(label, csv, file_name=filename, mime='text/csv')


def validate_file(uploaded_file) -> bool:
    """Basic checks for uploaded file size and type."""
    max_size = 10 * 1024 * 1024  # 10MB
    if uploaded_file.size > max_size:
        st.error("File too large. Maximum size is 10MB.")
        return False
    return True


def review_translations(df: pd.DataFrame, id_col: str) -> pd.DataFrame:
    """Allow user to edit translations and categories."""
    st.subheader("Review Translations and Categories")
    flags = []
    for idx, row in df.iterrows():
        with st.expander(f"User {row[id_col]}"):
            st.write("**Original:**", row["Concatenated"])
            new_trans = st.text_area(
                "Translated", value=row["Translated"], key=f"trans_{idx}")
            new_cats = st.multiselect(
                "Categories", options=CATEGORIES,
                default=[c.strip() for c in row["Categories"].split(',') if c],
                key=f"cat_{idx}")
            flag = st.checkbox("Flag for review", key=f"flag_{idx}")
            df.at[idx, "Translated"] = new_trans
            df.at[idx, "Categories"] = ", ".join(new_cats)
            flags.append(flag)
    df["Flagged"] = flags
    return df


def generate_report(df: pd.DataFrame) -> str:
    """Generate a detailed report covering all requested sections."""
    prompt = (
        "You are an expert analyst summarising NPS survey feedback. "
        "Write a detailed report with the following sections:\n"
        "Executive Summary of findings;\n"
        "Customer Suggestions with quoted comments and IDs;\n"
        "Localisation Issues, especially for US users;\n"
        "Pain Points;\n"
        "Negative Comments;\n"
        "Feedback not captured in categories;\n"
        "Suggested Next Steps with rationale, priority and confidence level;\n"
        "Devils Advocate (limitations and possible biases);\n"
        "Conclusion with summary and non-obvious recommendations.\n"
        "For every statement include raw number and percentage of supporting comments. "
        "Avoid bullet points and write in narrative paragraphs."
    )
    user_content = df.to_csv(index=False)
    try:
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": prompt},
                      {"role": "user", "content": user_content}],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Report generation failed: {e}")
        return ""


def save_docx(text: str, pivots: List[Tuple[str, pd.DataFrame]], charts: List[Tuple[str, BytesIO]]) -> BytesIO:
    """Save the narrative report with tables and charts to DOCX."""
    document = Document()
    document.add_paragraph(text)
    for (name, pivot), (_, chart) in zip(pivots, charts):
        document.add_heading(name, level=2)
        table = document.add_table(rows=pivot.shape[0] + 1, cols=pivot.shape[1])
        for j, col in enumerate(pivot.columns):
            table.cell(0, j).text = str(col)
        for i, row in pivot.iterrows():
            for j, col in enumerate(pivot.columns):
                table.cell(i + 1, j).text = str(row[col])
        chart.seek(0)
        document.add_picture(chart, width=Inches(5))
    bio = BytesIO()
    document.save(bio)
    bio.seek(0)
    return bio


def save_pdf(text: str, pivots: List[Tuple[str, pd.DataFrame]], charts: List[Tuple[str, BytesIO]]) -> BytesIO:
    """Save the narrative report with tables and charts to PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in text.split("\n"):
        pdf.multi_cell(0, 10, line)
    for (name, pivot), (_, chart) in zip(pivots, charts):
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, name, ln=True)
        pdf.set_font("Arial", size=10)
        col_width = (pdf.w - 20) / len(pivot.columns)
        for col in pivot.columns:
            pdf.cell(col_width, 10, str(col), border=1)
        pdf.ln()
        for _, row in pivot.iterrows():
            for col in pivot.columns:
                pdf.cell(col_width, 10, str(row[col]), border=1)
            pdf.ln()
        chart.seek(0)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        tmp.write(chart.getbuffer())
        tmp.close()
        pdf.image(tmp.name, w=pdf.w - 20)
        os.unlink(tmp.name)
    bio = BytesIO()
    pdf.output(bio)
    bio.seek(0)
    return bio


def process_free_text(df: pd.DataFrame, free_text_cols: List[str]) -> pd.DataFrame:
    """Concatenate, translate and categorize free-text columns with progress."""
    concat, translated, categories, languages = [], [], [], []
    progress = st.progress(0.0, text="Starting...")
    start = time.time()
    for i, (_, row) in enumerate(df.iterrows(), start=1):
        combined = " ".join(str(row[c]) if pd.notnull(row[c]) else "" for c in free_text_cols)
        trans, lang = translate_text(combined)
        cats = categorize_text(trans)
        concat.append(combined)
        translated.append(trans)
        languages.append(lang)
        categories.append(", ".join(cats))
        rate = (time.time() - start) / i
        remaining = rate * (len(df) - i)
        progress.progress(i / len(df), text=f"Processing... ETA {int(remaining)}s")
    progress.empty()
    df["Concatenated"] = concat
    df["Translated"] = translated
    df["Language"] = languages
    df["Categories"] = categories
    return df

# ----------------------------- Streamlit App -----------------------------

st.set_page_config(page_title="NPS Survey Analyzer", layout="wide")
st.title("NPS Survey Analyzer")

if "processed_df" not in st.session_state:
    st.session_state.processed_df = None
if "pivots" not in st.session_state:
    st.session_state.pivots = {}
if "charts" not in st.session_state:
    st.session_state.charts = {}

st.sidebar.header("1. Upload Survey Data")
file = st.sidebar.file_uploader(
    "Upload CSV, XLS or XLSX", type=["csv", "xls", "xlsx"],
    help="File must include a unique ID, location, at least one structured and one free-text column."
)

if file and validate_file(file):
    try:
        if file.name.endswith(("xls", "xlsx")):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)
        if df.empty:
            st.error("Uploaded file contains no data")
            st.stop()
        if df.isnull().all(axis=0).any():
            st.warning("Some columns contain only missing values")
    except Exception as e:
        st.error(f"Failed to read file: {e}")
        st.stop()

    st.subheader("Data Preview")
    st.dataframe(df.head(10))
    st.write(f"**Rows:** {df.shape[0]}  **Columns:** {df.shape[1]}")
    st.write("**Columns:**", ", ".join(df.columns))

    user_id_col = st.selectbox("Column with User ID", options=df.columns)
    location_col = st.selectbox("Column with County/Location", options=df.columns)

    free_text_cols = st.multiselect(
        "Free-text response columns", options=[c for c in df.columns if c not in [user_id_col, location_col]]
    )

    structured_cols = st.multiselect(
        "Structured question columns", options=[c for c in df.columns if c not in free_text_cols + [user_id_col, location_col]],
        default=[c for c in df.columns if c not in free_text_cols + [user_id_col, location_col]]
    )

    segment_options = df[location_col].dropna().unique().tolist()
    selected_segments = st.multiselect("Filter by segment (optional)", options=segment_options)
    if selected_segments:
        df = df[df[location_col].isin(selected_segments)]

    st.markdown("### Available Categories")
    st.write(", ".join(CATEGORIES))

    if st.button("Process Data"):
        with st.spinner("Processing free-text responses..."):
            df = process_free_text(df, free_text_cols)

        df = review_translations(df, user_id_col)
        st.session_state.processed_df = df
        st.session_state.pivots = {}
        st.session_state.charts = {}
        for col in structured_cols:
            pivot = generate_pivot(df, col)
            st.session_state.pivots[col] = pivot
            img = chart_to_png(pivot, f"{col} Responses")
            st.session_state.charts[col] = img.getvalue()
        st.success("Processing complete")

    if st.session_state.processed_df is not None:
        df = st.session_state.processed_df
        st.subheader("Structured Data Analysis")
        for col in structured_cols:
            pivot = st.session_state.pivots.get(col)
            if pivot is None:
                pivot = generate_pivot(df, col)
                st.session_state.pivots[col] = pivot
                img = chart_to_png(pivot, f"{col} Responses")
                st.session_state.charts[col] = img.getvalue()
            st.write(f"### {col}")
            st.dataframe(pivot)
            bar_chart(pivot, f"{col} Responses")
            download_link(pivot, f"pivot_{col}.csv", f"Download {col} Pivot")

        st.subheader("Categorized Comments")
        display_cols = [user_id_col, location_col, 'Concatenated', 'Translated', 'Language', 'Categories', 'Flagged']
        st.dataframe(df[display_cols])
        if st.button("Spot-check 5 Random Comments"):
            sample = df.sample(min(5, len(df)))
            for _, row in sample.iterrows():
                st.write(f"**User {row[user_id_col]}** - {row['Categories']}")
                st.write(row['Translated'])
        download_link(df, "full_results.csv", "Download All Results")

        if st.button("Generate Report"):
            report_text = generate_report(df[[user_id_col, location_col, 'Translated', 'Categories', 'Flagged']])
            if report_text:
                pivots = [(col, st.session_state.pivots[col]) for col in structured_cols]
                charts = [(col, BytesIO(st.session_state.charts[col])) for col in structured_cols]
                st.markdown(report_text)
                docx_file = save_docx(report_text, pivots, charts)
                pdf_file = save_pdf(report_text, pivots, charts)
                st.download_button("Download DOCX", docx_file, "report.docx")
                st.download_button("Download PDF", pdf_file, "report.pdf")
else:
    st.info("Upload a survey file to begin.")
