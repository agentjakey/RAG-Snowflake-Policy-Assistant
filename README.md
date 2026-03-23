# RAG Policy Assistant — Snowflake Cortex + Streamlit

A retrieval-augmented generation (RAG) system built entirely inside Snowflake using
Cortex Search and Cortex LLM, with a Streamlit UI for querying and uploading internal policy documents.

Built for American Refrigeration to allow employees to ask natural language questions
about SOPs, safety procedures, and internal policies with answers grounded in
source documents and citations. Important for high stakes environments that require safety and strict protocols, where LLM hallucinations could be drastic.

---

## Demo

**Querying a safety policy:**

![alt text](<Screenshot 2026-02-08 165946.png>)

**Cited source chunks from the indexed PDF:**

![alt text](<Screenshot 2026-02-08 165931.png>)

---

## What It Does

1. **Ingest** - Upload policy PDFs via a Streamlit app into a Snowflake internal stage
2. **Parse** - Snowflake Cortex parses each PDF into structured text
3. **Chunk** - Text is split into overlapping chunks (1800 chars, 250 overlap)
4. **Index** - A Cortex Search Service indexes all chunks for semantic search
5. **Query** - A Streamlit assistant retrieves relevant chunks and optionally
   summarizes them with an LLM (`snowflake-arctic`)

All compute, storage, and inference runs inside Snowflake. There are no external API keys nor
external vector databases/infrastructure.

---

## Architecture
```
PDF Upload (Streamlit)
        ↓
@PDF_STAGE_RAW  (Snowflake internal stage)
        ↓
CORTEX.PARSE_DOCUMENT  →  PARSED_POLICY_DOCS
        ↓
CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER  →  POLICY_DOC_CHUNKS
        ↓
CORTEX SEARCH SERVICE: POLICY_DOCS_SEARCH
        ↓
Streamlit Assistant
    ├── Summary mode   →  CORTEX.COMPLETE (snowflake-arctic)
    └── Verbatim mode  →  raw chunk retrieval only
```

---

## Stack

| Component | Technology |
|---|---|
| Data warehouse | Snowflake |
| PDF parsing | Snowflake Cortex (`PARSE_DOCUMENT`) |
| Text chunking | Snowflake Cortex (`SPLIT_TEXT_RECURSIVE_CHARACTER`) |
| Semantic search | Snowflake Cortex Search Service |
| LLM | Snowflake Arctic (`CORTEX.COMPLETE`) |
| Frontend | Streamlit in Snowflake |
| Language | Python, SQL |

---

## Setup

### Prerequisites

- Snowflake account with Cortex enabled
- `ACCOUNTADMIN` role (for initial setup)
- Cortex Search available in your region

### Step 1 — Run SQL setup scripts in order

Run each file in `sql/` sequentially in a Snowflake worksheet:
```sql
-- 1. Create DB, schema, warehouse
01_setup.sql

-- 2. Parse PDFs → PARSED_POLICY_DOCS
02_parse_docs.sql

-- 3. Chunk text → POLICY_DOC_CHUNKS
03_chunk_text.sql

-- 4. Create Cortex Search Service
04_create_search_service.sql

-- 5. Test search (optional)
05_test_search.sql
```

### Step 2 — Deploy the PDF uploader

Create a new Streamlit app in Snowflake:
- Database: `RAG_DOCS_DB`
- Schema: `INTERNAL_PDFS`
- Warehouse: `RAG_WH`

Paste the contents of `apps/pdf_uploader.py` and run it. Upload your policy PDFs.

Then run in a worksheet:
```sql
ALTER STAGE PDF_STAGE_RAW REFRESH;
SELECT * FROM DIRECTORY(@PDF_STAGE_RAW);
```

### Step 3 — Deploy the assistant

Create another Streamlit app with the same DB/schema/warehouse settings.
Paste one of:

| File | Mode |
|---|---|
| `apps/assistant_summary.py` | LLM-summarized answers + citations |
| `apps/assistant_verbatim.py` | Exact policy excerpts only (no LLM) |
| `apps/assistant_toggle.py` | Toggle between both modes |

---

## Assistant Modes

### Summary Mode
Uses `CORTEX.COMPLETE` (snowflake-arctic) to generate a natural language answer
grounded in the top 5 retrieved policy chunks. Best for internal guidance and
employee Q&A.

### Verbatim Mode
Returns exact text excerpts from the indexed PDFs with no LLM interpretation.
Best for compliance use cases where verbatim policy text is required.

### Toggle Mode
Lets the user switch between both modes in the same interface.

---

## Snowflake Resources Created

| Resource | Name | Type |
|---|---|---|
| Database | `RAG_DOCS_DB` | Database |
| Schema | `INTERNAL_PDFS` | Schema |
| Warehouse | `RAG_WH` | XSmall, auto-suspend 60s |
| Stage | `PDF_STAGE_RAW` | Internal stage (SSE encrypted) |
| Table | `PARSED_POLICY_DOCS` | One row per PDF |
| Table | `POLICY_DOC_CHUNKS` | One row per chunk |
| Search Service | `POLICY_DOCS_SEARCH` | Cortex Search, 90min lag |

---

## Key Design Decisions

**Why Snowflake Cortex instead of an external vector DB?**
Everything stays inside the data warehouse, so no credentials to manage, no separate
infrastructure to maintain, and no data leaving the Snowflake trust boundary.
This is good for internal compliance documents.

**Why two assistant modes?**
Verbatim mode is appropriate for official compliance answers. Summary mode is
appropriate for internal employee guidance. The toggle version gives operators
control over which mode employees use.

**Why 1800 char chunks with 250 overlap?**
This balances retrieval precision (smaller chunks = more targeted results) against
context completeness (overlap prevents answers from being split across chunk boundaries).

---

## Reference

Built using Snowflake Cortex features:
- [CORTEX.PARSE_DOCUMENT](https://docs.snowflake.com/en/user-guide/snowflake-cortex/parse-document)
- [CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER](https://docs.snowflake.com/en/user-guide/snowflake-cortex/split-text)
- [Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [CORTEX.COMPLETE](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)