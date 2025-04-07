Development challenge by Bytez.com.
See [instructions](file:///challenge.md)

# Installing

1. Install Python 3
1. Install Poetry
1. Run `poetry install`
1. Run `export GEMINI_API_KEY=<...>` replacing `...` by your Google Gemini API key

# Running

1. Run `poetry run uvicorn paper_analyzer.api:app --reload`
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
