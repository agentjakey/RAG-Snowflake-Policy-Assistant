import json 
import streamlit as st 
from snowflake.snowpark.context import get_active_session 
 
session = get_active_session() 
 
st.title("American Refrigeration Policy Assistant") 
 
st.write( 
    "Ask questions about SOPs, safety procedures, and internal policies. " 
    "Responses show exact policy excerpts (no AI rewording or interpretation)." 
) 
 
if "history" not in st.session_state: 
    st.session_state.history = [] 
 
question = st.text_input( 
    "Question", 
    placeholder="e.g. When is a full-face respirator required?", 
) 
 
ask_clicked = st.button("Ask") 
 
if ask_clicked and question.strip(): 
    with st.spinner("Searching policy documents..."): 
 
        payload = json.dumps({ 
            "query": question, 
            "columns": ["RELATIVE_PATH", "CHUNK"], 
            "limit": 5 
        }) 
 
        sql = f""" 
WITH raw AS ( 
  SELECT PARSE_JSON( 
    SNOWFLAKE.CORTEX.SEARCH_PREVIEW( 
      'POLICY_DOCS_SEARCH', 
      $${payload}$$ 
    ) 
  ) AS resp 
) 
SELECT 
  value:"RELATIVE_PATH"::string AS rel_path, 
  value:"CHUNK"::string        AS chunk 
FROM raw, 
LATERAL FLATTEN(input => resp:"results"); 
""" 
 
        df = session.sql(sql).to_pandas() 
 
        if df.empty: 
            answer_text = ( 
                "No exact policy excerpts were found for this question. " 
                "Please try rephrasing or verify the policy exists in the uploaded PDFs." 
            ) 
            citations = [] 
        else: 
            answer_lines = [] 
            citations = [] 
            for i, row in df.iterrows(): 
                rel_path = row["REL_PATH"] 
                chunk = row["CHUNK"] 
                answer_lines.append(f"[{i+1}] {chunk}") 
                citations.append({ 
                    "relative_path": rel_path, 
                    "snippet": chunk[:200] 
                }) 
 
            answer_text = ( 
                "Exact policy excerpts (no interpretation):\n\n" + 
                "\n\n".join(answer_lines) 
            ) 
 
        st.session_state.history.append( 
            {"role": "user", "content": question} 
        ) 
        st.session_state.history.append( 
            {"role": "assistant", "content": answer_text, "citations": citations} 
        ) 
 
for msg in st.session_state.history: 
    if msg["role"] == "user": 
        st.markdown(f"**You:** {msg['content']}") 
    else: 
        st.markdown(f"**Assistant:**\n\n{msg['content']}") 
        cites = msg.get("citations") or [] 
        if cites: 
            with st.expander("Sources", expanded=False): 
                for i, c in enumerate(cites, start=1): 
                    rel_path = c.get("relative_path", "") 
                    snippet = c.get("snippet", "") 
                    st.markdown(f"**{i}.** `{rel_path}` - {snippet}")