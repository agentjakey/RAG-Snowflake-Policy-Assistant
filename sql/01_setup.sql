-- ============================================================
-- 01_setup.sql
-- Creates all Snowflake resources needed for the RAG pipeline.
-- Run this first before any other script.
-- ============================================================

USE ROLE ACCOUNTADMIN;

-- Create the database that holds everything
CREATE DATABASE IF NOT EXISTS RAG_DOCS_DB;

-- Create the schema for all RAG-related objects
CREATE SCHEMA IF NOT EXISTS RAG_DOCS_DB.INTERNAL_PDFS;

-- Create a small warehouse that auto-suspends after 60s idle
-- XSMALL is sufficient for parsing, chunking, and search
CREATE WAREHOUSE IF NOT EXISTS RAG_WH
    WAREHOUSE_SIZE = XSMALL
    AUTO_SUSPEND   = 60
    INITIALLY_SUSPENDED = TRUE;

-- Set active context for all subsequent statements
USE DATABASE  RAG_DOCS_DB;
USE SCHEMA    INTERNAL_PDFS;
USE WAREHOUSE RAG_WH;

-- Grant Cortex access to ACCOUNTADMIN so we can call:
--   CORTEX.PARSE_DOCUMENT
--   CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER
--   CORTEX.SEARCH_PREVIEW
--   CORTEX.COMPLETE
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE ACCOUNTADMIN;

-- Create the internal stage where PDF files will be uploaded.
-- SNOWFLAKE_SSE encryption is required for CORTEX.PARSE_DOCUMENT to read files.
-- DIRECTORY = TRUE enables DIRECTORY(@PDF_STAGE_RAW) queries.
CREATE OR REPLACE STAGE PDF_STAGE_RAW
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    DIRECTORY  = (ENABLE = TRUE);

-- Verify the stage exists
SHOW STAGES;