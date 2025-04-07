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


def chunk_by_semantic_units(pdf_bytes: bytes, max_tokens: int = 128000) -> List[Dict]:
    """
    Split PDF into coherent chunks that:
    - Respect section boundaries
    - Stay under token limits
    - Include context carryover
    """
    doc = pymupdf.open(stream=pdf_bytes)
    chunks = []
    current_chunk = {
        'pages': [],
        'headings': [],
        'content': []
    }

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        layout = page.get_text('dict')
        for block in layout['blocks']:
            if block['type'] != 0:
                continue  # Skip non-text block
            for line in block['lines']:
                text = ' '.join(span['text'] for span in line['spans'])
                first_span = line["spans"][0]
                level = get_heading_level(first_span)
                if level > 0:  # Heading
                    # Close chunk if new top-level section starts
                    if level == 1 and current_chunk["content"]:
                        chunks.append(current_chunk)
                        current_chunk = {
                            'pages': {page_num + 1},
                            'hierarchy': [{'text': text, 'level': level}],
                            'content': [{'type': 'heading', 'text': text, 'level': level}]
                        }
                    else:
                        # Update hierarchy stack
                        while (current_chunk['hierarchy'] and
                                current_chunk['hierarchy'][-1]['level'] >= level):
                            current_chunk['hierarchy'].pop()
                        current_chunk['hierarchy'].append({'text': text, 'level': level})
                        current_chunk['content'].append(
                            {'type': 'heading', 'text': text, 'level': level}
                        )
                else:
                    current_chunk['content'].append(
                        {'type': 'paragraph', 'text': text}
                    )
                current_chunk['pages'].add(page_num + 1)

                # Split if approaching token limit
                if len(json.dumps(current_chunk)) > max_tokens * 3.5:
                    chunks.append(current_chunk)
                    # Carry over last 2 heading levels
                    current_chunk = {
                        'pages': {page_num + 1},
                        'hierarchy': current_chunk['hierarchy'][-2:],
                        'content': current_chunk['content'][-3:]  # Last para + headings
                    }

    if current_chunk['content']:
        chunks.append(current_chunk)

    # Convert page sets to sorted lists
    for chunk in chunks:
        chunk['pages'] = sorted(chunk['pages'])

    return chunks
