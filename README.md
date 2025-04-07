Development challenge by Bytez.com.
See [instructions](file:///instructions.md)

# Installing

1. Install Python 3
1. Install Poetry
1. Run `poetry install`
1. Run `export GEMINI_API_KEY=<...>` replacing `...` by your Google Gemini API key

# Running

There are three ways to run the software:
1. Start the HTTP server: `poetry run uvicorn paper_analyzer.api:app --reload`; then either:
  1. POST a paper URL to endpoint `/analyze-url`
    ```
    curl -X POST 'http://localhost:8000/analyze/url'\
    -d '{"url": "https://arxiv.org/pdf/2101.08809"}'\
    -H 'Content-Type: application/json'
    ```
  1. POST a paper PDF file to endpoint `/analyze/file`
    ```
    curl -X POST 'http://localhost:8000/analyze-file'\
    -F 'file=@data/97479/paper.pdf'
    ```
1. Directly run the Python script
    ```
    poetry run analyze data/97479/paper.pdf
    ```
