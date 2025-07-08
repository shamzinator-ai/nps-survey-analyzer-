import os
import json
from io import BytesIO
from typing import List, Tuple
import time
import hashlib

import altair as alt
import openai
import pandas as pd
import streamlit as st
from docx import Document
from fpdf import FPDF

# Set your OpenAI API key via environment variable
openai.api_key = os.getenv("OPENAI_API_KEY", "")
MODEL = "gpt-4o-mini"

# Directory for cached processed data
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

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

@st.cache_data(show_spinner=False)
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


@st.cache_data(show_spinner=False)
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


def download_link(df: pd.DataFrame, filename: str, label: str, help: str | None = None):
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(label, csv, file_name=filename, mime='text/csv', help=help)


def export_excel(df: pd.DataFrame, filename: str, label: str, help: str | None = None):
    """Download a DataFrame as an Excel file."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    st.download_button(
        label,
        buffer.getvalue(),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help=help,
    )


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
                "Translated", value=row["Translated"], key=f"trans_{idx}",
                help="Edit the AI translation if it looks incorrect.")
            new_cats = st.multiselect(
                "Categories", options=CATEGORIES,
                default=[c.strip() for c in row["Categories"].split(',') if c],
                key=f"cat_{idx}",
                help="Add or remove categories for this comment.")
            flag = st.checkbox(
                "Flag for review", key=f"flag_{idx}",
                help="Mark this comment for manual follow-up.")
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


def save_docx(text: str) -> BytesIO:
    document = Document()
    document.add_paragraph(text)
    bio = BytesIO()
    document.save(bio)
    bio.seek(0)
    return bio


def save_pdf(text: str) -> BytesIO:
    """Save text as a simple PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in text.split("\n"):
        pdf.multi_cell(0, 10, line)
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

st.sidebar.header("1. Upload Survey Data")
st.sidebar.markdown(
    "🔗 [Troubleshooting guide](README.md#troubleshooting)")
file = st.sidebar.file_uploader(
    "Upload CSV, XLS or XLSX", type=["csv", "xls", "xlsx"],
    help="File must include a unique ID, location, at least one structured and one free-text column."
)

if file and validate_file(file):
    raw_bytes = file.getvalue()
    checksum = hashlib.md5(raw_bytes).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{checksum}.pkl")
    if "processed_df" in st.session_state:
        df = st.session_state["processed_df"]
    elif os.path.exists(cache_path):
        df = pd.read_pickle(cache_path)
        st.success("Loaded cached processed data")
    else:
        try:
            if file.name.endswith(("xls", "xlsx")):
                df = pd.read_excel(BytesIO(raw_bytes))
            else:
                df = pd.read_csv(BytesIO(raw_bytes))
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

    user_id_col = st.selectbox(
        "Column with User ID", options=df.columns,
        help="Select the column that uniquely identifies each user."
    )
    location_col = st.selectbox(
        "Column with County/Location", options=df.columns,
        help="Pick the column that indicates user location or segment."
    )

    free_text_cols = st.multiselect(
        "Free-text response columns",
        options=[c for c in df.columns if c not in [user_id_col, location_col]],
        help="These comments will be translated and categorised."
    )

    structured_cols = st.multiselect(
        "Structured question columns",
        options=[c for c in df.columns if c not in free_text_cols + [user_id_col, location_col]],
        default=[c for c in df.columns if c not in free_text_cols + [user_id_col, location_col]],
        help="Responses to these columns will be summarised in pivot tables."
    )

    segment_options = df[location_col].dropna().unique().tolist()
    selected_segments = st.multiselect(
        "Filter by segment (optional)", options=segment_options,
        help="Choose segments to focus on or leave empty for all."
    )
    if selected_segments:
        df = df[df[location_col].isin(selected_segments)]

    st.markdown("### Available Categories")
    st.write(", ".join(CATEGORIES))

    if st.button(
        "Process Data",
        help="Translate comments, categorise them and generate summaries."
    ):
        with st.spinner("Processing free-text responses..."):
            df = process_free_text(df, free_text_cols)

        st.success("Processing complete")

        df = review_translations(df, user_id_col)
        st.session_state["processed_df"] = df
        df.to_pickle(cache_path)

        st.subheader("Structured Data Analysis")
        for col in structured_cols:
            pivot = generate_pivot(df, col)
            st.write(f"### {col}")
            st.dataframe(pivot)
            bar_chart(pivot, f"{col} Responses")
            c1, c2 = st.columns(2)
            with c1:
                download_link(
                    pivot,
                    f"pivot_{col}.csv",
                    f"Download {col} CSV",
                    help="Download the pivot table as a CSV file."
                )
            with c2:
                export_excel(
                    pivot,
                    f"pivot_{col}.xlsx",
                    f"Download {col} Excel",
                    help="Download the pivot table as an Excel file."
                )

        st.subheader("Categorized Comments")
        display_cols = [user_id_col, location_col, 'Concatenated', 'Translated', 'Language', 'Categories', 'Flagged']
        st.dataframe(df[display_cols])
        if st.button(
            "Spot-check 5 Random Comments",
            help="Preview a random sample to verify AI results."
        ):
            sample = df.sample(min(5, len(df)))
            for _, row in sample.iterrows():
                st.write(f"**User {row[user_id_col]}** - {row['Categories']}")
                st.write(row['Translated'])
        download_link(
            df,
            "full_results.csv",
            "Download All Results",
            help="Save the full dataset with translations and categories."
        )

        if st.button(
            "Generate Report",
            help="Create a narrative summary of all findings."
        ):
            report_text = generate_report(df[[user_id_col, location_col, 'Translated', 'Categories', 'Flagged']])
            if report_text:
                st.markdown(report_text)
                docx_file = save_docx(report_text)
                pdf_file = save_pdf(report_text)
                st.download_button(
                    "Download DOCX",
                    docx_file,
                    "report.docx",
                    help="Save the report as a Word document."
                )
                st.download_button(
                    "Download PDF",
                    pdf_file,
                    "report.pdf",
                    help="Save the report as a PDF file."
                )
else:
    st.info("Upload a survey file to begin.")
