import json
import logging
import os
import sys
from pathlib import Path
from typing import Literal

from google import genai
from google.genai.types import GenerateContentConfig
from pydantic import BaseModel, validator, Field, ValidationError

from .chunking import chunk_by_semantic_units


class ContentBlock(BaseModel):
    type: Literal[
        'paragraph', 'image', 'table', 'formula', 'code', 'reference',
        'header', 'footer', 'print_notice', 'toc', 'authors'
    ]
    content: str = ''
    caption: str | None = None  # For image/table/code


class DocumentSection(BaseModel):
    type: Literal['section']
    title: str
    level: int = Field(ge=1, le=4)
    content: list[ContentBlock]
    sections: list['DocumentSection'] = Field(default_factory=list)
    continued: bool = False


class StructuredDocument(BaseModel):
    title: str
    sections: list[DocumentSection]

    @validator('sections')
    def check_continuations(cls, v):
        for i, section in enumerate(v):
            if i == 0 and section.continued:
                raise ValidationError('First section cannot be continuation')
        return v


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


def process_chunk(chunk: dict) -> dict:
    """
    Processes a chunk while maintaining heading relationships.
    Returns structure with placeholders for cross-chunk sections.
    """
    hierarchy_context = '\n'.join(
        f"{'  '*(h['level']-1)}- {h['text']}"
        for h in chunk['hierarchy']
    )
    prompt = f"""
    Current heading hierarchy:
    {hierarchy_context}

    Content:
    {json.dumps(chunk['content'])}
    """
    token_count = llm_client.models.count_tokens(model=LLM_NAME, contents=prompt)
    if token_count.total_tokens > MAX_TOKENS:
        raise ValueError(f'Input exceeds token limit: {token_count.total_tokens} > {MAX_TOKENS}')
    response = llm_client.models.generate_content(
        model=LLM_NAME,
        contents=prompt,
        config=gemini_config,
    )
    result = json.loads(response.text)
    result['meta'] = {
        'start_headings': chunk['hierarchy'],
        'pages': chunk['pages']
    }
    return result


def assemble_hierarchical_structure(chunk_results: list[dict]) -> dict:
    """
    Merges chunks while resolving:
    - Continued subsections
    - Nested heading relationships
    - Cross-chunk references
    """
    document = {}
    section_stack = []  # Tracks open sections

    for chunk in chunk_results:
        if not document.get('title'):
            document['title'] = chunk['title']
        for section in chunk['sections']:
            level = section.get('level', 1)
            # Close completed sections from previous chunks
            while section_stack and section_stack[-1]['level'] >= level:
                closed_section = section_stack.pop()
                if not section_stack:
                    if 'sections' not in document:
                        document['sections'] = []
                    document['sections'].append(closed_section)
            # Handle continued sections
            if section.get('continued'):
                if section_stack:
                    section_stack[-1]['sections'].extend(section['content'])
                continue
            # Add new section
            if section_stack:
                section_stack[-1].setdefault('sections', []).append(section)
            else:
                if 'sections' not in document:
                    document['sections'] = []
                document['sections'].append(section)
            section_stack.append(section)
    # Close any remaining open sections
    while section_stack:
        if 'sections' not in document:
            document['sections'] = []
        document['sections'].append(section_stack.pop())
    return document


def analyze_paper_pdf(pdf_bytes: bytes) -> dict:
    chunks = chunk_by_semantic_units(pdf_bytes)
    document = {}
    for retry_ix in range(MAX_RETRIES):
        chunk_results = []
        for chunk in chunks:
            result = process_chunk(chunk)
            chunk_results.append(result)
        document = assemble_hierarchical_structure(chunk_results)
        try:
            StructuredDocument.validate(document)
            return document
        except ValidationError as e:
            logging.error(f'Structure validation failed: {e}')
    return document


def analyze() -> dict:
    if sys.argv[1:]:
        pdf_bytes = Path(sys.argv[1]).read_bytes()
    else:
        pdf_bytes = sys.stdin.buffer.read()
    return analyze_paper_pdf(pdf_bytes)
