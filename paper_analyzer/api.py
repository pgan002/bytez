from io import BytesIO

import PyPDF2
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from paper_analyzer.analyzer import analyze

app = FastAPI()


class PaperRequest(BaseModel):
    url: str


@app.post('/extract-text')
async def extract_text(request: PaperRequest):
    url = request.url
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = BytesIO(response.content)
        page_texts = analyze(content)
        return {'text': page_texts}
    except requests.RequestException:
        msg = 'Failed to download the PDF from the store'
        raise HTTPException(status_code=400, detail=msg)
    except PyPDF2.errors.PdfReadError:
        raise HTTPException(status_code=400, detail='Invalid PDF content')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/')
async def read_root():
    return 'hello world'
