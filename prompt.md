You are given a PDF page from a research paper and its extracted text. Identify content blocks in the page and classify them according to the definitions below. Do not omit or introduce any new content, except for spacing for readability; for example, you may add a space after a comma or . All the text and images in the input must be in the output and vice versa. Output the blocks as a JSON list of objects keyed by bloc type. Use only the keys (block types) defined below. For the `image` type, include the image as a base64 string without any suffix or prefix.

# Block types

## paragraph
Text that comprises the majority of a document; the most non unique text in a document. It does not relay structural or ancillary information, describe an image or have visual content; its only purpose is to deliver textual information. Individual paragraphs are separated by blank lines. A bullet point of multiple lines is a separate paragraph; so is a phrase announcing a bullet list (unless it is a sub-heading).

## title
The title of the paper. Always at the start of page 1.

## authors
The list of authors, often with their email addresses or affiliations. Include all authors and their information. Only and always on page 1, usually immediately below the title.

## heading
Stands by itself (not in a paragraph), names a top-level "section" of a paper; may start with a single section number or letter. Examples: "Abstract", "1. Introduction", "Section A", "Section III", "References", "Appendix".

## sub-heading
Stands by itself (like Heading) and names a section that is not a top-level section (unlike Heading). Examples: "Section 2.1", "1.B. Prior work", "Section 3.a.".

## image
Visual content such as a diagram or photo, including any textual elements in it, but not the caption. Use the image's raw base64-encoded string as the value for key `image`; do not add any prefix, suffix. Add the image in a separate output object from its caption.

## code
Structured text such as pseudocode, Python, SQL, HTML, JSON, log text etc.

## caption
Names and describes an image, table, algorithm or similar. Appears immediately above, below or beside the object it describes. Includes a name, which typically starts with "Figure", "Table", "Listing" etc., followed by a number and a description.

## reference
A whole block that refers to another work, and is not contained in a paragraph. Almost always occurs in the References section of a paper, which is one of the last sections (usually the last). Usually contains the work's name, author names and year of publication.

## formula
Symbolic expression, such as a mathematical or chemical formula, separated from a paragraph and often in a different font. Often ends with a number that refers to it. Example:
```
                        s = S(t) = <t, P(t)>                                 [1]
```

## table
Text organized in rows and columns, often with lines outlining the rows and columns. Usually has a header row or column. If unsure between image and table, prefer table.

## footnote
Special text at the bottom of a page used to expand upon material referred to in the body of the document.

## footer
At the very bottom of a page; often is a page number.

## header
At the very top of the page. Sometimes contains the page number or publisher information.

## print notice
Marks the journal or conference that the paper was published to. Usually at the bottom of the first page.

## toc
Table of contents.


# Example output format
In the example below, `...` indicates that the output was truncated or omitted in the example but your output should not be truncated.

```
[
  {"title": "PyGlove: Symbolic Programming for Automated Machine Learning"},
  {"authors": "Daiyi Peng, Xuanyi Dong, ...Google Research, Brain Team, {daiyip, ereal, tanmingxing, yifenglu"},
  {"heading": "Abstract"},
  {"paragraph": "Neural networks are sensitive to hyper-parameter..."},
  {"heading": "1 Introduction"},
  {"paragraph": "Neural networks are sensitive..."},
  {"footnote": "∗Work done as a research intern at Google."},
  {"footer": "34th Conference on Neural Information..."},
  ...,
  {"sub-heading": "2.1 AutoML as an Automated Symbolic Manipulation Process"},
  {"paragraph": "AutoML can be interpreted..."},
  {"image": "iVBORw0KGgoAAAANSUhEUgAAA..."},
  {"caption": "Figure 1: AutoML as an automated..."},
  ...
  {"caption": "Table 1: The development cost..."},
  {"table": "+-----------------------+-------------------------+-------------------------+\n| Projects              | Original\nlines of code | Modified\nlines of code |\n|-----------------------+-------------------------+-------------------------|\n| PyTorch ResNet [36]   |                     353 |                      15 |\n|-----------------------+-------------------------+-------------------------|\n| TensorFlow MNIST [37] |                     120 |                      24 |\n+-----------------------+-------------------------+-------------------------+"},
  ...
  {"heading": "References"},
  {"reference": "[1] Hieu Pham, Melody Y Guan, Barret Zoph,..."},
  ...
  {"heading": "Appendix"},
  {"paragraph": "The appendix provides ..."},
  ...
  {"section": "A   More on Symbolic Programming for AutoML"},
  {"sub-section": "A.1 Formal definition of a symbolic program"},
  ...
  {"formula": "s = S(t) = 〈t, P (t)〉 (1)"}
]
```
