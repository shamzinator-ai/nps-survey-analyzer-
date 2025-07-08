import os
import json
from io import BytesIO, StringIO
from typing import List, Tuple
import time
import asyncio
import hashlib

import altair as alt
import openai
import pandas as pd
import streamlit as st
from docx import Document
from docx.shared import Inches
from fpdf import FPDF
import tempfile
import zipfile

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

# Map each category to a short description shown in the sidebar
CATEGORY_DESCRIPTIONS = {
    "Search/Navigation": "Finding resources or moving around the site",
    "Resource Mention": "References to specific products or resources",
    "User Question": "Questions users ask about the service",
    "Translation Mention": "Comments about translation quality or requests",
    "User Suggestion": "Ideas or feature requests from users",
    "Pain Point": "Descriptions of frustrations or obstacles",
    "AI": "Mentions of AI or automated features",
    "Competitor": "Comparisons to or mentions of competitors",
    "Site Error": "Reports of errors or broken pages",
    "Social Media": "Links or references to social media platforms",
    "Phonics": "Feedback specifically about phonics content",
    "Price Mention": "Concerns related to pricing or cost",
    "Accidental Purchase": "Unintended purchases or charges",
    "Resource Preview": "Ability to preview resources before buying",
    "Resource Request": "Requests for new resources",
    "Editing/Adapting Resource": "Need to edit or customise resources",
    "Resource Quality": "Opinions about quality of resources",
    "EDI": "Equity, diversity and inclusion topics",
    "SEND": "Special educational needs and disabilities",
    "Partnership": "Potential or ongoing partnerships",
    "Parental Leave": "Questions about parental leave policies",
    "Email": "General email communication issues",
    "Email Verification": "Problems verifying email accounts",
    "Not Used Enough": "Users saying they don't use the service often",
    "Legal": "Legal references or compliance concerns",
    "Glassdoor": "Mentions of Glassdoor reviews or reputation",
    "GDPR": "Data protection and GDPR related comments",
    "Free Resources": "Discussion of free offerings",
    "Download Issues": "Trouble downloading files or resources",
    "Content Errors": "Mistakes found in content or resources",
    "Account Access": "Login or account access problems",
    "Already Cancelled": "Users claiming they already cancelled",
    "Auto-renewal": "Concerns about auto-renewing subscriptions",
    "Book Club": "References to book club features",
    "Cancellation Difficulty": "Difficulty cancelling subscriptions",
    "CS General": "General customer service feedback",
    "CS Negative": "Negative comments about support",
    "CS Positive": "Positive comments about support",
    "Negative Words": "Use of negative language or sentiment",
    "Positive Words": "Use of positive language or sentiment",
}

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


async def async_translate_batch(texts: List[str]) -> List[Tuple[str, str, int, str]]:
    """Translate a batch of texts concurrently using OpenAI's async API."""

    async def _translate(text: str) -> Tuple[str, str, int, str]:
        if not text or not text.strip():
            return "", "", 0, ""
        prompt = (
            "Detect the language of the following text and translate it to English."
            "Respond in JSON with keys 'language' and 'translation'.\nText: " + text
        )
        try:
            response = await openai.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            content = response.choices[0].message.content
            data = json.loads(content)
            tokens = response.usage.total_tokens if getattr(response, "usage", None) else 0
            finish = response.choices[0].finish_reason or ""
            return (
                data.get("translation", "").strip(),
                data.get("language", ""),
                tokens,
                finish,
            )
        except Exception as e:
            st.error(f"Translation failed: {e}")
            return text, "", 0, ""

    tasks = [asyncio.create_task(_translate(t)) for t in texts]
    return await asyncio.gather(*tasks)


async def async_categorize_batch(texts: List[str]) -> List[Tuple[List[str], int, str]]:
    """Categorize a batch of texts concurrently."""

    categories_str = ", ".join(CATEGORIES)
    system_prompt = (
        "You are a helpful assistant that tags survey comments with all relevant "
        "categories from the provided list. Return a comma-separated list of "
        "matching categories. If none apply, return 'None'."
    )

    async def _categorize(text: str) -> Tuple[List[str], int, str]:
        if not text:
            return [], 0, ""
        user_prompt = f"Categories: {categories_str}\nComment: {text}"
        try:
            response = await openai.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
            )
            result = response.choices[0].message.content.strip()
            tokens = response.usage.total_tokens if getattr(response, "usage", None) else 0
            finish = response.choices[0].finish_reason or ""
            if result.lower() == "none":
                return [], tokens, finish
            return [c.strip() for c in result.split(',')], tokens, finish
        except Exception as e:
            st.error(f"Categorization failed: {e}")
            return [], 0, ""

    tasks = [asyncio.create_task(_categorize(t)) for t in texts]
    return await asyncio.gather(*tasks)


