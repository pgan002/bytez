# PDF structure extraction instructions

## Core Objectives
1. Extract nested document structure from content chunks
2. Preserve heading hierarchies across page boundaries
3. Identify continuations when sections span multiple chunks

## Block types
- paragraph: Continuous body of text (not a heading, caption, footnote etc.).
- title: Paper title (first block of page 1)
- authors: Authors list with any affiliations and addresses (only on page 1, usually just below the title).
- heading: Name of a top-level or nested section; e.g.: 'Abstract', '2 Introduction', 'Section 2.1', '1.B. Prior work'.
- image: base64-encoded image data
- code: Formatted text; e.g.: pseudocode, program code, log.
- caption: Label+description of a figure, table or similar; e.g., 'Figure 1: System diagram'
- reference: Citation entry (in References section).
- formula: Numbered equation or symbolic expression; e.g.: `s = S(t) = <t, P(t)>                                 [1]`
- table: rows/columns data. Reformat for alignment.
- footnote: Page-bottom annotation linked from the body
- footer: bottom-most snippet, e.g. page number
- header: top-most snippet, e.g. page number, repeating content, publisher info.
- print_notice: Publication venue (first page bottom)
- toc: Table of contents

## Continued sections
Set key `"continued": true`when section spans multiple chunks.

## Output format (shortened)
```json
{
  "title": "Document Title (first heading on page 1)",
  "sections": [
    {
      "heading": "Formal Heading Text",
      "level": 1|2|3|4,
      "content": [
        "type": "paragraph|image|table|formula|authors|code|header|footer|print_notice|toc",
        // Paragraphs, authors, header, footer, footnote, print_notice, toc: "content": <text>
        // Images: "content": <b64-encoded>, "caption": <text>
        // Tables, code: "content": <formatted row/column text>, "caption": <text>
      ],
      "sections": [...],
      "continued": bool // true if section spans multiple chunks
    }
  ]
}
```

## Example output (shortened)
```json
{
  "title": "Neural Networks",
  "sections": [
    {
      "title": "1. Introduction",
      "level": 1,
      "content": [
        {"type": "paragraph", "content": "Deep learning..."},
        {"type": "image", "content": "Xa4nnlam...", "caption": "Figure 1: Architecture"}
      ],
      "sections": [
        {
          ...,
          "continued": true
        },
      ],
    }
  ]
}
```
