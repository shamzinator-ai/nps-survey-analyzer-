# NPS Survey Analyzer

This repository contains a simple Streamlit application for analyzing NPS survey results with help from OpenAI's **GPT-4o-mini** model. The app allows non-technical users to upload survey data, translate free-text comments to English, categorize them, generate pivot tables for structured questions, and create a narrative report.

## Features

- Upload CSV or Excel survey data.
- Select columns for User ID, location, structured questions and free-text responses.
- Automatic translation of comments to English using GPT-4o-mini.
- AI-driven categorization into a predefined list of categories.
- Pivot tables with percentages and bar charts for structured questions.
- Downloadable results and pivot tables.
- Generate a narrative report and download it as a DOCX or PDF file.
- Exported reports include the pivot tables and charts shown in Streamlit.
- Progress bars for long-running translation and categorization tasks.
- Expandable comments for spot-checking AI results.
- Language detection stored alongside translations.

## Requirements

- Python 3.12
- An OpenAI API key set as the environment variable `OPENAI_API_KEY`.
- Matplotlib for saving charts as images.

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Running

```bash
streamlit run app.py
```

Use the sidebar to upload your survey file. The app will guide you through selecting free-text columns, processing translations with progress bars, and generating downloadable pivot tables, charts, and reports.

An example dataset `example_data.csv` is included for testing.