def generate_pivot(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Return value counts with percentage and total row."""
    pivot = df[column].value_counts(dropna=False).reset_index()
    pivot.columns = ["Response", "Count"]
    total = pivot["Count"].sum()
    pivot["Percent"] = (pivot["Count"] / total * 100).round(1)
    total_row = pd.DataFrame({"Response": ["Total"], "Count": [total], "Percent": [100.0]})
    pivot = pd.concat([pivot, total_row], ignore_index=True)
    return pivot


def create_chart(pivot: pd.DataFrame, title: str):
    """Return an Altair chart object matching the on-screen chart."""
    color_range = ["#ff66b3", "#3399ff"]
    chart = (
        alt.Chart(pivot, background="white")
        .mark_bar()
        .encode(
            x=alt.X("Response:N", sort="-y", title="Response"),
            y=alt.Y("Count:Q", title="Count"),
            color=alt.Color("Count:Q", scale=alt.Scale(range=color_range), legend=None),
            tooltip=["Response", "Count"],
        )
        .properties(title=f"{title} 📊", height=300)
        .configure_title(fontSize=18)
        .configure_axis(labelFontSize=12, titleFontSize=14)
    )
    return chart


def chart_png(pivot: pd.DataFrame, title: str) -> BytesIO:
    """Return a PNG image buffer for the given pivot chart."""
    chart = create_chart(pivot, title)
    buf = BytesIO()
    chart.save(buf, format="png")
    buf.seek(0)
    return buf


def bar_chart(pivot: pd.DataFrame, title: str) -> BytesIO:
    """Display a bar chart and provide PNG/SVG downloads. Returns PNG buffer."""
    chart = create_chart(pivot, title)
    st.altair_chart(chart, use_container_width=True)

    png_buffer = BytesIO()
    chart.save(png_buffer, format="png")
    png_buffer.seek(0)
    svg_buffer = StringIO()
    chart.save(svg_buffer, format="svg")
    svg_bytes = svg_buffer.getvalue().encode("utf-8")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Download Chart PNG",
            png_buffer,
            file_name=f"{title}.png",
            mime="image/png",
        )
    with col2:
        st.download_button(
            "Download Chart SVG",
            svg_bytes,
            file_name=f"{title}.svg",
            mime="image/svg+xml",
        )

    return png_buffer


def category_frequency(df: pd.DataFrame) -> pd.DataFrame:
    """Return counts and percentages for all categories."""
    cats = df["Categories"].str.split(",").explode().str.strip()
    cats = cats[cats != ""]
    pivot = cats.value_counts().reset_index()
    pivot.columns = ["Category", "Count"]
    total = pivot["Count"].sum()
    pivot["Percent"] = (pivot["Count"] / total * 100).round(1)
    total_row = pd.DataFrame({"Category": ["Total"], "Count": [total], "Percent": [100.0]})
    return pd.concat([pivot, total_row], ignore_index=True)


def sentiment_metrics(df: pd.DataFrame) -> tuple[int, int]:
    """Return counts of positive and negative comments."""
    pos = df["Categories"].str.contains("Positive Words", na=False).sum()
    neg = df["Categories"].str.contains("Negative Words", na=False).sum()
    return pos, neg


def display_summary(df: pd.DataFrame, nps_col: str | None):
    """Show high-level KPIs and charts."""
    st.subheader("🚀 High-Level KPIs")
    if nps_col and nps_col in df.columns:
        nps_pivot = generate_pivot(df, nps_col)
        st.write("### NPS Distribution")
        st.dataframe(nps_pivot)
        bar_chart(nps_pivot, "NPS Distribution")
    cat_pivot = category_frequency(df)
    st.write("### Category Frequency")
    st.dataframe(cat_pivot)
    bar_chart(cat_pivot, "Category Frequency")
    pos, neg = sentiment_metrics(df)
    st.metric("Positive/Negative Ratio", f"{pos}:{neg}")
    if not cat_pivot.empty:
        st.write("Top 3 Issues:", ", ".join(cat_pivot.head(3)["Category"].tolist()))


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
            st.write(f"Tokens used: {row.get('ModelTokens', 0)}")
            st.write(f"Finish reason: {row.get('FinishReason', '')}")
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


def save_docx(text: str, pivots: dict[str, pd.DataFrame]) -> BytesIO:
    """Create a DOCX report with text, pivot tables and charts."""
    document = Document()
    for para in text.split("\n"):
        document.add_paragraph(para)

    for title, pivot in pivots.items():
        document.add_heading(title, level=2)
        table = document.add_table(rows=1, cols=len(pivot.columns))
        hdr = table.rows[0].cells
        for idx, col in enumerate(pivot.columns):
            hdr[idx].text = str(col)
        for _, row in pivot.iterrows():
            cells = table.add_row().cells
            for idx, col in enumerate(pivot.columns):
                cells[idx].text = str(row[col])
        img = chart_png(pivot, f"{title} Responses")
        img.name = "chart.png"
        document.add_picture(img, width=Inches(6))

    bio = BytesIO()
    document.save(bio)
    bio.seek(0)
    return bio


def save_pdf(text: str, pivots: dict[str, pd.DataFrame]) -> BytesIO:
    """Save text, pivot tables and charts as a PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in text.split("\n"):
        pdf.multi_cell(0, 10, line)

    for title, pivot in pivots.items():
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, title, ln=True)
        pdf.set_font("Arial", size=10)
        col_widths = [80, 30, 30]
        headers = list(pivot.columns)
        for i, h in enumerate(headers):
            w = col_widths[i] if i < len(col_widths) else 30
            pdf.cell(w, 8, str(h), border=1)
        pdf.ln()
        for _, row in pivot.iterrows():
            for i, h in enumerate(headers):
                w = col_widths[i] if i < len(col_widths) else 30
                pdf.cell(w, 8, str(row[h]), border=1)
            pdf.ln()
        img = chart_png(pivot, f"{title} Responses")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(img.getvalue())
            tmp.flush()
            pdf.image(tmp.name, w=180)
        os.unlink(tmp.name)

    bio = BytesIO()
    pdf.output(bio)
    bio.seek(0)
    return bio


