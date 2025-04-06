Development challenge by Bytez.com.
See [instructions](file:///challenge.md)

# Installing

1. Install Python 3
1. Install Poetry
1. Run `poetry install`

# Running

1. Run `poetry run uvicorn paper_analyzer.api:app --reload`
1. POST a PDF file to `/page-count` endpoint
    ```
    curl -X POST "http://localhost:8000/extract-text"\
    -H "Content-Type: application/json"\
    -d '{"url": "https://arxiv.org/pdf/2101.08809"}'
    ```
