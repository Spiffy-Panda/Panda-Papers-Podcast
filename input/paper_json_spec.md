# Paper JSON Encoding Spec

This spec defines the format for encoding academic papers as structured JSON, as exemplified by `great_plea_paper.json`.

---

## Top-Level Structure

```json
{
  "meta": { ... },
  "sections": [ ... ]
}
```

The document is a single JSON object with exactly two keys: `meta` and `sections`.

---

## `meta` Object

Bibliographic metadata for the paper. All fields are strings unless noted.

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | yes | Full paper title, exactly as published |
| `authors` | string[] | yes | Ordered list of author names as "First Last" |
| `journal` | string | yes | Publication venue name |
| `year` | integer | yes | Publication year |
| `doi` | string | yes | DOI without URL prefix, e.g. `"10.1038/s41746-023-00965-x"` |
| `pmcid` | string | no | PubMed Central ID if available, e.g. `"PMC10693640"` |
| `source_url` | string | yes | Canonical URL used to access the paper |
| `license` | string | yes | License under which the paper is published, e.g. `"CC BY 4.0"` |

**Example:**
```json
"meta": {
  "title": "Adopting and Expanding Ethical Principles for Generative Artificial Intelligence from Military to Healthcare",
  "authors": ["Alice Smith", "Bob Jones"],
  "journal": "Nature Medicine",
  "year": 2024,
  "doi": "10.1038/example",
  "pmcid": "PMC12345678",
  "source_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC12345678/",
  "license": "CC BY 4.0"
}
```

---

## `sections` Array

An ordered array of section objects following the paper's structure from top to bottom. The abstract is always the first section.

### Section Object

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Kebab-case slug uniquely identifying the section within the document |
| `title` | string | yes | Section heading as it appears in the paper |
| `paragraphs` | Paragraph[] | yes | Ordered list of paragraphs in the section |

**`id` conventions:**
- Use lowercase kebab-case: `"introduction"`, `"risks-and-challenges"`, `"principle-governability"`
- The abstract section always uses `id: "abstract"`
- For principle/subsection sections, prefix with the parent concept: `"principle-equity"`, `"principle-privacy"`
- Must be unique across all sections in the document

### Paragraph Object

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | integer | yes | Globally unique integer ID, sequential from 1 across the entire document |
| `text` | string | yes | Paragraph content (see Paragraph Text guidelines below) |

**`id` conventions:**
- Paragraph IDs are **global**, not per-section — the first paragraph in the document is `1`, and numbering continues uninterrupted across all sections
- IDs must be strictly sequential with no gaps

---

## Paragraph Text Guidelines

Paragraphs are **faithful summaries**, not verbatim transcriptions. The goal is to preserve the intellectual content and argumentative structure of the source while:

- Condensing multiple related sentences into one paragraph where appropriate
- Omitting pure boilerplate, acknowledgements, funding disclosures, and citation lists
- Preserving specific named entities: organizations, model names, frameworks, defined terms, acronyms
- Preserving numerical claims, statistics, and quantitative findings
- Retaining the paper's own definitions and framings (e.g. `"Reliability is defined as..."`)
- Writing in third person, attributing claims to "the authors" or "the paper"

**What to omit:**
- Figure and table captions (figures and tables are not encoded)
- In-text citation markers like `[1]`, `(Smith et al., 2020)`
- Footnotes
- Acknowledgements, funding, conflict of interest, and data availability sections
- Reference list / bibliography

---

## Section Ordering

Sections appear in document reading order:

1. `abstract`
2. `introduction`
3. Body sections (in paper order)
4. `conclusion`

If a paper has subsections that are each substantive (e.g. one section per principle), each subsection becomes its own section object. If subsections are brief or purely organizational, they may be collapsed into a single parent section.

---

## Complete Minimal Example

```json
{
  "meta": {
    "title": "Example Paper Title",
    "authors": ["Jane Doe", "John Smith"],
    "journal": "Journal of Examples",
    "year": 2024,
    "doi": "10.0000/example.2024",
    "source_url": "https://example.com/paper",
    "license": "CC BY 4.0"
  },
  "sections": [
    {
      "id": "abstract",
      "title": "Abstract",
      "paragraphs": [
        { "id": 1, "text": "This paper examines..." },
        { "id": 2, "text": "The authors propose..." }
      ]
    },
    {
      "id": "introduction",
      "title": "Introduction",
      "paragraphs": [
        { "id": 3, "text": "Background context..." },
        { "id": 4, "text": "The problem addressed..." }
      ]
    },
    {
      "id": "conclusion",
      "title": "Conclusion",
      "paragraphs": [
        { "id": 5, "text": "The authors conclude..." }
      ]
    }
  ]
}
```

---

## Validation Checklist

Before finalizing a paper JSON file:

- [ ] All `meta` required fields are present
- [ ] `authors` is an array (even for single-author papers)
- [ ] `year` is an integer, not a string
- [ ] All section `id` values are unique kebab-case strings
- [ ] Paragraph `id` values are globally sequential integers starting at 1 with no gaps
- [ ] No verbatim long passages are reproduced from the source
- [ ] References, acknowledgements, and figure captions are omitted
- [ ] Abstract is the first section with `id: "abstract"`
