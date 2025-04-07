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


def process_hierarchical_chunk(chunk: Dict) -> Dict:
    """
    Processes a chunk while maintaining heading relationships.
    Returns structure with placeholders for cross-chunk sections.
    """
    hierarchy_context = "\n".join(
        f"{'  '*(h['level']-1)}- {h['text']}"
        for h in chunk["hierarchy"]
    )

    prompt = f"""
    Current Heading Hierarchy:
    {hierarchy_context}

    Continue analyzing this section and its subsections.
    For incomplete sections, use <CONTINUED> markers.

    Content:
    {json.dumps(chunk['content'][:200])}
    """

    response = genai.generate_content(
        system_instruction=Path("prompt.md").read_text(),
        contents=[prompt],
        generation_config={
            "temperature": 0.2,
            "response_mime_type": "application/json"
        }
    )

    result = json.loads(response.text)
    result["meta"] = {
        "start_headings": chunk["hierarchy"],
        "pages": chunk["pages"]
    }
    return result


def assemble_hierarchical_structure(chunk_results: List[Dict]) -> Dict:
    """
    Merges chunks while resolving:
    - Continued subsections
    - Nested heading relationships
    - Cross-chunk references
    """
    document = {'sections': []}
    section_stack = []  # Tracks open sections across chunks

    for chunk in chunk_results:
        for section in chunk['structure']['sections']:
            current_level = section.get('level', 1)

            # Close completed sections from previous chunks
            while section_stack and section_stack[-1]['level'] >= current_level:
                closed_section = section_stack.pop()
                if not section_stack:
                    document['sections'].append(closed_section)

            # Handle continued sections
            if '<CONTINUED>' in section['title']:
                if section_stack:
                    section['title'] = section['title'].replace('<CONTINUED>', "")
                    section_stack[-1]['subsections'].append(section)
            else:
                if section_stack:
                    section_stack[-1]['subsections'].append(section)
                else:
                    document['sections'].append(section)

            section_stack.append(section)

    # Close any remaining open sections
    while section_stack:
        document['sections'].append(section_stack.pop())
    return document


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
