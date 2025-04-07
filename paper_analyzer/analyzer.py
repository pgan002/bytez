import json
import logging
import os
import sys
from pathlib import Path

import tiktoken
from openai import OpenAI
from pydantic import ValidationError

from .chunking import chunk_by_semantic_units
from .models import StructuredDocument


LLM_NAME = 'gpt-4o-mini'  # Cheap, allows tuning (TODO: tune)
MAX_RETRIES = 3
llm_client = client = OpenAI()
MAX_TOKENS = 16_384  # Output limit. Output size will be similar to input size.
with open('prompt.md') as f:
   SYSTEM_PROMPT = f.read()
encoding = tiktoken.encoding_for_model(LLM_NAME)


def call_llm(prompt: str) -> dict:
    llm_response = None
    error = None
    for _ in range(MAX_RETRIES):
        try:
            completion = llm_client.chat.completions.create(
                model=LLM_NAME,
                messages=[
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': prompt}
                ],
                response_format={'type': 'json_object'}
            )
            llm_response = completion.choices[0].message.content
            return json.loads(llm_response)
        except Exception as e:
            logging.error(f'LLM call failed: {e}')
            error = e
    return {'error': str(error), 'llm_response': llm_response}


def process_chunk(chunk: dict) -> dict:
    """
    Processes a chunk while maintaining heading relationships.
    Returns structure with placeholders for cross-chunk sections.
    """
    hierarchy_context = '\n'.join(
        f"{'  '*(h['level']-1)}- {h['text']}"
        for h in chunk['hierarchy']
    )
    content = json.dumps(chunk['content'])
    prompt = f"""
    Current hierarchy:
    {hierarchy_context}

    Content:
    {content}
    """
    n_tokens = len(encoding.encode(content))
    if n_tokens > MAX_TOKENS:
        pages = chunk.get('pages')
        ix = pages[-1] if pages else None
        msg = f'Page {ix} chunk exceeds our token limit: {n_tokens} > {MAX_TOKENS}'
        #raise ValueError(msg)
        logging.error(msg)
    result = call_llm(prompt)
    result['meta'] = {
        'start_headings': chunk['hierarchy'],
        'pages': chunk['pages']
    }
    if n_tokens > MAX_TOKENS:
        result['error'] = f'Chunk exceeds our token limit {MAX_TOKENS}'
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
    chunks = chunk_by_semantic_units(pdf_bytes, max_tokens=MAX_TOKENS)
    document = {}
    error = None
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
            error = e
    document['error'] = error
    return document


def analyze() -> dict:
    if sys.argv[1:]:
        pdf_bytes = Path(sys.argv[1]).read_bytes()
    else:
        pdf_bytes = sys.stdin.buffer.read()
    return analyze_paper_pdf(pdf_bytes)
