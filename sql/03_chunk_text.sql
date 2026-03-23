-- ============================================================
-- 03_chunk_text.sql
-- Splits each parsed document into overlapping text chunks.
-- Run after 02_parse_docs.sql.
-- ============================================================

USE ROLE      ACCOUNTADMIN;
USE WAREHOUSE RAG_WH;
USE DATABASE  RAG_DOCS_DB;
USE SCHEMA    INTERNAL_PDFS;

-- Split each document's PARSED_TEXT into smaller chunks using
-- CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER.
--
-- Parameters:
--   PARSED_TEXT  : the full document text to split
--   'markdown'   : treat text as markdown (respects headings and paragraphs
--                  as natural split boundaries)
--   1800         : target chunk size in characters
--   250          : overlap between consecutive chunks — prevents answers
--                  from being cut across chunk boundaries
--
-- LATERAL FLATTEN unpacks the array of chunks into individual rows.
-- Output: one row per chunk with RELATIVE_PATH, CHUNK_INDEX, and CHUNK.
CREATE OR REPLACE TABLE POLICY_DOC_CHUNKS AS
SELECT
    RELATIVE_PATH,
    F.INDEX  AS CHUNK_INDEX,
    F.VALUE::STRING AS CHUNK
FROM PARSED_POLICY_DOCS,
LATERAL FLATTEN(
    INPUT => SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
        PARSED_TEXT,
        'markdown',
        1800,
        250
    )
) AS F;

-- Verify: check chunk count per document and preview a few chunks
SELECT
    RELATIVE_PATH,
    COUNT(*)        AS total_chunks,
    MIN(CHUNK_INDEX) AS first_idx,
    MAX(CHUNK_INDEX) AS last_idx
FROM POLICY_DOC_CHUNKS
GROUP BY RELATIVE_PATH
ORDER BY total_chunks DESC;

-- Preview the actual chunk text
SELECT
    RELATIVE_PATH,
    CHUNK_INDEX,
    LENGTH(CHUNK) AS chunk_chars,
    CHUNK
FROM POLICY_DOC_CHUNKS
LIMIT 10;