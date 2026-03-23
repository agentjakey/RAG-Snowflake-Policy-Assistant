-- ============================================================
-- 04_create_search_service.sql
-- Creates the Cortex Search Service over POLICY_DOC_CHUNKS.
-- Run after 03_chunk_text.sql.
--
-- NOTE: The search service builds its index asynchronously.
-- Wait 1-2 minutes after running before testing queries.
-- ============================================================

USE ROLE      ACCOUNTADMIN;
USE WAREHOUSE RAG_WH;
USE DATABASE  RAG_DOCS_DB;
USE SCHEMA    INTERNAL_PDFS;

-- Create the Cortex Search Service.
-- ON CHUNK        : the column to index for semantic search
-- WAREHOUSE       : compute used to maintain the index
-- TARGET_LAG      : how often the index refreshes when new chunks are added.
--                   '90 minutes' is the minimum allowed value.
-- The SELECT at the end defines what columns are returned in search results —
-- RELATIVE_PATH lets us trace each result back to its source PDF.
CREATE OR REPLACE CORTEX SEARCH SERVICE POLICY_DOCS_SEARCH
    ON CHUNK
    WAREHOUSE  = RAG_WH
    TARGET_LAG = '90 minutes'
AS
SELECT
    RELATIVE_PATH,
    CHUNK
FROM POLICY_DOC_CHUNKS;

-- Verify the service was created successfully
SHOW CORTEX SEARCH SERVICES;

-- --- Re-indexing after adding new PDFs --------------------------
-- If you upload new PDFs later, re-run scripts 02 through 04
-- in order to re-parse, re-chunk, and re-index everything:
--
--   02_parse_docs.sql     (refreshes stage + re-parses all PDFs)
--   03_chunk_text.sql     (re-chunks all parsed text)
--   04_create_search_service.sql  (rebuilds the search index)
--
-- The CREATE OR REPLACE in each script makes this safe to re-run.
-- ---------------------------------------------------------------