from io import BytesIO
from urllib.parse import urlparse

import PyPDF2
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI()


class ArxivRequest(BaseModel):
    arxiv_url: str


def is_valid_arxiv_url(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.scheme in ('http', 'https') and
        parsed.netloc == 'arxiv.org' and
        parsed.path.startswith('/pdf/')
    )


@app.post('/extract-text')
async def extract_text(request: ArxivRequest):
    arxiv_url = request.arxiv_url
    if not is_valid_arxiv_url(arxiv_url):
        msg = 'Invalid arXiv URL format. '\
            'Expected format: https://arxiv.org/pdf/XXXX.XXXXX'
        raise HTTPException(status_code=400, detail=msg)
    try:
        response = requests.get(arxiv_url)
        response.raise_for_status()
        pdf = PyPDF2.PdfReader(BytesIO(response.content))
        page_texts = [page.extract_text() for page in pdf.pages]
        return {'text': page_texts}
    except requests.RequestException:
        msg = 'Failed to download the PDF from arXiv'
        raise HTTPException(status_code=400, detail=msg)
    except PyPDF2.PdfReadError:
        raise HTTPException(status_code=400, detail='Invalid PDF content')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/')
async def read_root():
    return 'hello world'
