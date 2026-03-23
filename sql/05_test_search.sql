-- ============================================================
-- 05_test_search.sql
-- Tests the Cortex Search Service with sample queries.
-- Run after 04_create_search_service.sql (wait ~1-2 min first).
-- No LLM is called here - pure retrieval only.
-- ============================================================

USE ROLE      ACCOUNTADMIN;
USE WAREHOUSE RAG_WH;
USE DATABASE  RAG_DOCS_DB;
USE SCHEMA    INTERNAL_PDFS;

-- --- Test 1: Personal protective equipment -------------------------
-- Should return chunks about PPE requirements from your policy docs
WITH raw AS (
    SELECT PARSE_JSON(
        SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
            'POLICY_DOCS_SEARCH',
            '{
                "query":   "personal protective equipment",
                "columns": ["RELATIVE_PATH", "CHUNK"],
                "limit":   5
            }'
        )
    ) AS resp
)
SELECT
    value:"RELATIVE_PATH"::STRING AS source_file,
    value:"CHUNK"::STRING         AS chunk_text
FROM raw,
LATERAL FLATTEN(input => resp:"results");

-- ---- Test 2: Ear protection ------------------------
-- Matches the demo query shown in the README screenshots
WITH raw AS (
    SELECT PARSE_JSON(
        SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
            'POLICY_DOCS_SEARCH',
            '{
                "query":   "when should I wear ear protection",
                "columns": ["RELATIVE_PATH", "CHUNK"],
                "limit":   5
            }'
        )
    ) AS resp
)
SELECT
    value:"RELATIVE_PATH"::STRING AS source_file,
    value:"CHUNK"::STRING         AS chunk_text
FROM raw,
LATERAL FLATTEN(input => resp:"results");

-- -- Test 3: Respirator requirements ------------------------
WITH raw AS (
    SELECT PARSE_JSON(
        SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
            'POLICY_DOCS_SEARCH',
            '{
                "query":   "when is a full-face respirator required",
                "columns": ["RELATIVE_PATH", "CHUNK"],
                "limit":   5
            }'
        )
    ) AS resp
)
SELECT
    value:"RELATIVE_PATH"::STRING AS source_file,
    value:"CHUNK"::STRING         AS chunk_text
FROM raw,
LATERAL FLATTEN(input => resp:"results");

-- --- Diagnostic: check chunk and document counts -----------
-- Useful to confirm how much content is indexed
SELECT
    COUNT(DISTINCT RELATIVE_PATH) AS total_documents,
    COUNT(*)                      AS total_chunks,
    AVG(LENGTH(CHUNK))            AS avg_chunk_chars,
    MIN(LENGTH(CHUNK))            AS min_chunk_chars,
    MAX(LENGTH(CHUNK))            AS max_chunk_chars
FROM POLICY_DOC_CHUNKS;
```

---

## Run order summary
```
01_setup.sql                <- run once to create all resources
    |
[upload PDFs via pdf_uploader Streamlit app]
    |
02_parse_docs.sql           <- parse PDFs into PARSED_POLICY_DOCS
    |
03_chunk_text.sql           <- chunk into POLICY_DOC_CHUNKS
    |
04_create_search_service.sql <- build POLICY_DOCS_SEARCH index
    |
[wait 1-2 minutes]
    |
05_test_search.sql          <- verify everything works