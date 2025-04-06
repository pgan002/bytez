from io import BytesIO

import PyPDF2
import requests
from fastapi import Body, FastAPI, File, HTTPException, UploadFile

from paper_analyzer import analyzer


app = FastAPI()


def _analyze_pdf(content):
    try:
        page_texts = analyzer.analyze(content)
        return {'text': page_texts}
    except PyPDF2.errors.PdfReadError:
        raise HTTPException(400, 'Invalid PDF content')
    #except Exception as e:
    #    raise HTTPException(500, str(e))


@app.post('/analyze/file')
async def analyze_file(file: UploadFile = File(...)):
    if file.content_type != 'application/pdf':
        raise HTTPException(400, f'Expected PDF, got {file.content_type}')
    try:
        content = await file.read()
    finally:
        await file.close()
    return _analyze_pdf(BytesIO(content))


@app.post('/analyze/url')
async def analyze_url(url: str = Body(embed=True)):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(400, f'Download failed: {str(e)}')
    content_type = response.headers['content-type']
    if content_type != 'application/pdf':
        raise HTTPException(400, f'Expected PDF, got {content_type}')
    return _analyze_pdf(BytesIO(response.content))


@app.get('/')
async def read_root():
    return 'hello world'
