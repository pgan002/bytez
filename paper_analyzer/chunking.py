import json
from typing import List, Dict

import pymupdf


def get_heading_level(span: dict) -> int:
    if span['size'] > 16:
        return 1  # h1
    if span['size'] > 14:
        return 2  # h2
    if span['flags'] & 2:
        return 3  # h3 (bold)
    return 0


def chunk_by_semantic_units(pdf_bytes: bytes, max_tokens: int = 128_000) -> List[Dict]:
    """
    Split PDF into coherent chunks that:
    - Respect section boundaries
    - Stay under token limits
    - Include context carryover
    """
    doc = pymupdf.open(stream=pdf_bytes)
    chunks = []
    chunk = {
        'pages': [],
        'headings': [],
        'content': [],
        'hierarchy': []
    }
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        layout = page.get_text('dict')
        for block in layout['blocks']:
            if block['type'] != 0:
                continue  # Skip non-text block
            for line in block['lines']:
                text = ' '.join(span['text'] for span in line['spans'])
                first_span = line['spans'][0]
                level = get_heading_level(first_span)
                if level > 0:  # Heading
                    # Close chunk if new top-level section starts
                    if level == 1 and chunk['content']:
                        chunks.append(chunk)
                        chunk = {
                            'pages': [page_num + 1],
                            'hierarchy': [{'text': text, 'level': level}],
                            'content': [{'type': 'heading', 'text': text, 'level': level}]
                        }
                    else:
                        # Update hierarchy stack
                        while (chunk['hierarchy'] and
                                chunk['hierarchy'][-1]['level'] >= level):
                            chunk['hierarchy'].pop()
                        chunk['hierarchy'].append({'text': text, 'level': level})
                        chunk['content'].append(
                            {'type': 'heading', 'text': text, 'level': level}
                        )
                else:
                    chunk['content'].append(
                        {'type': 'paragraph', 'text': text}
                    )
                if page_num + 1 not in chunk['pages']:
                    chunk['pages'].append(page_num + 1)

                # Split if approaching token limit
                if len(json.dumps(chunk)) > max_tokens * 3.3:
                    chunks.append(chunk)
                    # Carry over last 2 heading levels
                    chunk = {
                        'pages': [page_num + 1],
                        'hierarchy': chunk['hierarchy'][-2:],
                        'content': chunk['content'][-3:]  # Last para + headings
                    }

    if chunk['content']:
        chunks.append(chunk)

    # Convert page sets to sorted lists
    for chunk in chunks:
        chunk['pages'] = sorted(list(chunk['pages']))

    return chunks
