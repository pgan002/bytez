# Challenge A
- Create a Python or Node.js server that responds with "hello world" when
the "/" endpoint is hit

# Challenge B
- Update the endpoint to accept a PDF file upload and return the number of
pages in the document

# Challenge C
- Update the endpoint to accept a link to an Arxiv research paper (link:https://arxiv.org/pdf/2101.08809) and
return the text content of each page as a JSON array
- Example response => `{ “text”: [“page 1 text”, “page 2 text”, ...] }`

# Challenge D
- Implement a rule-based engine to classify content blocks within each page
of the PDF using these [predefined classes](https://human-in-the-loop.bytez.com/edit/arxiv/2101.08809) (see Cheat Sheet). Return the
classifications as JSON.
- Example JSON schema => `{ “output”: [{ “title”: “Abstract”, ... }, {“title”:
“Introduction” ... }, {...} ] }`

# Challenge E
- Improve your software to enhance the overall parsing quality of each page
and also extract tables from the PDF as both images and text, and return
those in your JSON response.
- Note: To accomplish table extraction, you may either write your own
software, use closed/open source software, or use open/closed models

# Challenge F
- Replace your rules-engine with a DNN, LLM, or any combo models. You
may train your own model. Return the classifications as your JSON
response

# Challenge G
- Update your software to meet or exceed the performance on the provided
dataset of papers and their corresponding JSON output.
- The dataset can be downloaded with the following command
  - `gsutil -m cp -r gs://cdn.bytez.com/technical-assessment-dataset`
