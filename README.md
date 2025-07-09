# NPS Survey Analyzer

This repository contains a simple Streamlit application for analyzing NPS survey results with help from OpenAI's **GPT-4o-mini** model. The app allows non-technical users to upload survey data, translate free-text comments to English, categorize them, generate pivot tables for structured questions, and create a narrative report.

## Features

- Upload CSV or Excel survey data.
- Select columns for User ID, location, structured questions and free-text responses.
- Automatic translation of comments to English using GPT-4o-mini.
- AI-driven categorization into a predefined list of categories.
- Pivot tables with percentages and bar charts for structured questions.
- High-level summary dashboard showing NPS distribution, category frequency and sentiment ratio.
- Downloadable results and pivot tables.
- Generate a narrative report and download it as a DOCX or PDF file.
- Reports include pivot tables and bar chart images.
- When multiple segments are selected, generate a report for each and download all DOCX/PDF files in a ZIP.
- Progress bars for long-running translation and categorization tasks.
- Expandable comments for spot-checking AI results.
- Language detection stored alongside translations.
- Intermediate results saved after each processing batch.
- Automatically resume processing from the last completed row on startup.

## Requirements

- Python 3.12
- An OpenAI API key set as the environment variable `OPENAI_API_KEY`.

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

## Troubleshooting

If the app fails to start or behaves unexpectedly, try the following:

1. **Missing dependencies** – install them with `pip install -r requirements.txt`.
2. **OpenAI API errors** – ensure the `OPENAI_API_KEY` environment variable is set.
3. **Large files** – the uploader accepts files up to 10MB.
4. **Encoding issues** – save your CSV in UTF-8 format.

For more help open an issue on GitHub.
