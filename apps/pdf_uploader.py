import streamlit as st 
from snowflake.snowpark.context import get_active_session 
import tempfile 
import os 
 
session = get_active_session() 
 
st.title("PDF Uploader → Snowflake Stage") 
 
st.write("Upload SOP / policy PDFs directly into @PDF_STAGE_RAW.") 
 
uploaded_files = st.file_uploader( 
    "Choose PDF files", 
    type=["pdf"], 
    accept_multiple_files=True 
) 
 
if uploaded_files: 
    for uploaded_file in uploaded_files: 
        # Save uploaded file to a temporary path 
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp: 
            tmp.write(uploaded_file.read()) 
            tmp_path = tmp.name 
 
        # Upload to Snowflake internal stage 
        session.file.put( 
            tmp_path, 
            "@PDF_STAGE_RAW", 
            overwrite=True, 
            auto_compress=False 
        ) 
 
        # Clean up local temp file 
        os.remove(tmp_path) 
 
    st.success(f"Uploaded {len(uploaded_files)} file(s) to @PDF_STAGE_RAW")