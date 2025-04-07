import base64
import json
import os
import re
import sys
from io import BytesIO
from pathlib import Path
from typing import Literal, Union

import pymupdf
from google import genai
from google.genai.types import GenerateContentConfig
from pydantic import BaseModel, field_validator, Field, ValidationError


ContentBlockType = Literal[
    'paragraph',
    'title',
    'authors',
    'heading',
    'sub-heading',
    'image',
    'code',
    'caption',
    'reference',
    'formula',
    'table',
    'footnote',
    'footer',
    'header',
    'print notice',
    'toc'
]


class ContentBlock(BaseModel):
    type: ContentBlockType = Field(..., description='Type of content block')
    content: Union[str, bytes] = Field(
        ...,
        description='Block content (text or base64-encoded image)'
    )

    @classmethod
    @field_validator('content')
    def validate_content(cls, v, values):
        block_type = values.data.get('type')
        if block_type == 'image':
            if isinstance(v, str):
                try:
                    return base64.b64decode(v)  # Decode base64 strings to bytes
                except ValueError:
                    raise ValueError('Invalid base64 encoding for image')
            elif not isinstance(v, bytes):
                raise ValueError('Image content must be base64 string or bytes')
            return v

        if not isinstance(v, str):
            raise ValueError(f'Content for {block_type} must be text')
        return v

    def json(self, **kwargs):
        # Custom JSON serialization to handle bytes
        if self.type == 'image' and isinstance(self.content, bytes):
            model_copy = self.model_copy()
            model_copy.content = base64.b64encode(self.content).decode('utf-8')
            return super(ContentBlock, model_copy).json(**kwargs)
        return super().json(**kwargs)


LLM_NAME = 'gemini-1.5-flash-8b'  # Cheap, allows tuning (TODO: tune)
MAX_RETRIES = 3
llm_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
MAX_TOKENS = 8_192  # Output limit. Output size will be similar to input size.
with open('prompt.md') as f:
   SYSTEM_PROMPT = f.read()
gemini_config = GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    response_mime_type='application/json',
    #response_schema=list[ContentBlock]
)


def call_gemini_api(page_number: int, total_pages: int, text: str, pdf: pymupdf.Page) -> str:
    try:
        user_prompt = f'Page {page_number} of {total_pages}\n\n'\
            f'# Text\n{text}\n\n'\
            f'# PDF\n{pdf.read_contents()}'
        token_count = llm_client.models.count_tokens(model=LLM_NAME, contents=text)
        if token_count.total_tokens > MAX_TOKENS:
            raise ValueError(f'Input text exceeds maximum token limit: {token_count.total_tokens} > {MAX_TOKENS}')
        response = llm_client.models.generate_content(
            model=LLM_NAME,
            contents=user_prompt,
            config=gemini_config,
        )
        return response.text
    except Exception as e:
        return f'Error processing page: {str(e)}'


def extract_content_blocks(llm_response: str, page_text: str) -> list[dict[str, str]]:
    """Validate content blocks against the schema and the page text"""
    normalized_page_text = re.sub(r'\s+', ' ', page_text.strip().lower())
    raw_data = json.loads(llm_response)
    if not isinstance(raw_data, list):
        raise ValueError('Response is not a list')
    validated_blocks = []
    errors = []
    normalized_block_texts = []
    for i, item in enumerate(raw_data):
        try:
            block_type, content = next(iter(item.items()))
            block = ContentBlock(type=block_type, content=content)
            validated_blocks.append(item)
            if block_type != 'image':
                normalized_block_text = re.sub(r'\s+', ' ', content.strip().lower())
                if normalized_block_text not in normalized_page_text:
                    item['error'] = 'Not found in page text'
                normalized_block_texts.append(normalized_block_text)
        except ValidationError as e:
            validated_blocks.append({'error': str(e), 'original_text': item})
            errors.append(f'Item {i}: {str(e)}')
    if errors and not validated_blocks:
        raise ValueError('All blocks invalid:\n' + '\n'.join(errors))

    # TODO Check all page text is covered by blocks (excluding images)
    #if combined_block_text not in normalized_page_text: ...
    return validated_blocks


def analyze_page(page_number: int, total_pages: int, page_pdf: pymupdf.Page):
    text = page_pdf.get_text()
    result = []
    for _ in range(MAX_RETRIES):
        llm_response = call_gemini_api(page_number, total_pages, text, page_pdf)
        try:
            return extract_content_blocks(llm_response, text)
        except (json.JSONDecodeError, ValueError, ValidationError) as e:
            result = [{
                'error': str(e),
                'original_response': llm_response
            }]
    return result


def analyze_paper_pdf(pdf_bytes: BytesIO) -> list[str]:
    results = []
    pdf = pymupdf.open(stream=pdf_bytes, filetype='pdf')
    total_pages = len(pdf)
    for i, page_pdf in enumerate(pdf.pages(), 1):
        blocks = analyze_page(i, total_pages, page_pdf)
        results.extend(blocks)
    return results


def analyze() -> list[str]:
    if sys.argv[1:]:
        pdf_bytes = Path(sys.argv[1]).read_bytes()
    else:
        pdf_bytes = sys.stdin.buffer.read()
    return analyze_paper_pdf(pdf_bytes)
