-- ============================================================
-- 02_parse_docs.sql
-- Run AFTER uploading PDFs via the pdf_uploader Streamlit app.
-- Refreshes stage metadata, then parses each PDF into a table.
-- ============================================================

USE ROLE      ACCOUNTADMIN;
USE WAREHOUSE RAG_WH;
USE DATABASE  RAG_DOCS_DB;
USE SCHEMA    INTERNAL_PDFS;

-- Step 1: Refresh directory metadata so Snowflake sees newly uploaded files.
-- Always run this after uploading new PDFs — without it, new files won't appear.
ALTER STAGE PDF_STAGE_RAW REFRESH;

-- Step 2: Verify your PDFs are visible before parsing
SELECT *
FROM DIRECTORY(@PDF_STAGE_RAW);

-- Step 3: Parse every PDF in the stage into PARSED_POLICY_DOCS.
-- CORTEX.PARSE_DOCUMENT runs in LAYOUT mode, which preserves
-- document structure (headers, paragraphs, tables) better than plain text mode.
-- Output: one row per PDF with columns RELATIVE_PATH and PARSED_TEXT.
CREATE OR REPLACE TABLE PARSED_POLICY_DOCS AS
SELECT
    RELATIVE_PATH,
    SNOWFLAKE.CORTEX.PARSE_DOCUMENT(
        @PDF_STAGE_RAW,
        RELATIVE_PATH,
        OBJECT_CONSTRUCT('mode', 'LAYOUT')
    ):content::STRING AS PARSED_TEXT
FROM DIRECTORY(@PDF_STAGE_RAW)
WHERE RELATIVE_PATH ILIKE '%.pdf';  -- only process PDF files, skip anything else

-- Verify: should see one row per uploaded PDF
SELECT
    RELATIVE_PATH,
    LENGTH(PARSED_TEXT) AS char_count,
    LEFT(PARSED_TEXT, 300) AS preview
FROM PARSED_POLICY_DOCS;