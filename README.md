# NPS Survey Analyzer

This repository contains a simple Streamlit application for analyzing NPS survey results with help from OpenAI's **GPT-4o-mini** model. The app allows non-technical users to upload survey data, translate free-text comments to English, categorize them, generate pivot tables for structured questions, and create a narrative report.
The question **"1: How likely are you to recommend Twinkl to a friend or colleague?"** is automatically used to calculate the Net Promoter Score.

## Features

- Upload CSV or Excel survey data.
- Select columns for User ID, location, structured questions and free-text responses.
- Automatic translation of comments to English using GPT-4o-mini.
- AI-driven categorization into a predefined list of categories.
- Pivot tables with percentages and bar charts for structured questions.
- Binary multi-select columns with values 0 or 1 are grouped into a single pivot table.
- High-level summary dashboard showing NPS score, distribution, category frequency and sentiment ratio.
- Displays the number of rows after filters are applied.
- These KPIs and charts are shown before the detailed report for quick insight.
- Downloadable results and pivot tables.
- Use the **Download Charts PDF** button to save all graphs with their question titles.
- Use the **Download Tables PDF** button to save each pivot table with its question text.
- A second **Download Charts PDF** button appears after processing so you can download the graphs at the end as well.
- Use the **Download Everything PDF** button to save all charts, tables and the report in one file.
- Generate a narrative report and download it as a DOCX or via **Download Everything PDF**.
- Filter data by multiple segment columns at once (e.g., Country and Career Type).
- Quickly apply predefined segment filters such as **UK Parents** or **US Teachers**.
- Filters are applied before translation and analysis to save time and API usage.
- Reports include pivot tables and bar chart images.
- When multiple segments are selected, generate a report for each and download all DOCX/PDF files in a ZIP.
- Progress bars for long-running translation and categorization tasks.
- Uses OpenAI's async client for faster batch processing.
- Expandable comments for spot-checking AI results.
- Language detection stored alongside translations.
- Categories are generated for the original text and for the English
  translation with editable reasoning.
- Intermediate results saved after each processing batch.
- Automatically resume processing from the last completed row on startup.
- Clear cached data for the uploaded survey using the **Clear Cached Data** button.
- Toggle to switch all text to black and buttons to blue.

## Requirements

- Python 3.12
- An OpenAI API key set as the environment variable `OPENAI_API_KEY`.
- `openai` package version 1.0 or newer for the async client.

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
2. **OpenAI API errors** – ensure the `OPENAI_API_KEY` environment variable is set. The app now
   shows more descriptive messages for authentication, connection and rate limit
   issues.
3. **Large files** – the uploader accepts files up to 10MB.
4. **Encoding issues** – save your CSV in UTF-8 format.
5. **Stale results** – click **Clear Cached Data** in the sidebar to remove saved progress.

For more help open an issue on GitHub.
