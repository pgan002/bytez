from fastapi import FastAPI, UploadFile, File, HTTPException
import PyPDF2
from io import BytesIO


app = FastAPI()

@app.get('/')
async def read_root():
    return 'hello world'


@app.post('/page-count')
async def count_pages(file: UploadFile = File(...)):
    if file.content_type != 'application/pdf':
        raise HTTPException(status_code=400, detail='File must be a PDF')
    try:
        contents = await file.read()
        pdf = PyPDF2.PdfReader(BytesIO(contents))
        return len(pdf.pages)
    except PyPDF2.PdfReadError:
        raise HTTPException(status_code=400, detail='Invalid PDF file')
    finally:
        await file.close()