def process_free_text(df: pd.DataFrame, free_text_cols: List[str]) -> pd.DataFrame:
    """Concatenate, translate and categorize free-text columns with progress."""
    concat = [
        " ".join(str(row[c]) if pd.notnull(row[c]) else "" for c in free_text_cols)
        for _, row in df.iterrows()
    ]

    translated: List[str] = ["" for _ in concat]
    languages: List[str] = ["" for _ in concat]
    categories: List[str] = ["" for _ in concat]
    token_usage: List[int] = [0 for _ in concat]
    finish_reasons: List[str] = ["" for _ in concat]

    progress = st.progress(0.0, text="Starting...")
    start_time = time.time()
    batch_size = 5

    for start_idx in range(0, len(concat), batch_size):
        batch_texts = concat[start_idx : start_idx + batch_size]

        trans_lang = asyncio.run(async_translate_batch(batch_texts))
        batch_trans = [t for t, _, _, _ in trans_lang]
        batch_langs = [l for _, l, _, _ in trans_lang]
        batch_toks_trans = [tok for _, _, tok, _ in trans_lang]
        batch_finish_trans = [fin for _, _, _, fin in trans_lang]

        batch_cats_data = asyncio.run(async_categorize_batch(batch_trans))
        batch_cats = [cats for cats, _, _ in batch_cats_data]
        batch_toks_cat = [tok for _, tok, _ in batch_cats_data]
        batch_finish_cat = [fin for _, _, fin in batch_cats_data]

        for offset, idx in enumerate(range(start_idx, min(start_idx + batch_size, len(concat)))):
            translated[idx] = batch_trans[offset]
            languages[idx] = batch_langs[offset]
            categories[idx] = ", ".join(batch_cats[offset])
            token_usage[idx] = batch_toks_trans[offset] + batch_toks_cat[offset]
            finish_reasons[idx] = f"{batch_finish_trans[offset]}; {batch_finish_cat[offset]}"

        processed = min(start_idx + batch_size, len(concat))
        rate = (time.time() - start_time) / processed
        remaining = rate * (len(concat) - processed)
        progress.progress(processed / len(concat), text=f"Processing... ETA {int(remaining)}s")

    progress.empty()

    df["Concatenated"] = concat
    df["Translated"] = translated
    df["Language"] = languages
    df["Categories"] = categories
    df["ModelTokens"] = token_usage
    df["FinishReason"] = finish_reasons
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
                try:
                    df = pd.read_csv(BytesIO(raw_bytes), encoding="utf-8")
                except UnicodeDecodeError:
                    st.warning("File is not UTF-8 encoded, attempting latin-1 decoding")
                    df = pd.read_csv(BytesIO(raw_bytes), encoding="latin-1")
            if df.empty:
                st.error("Uploaded file contains no data")
                st.stop()
            if df.isnull().all(axis=0).any():
                st.warning("Some columns contain only missing values")
            if df.isnull().all(axis=1).any():
                st.warning("Some rows contain only missing values")
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

    with st.sidebar.expander("Category descriptions"):
        for cat, desc in CATEGORY_DESCRIPTIONS.items():
            st.write(f"**{cat}** - {desc}")

    if st.button(
        "Process Data",
        help="Translate comments, categorise them and generate summaries."
    ):
        errors = []
        if not user_id_col:
            errors.append("Please select a user ID column.")
        if not location_col:
            errors.append("Please select a location column.")
        if not free_text_cols:
            errors.append("Select at least one free-text column.")
        if not structured_cols:
            errors.append("Select at least one structured column.")
        if errors:
            for msg in errors:
                st.error(msg)
            st.stop()
        with st.spinner("Processing free-text responses..."):
            df = process_free_text(df, free_text_cols)

        st.success("Processing complete")

        df = review_translations(df, user_id_col)
        st.session_state["processed_df"] = df
        df.to_pickle(cache_path)

        nps_col = next((c for c in structured_cols if "nps" in c.lower()), None)
        display_summary(df, nps_col)

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
        display_cols = [
            user_id_col,
            location_col,
            'Concatenated',
            'Translated',
            'Language',
            'Categories',
            'ModelTokens',
            'FinishReason',
            'Flagged',
        ]
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
            segments_to_process = selected_segments if selected_segments else [None]
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for segment in segments_to_process:
                    seg_df = df if segment is None else df[df[location_col] == segment]
                    if seg_df.empty:
                        continue
                    report_text = generate_report(seg_df[[user_id_col, location_col, 'Translated', 'Categories', 'Flagged']])
                    if not report_text:
                        continue
                    segment_title = segment if segment is not None else "All"
                    st.markdown(f"## Report for {segment_title}")
                    st.markdown(report_text)
                    pivot_dict = {
                        col: generate_pivot(seg_df, col) for col in structured_cols
                    }
                    pivot_dict["Category Frequency"] = category_frequency(seg_df)
                    if nps_col and nps_col in seg_df.columns:
                        pivot_dict["NPS Distribution"] = generate_pivot(seg_df, nps_col)
                    docx_file = save_docx(report_text, pivot_dict)
                    pdf_file = save_pdf(report_text, pivot_dict)
                    if len(selected_segments) <= 1:
                        st.download_button(
                            "Download DOCX",
                            docx_file,
                            f"{segment_title}_report.docx",
                            help="Save the report as a Word document."
                        )
                        st.download_button(
                            "Download PDF",
                            pdf_file,
                            f"{segment_title}_report.pdf",
                            help="Save the report as a PDF file."
                        )
                    else:
                        zipf.writestr(f"{segment_title}_report.docx", docx_file.getvalue())
                        zipf.writestr(f"{segment_title}_report.pdf", pdf_file.getvalue())
            if len(selected_segments) > 1:
                zip_buffer.seek(0)
                st.download_button(
                    "Download Reports ZIP",
                    zip_buffer,
                    "reports.zip",
                    help="Download all segment reports as a ZIP file."
                )
else:
    st.info("Upload a survey file to begin.")
