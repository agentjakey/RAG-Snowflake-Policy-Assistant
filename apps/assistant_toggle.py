import json 
import streamlit as st 
from snowflake.snowpark.context import get_active_session 
 
session = get_active_session() 
 
st.title("American Refrigeration Policy Assistant") 
 
st.write( 
    "Ask questions about SOPs, safety procedures, and internal policies. " 
    "Choose between a summarized answer or exact policy excerpts." 
) 
 
if "history" not in st.session_state: 
    st.session_state.history = [] 
 
# Toggle 
mode = st.radio( 
    "Answer style", 
    ["Summary + citations", "Exact policy text (verbatim)"], 
    horizontal=True, 
) 
 
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
 
        sql_chunks = f""" 
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
 
        df = session.sql(sql_chunks).to_pandas() 
 
        if df.empty: 
            answer_text = ( 
                "No policy excerpts were found for this question. " 
                "Please try rephrasing or verify the policy exists in the uploaded PDFs." 
            ) 
            citations = [] 
        else: 
            # Build citations 
            citations = [] 
            for i, row in df.iterrows(): 
                rel_path = row["REL_PATH"] 
                chunk = row["CHUNK"] 
                citations.append({ 
                    "relative_path": rel_path, 
                    "snippet": chunk[:200] 
                }) 
 
            if mode == "Exact policy text (verbatim)": 
                # Verbatim: just show chunks 
                answer_lines = [] 
                for i, row in df.iterrows(): 
                    chunk = row["CHUNK"] 
                    answer_lines.append(f"[{i+1}] {chunk}") 
 
                answer_text = ( 
                    "Exact policy excerpts (no AI rewording or interpretation):\n\n" 
                    + "\n\n".join(answer_lines) 
                ) 
 
            else: 
                # Summary: call LLM on retrieved chunks 
                chunks = df["CHUNK"].tolist() 
                context_text = "\n\n".join(chunks) 
 
                prompt = ( 
                    "You are a safety and policy assistant for American Refrigeration. " 
                    "Answer using ONLY the provided policy text. If the policy text is " 
                    "unclear or does not answer the question, say so explicitly.\n\n" 
                    f"Context:\n{context_text}\n\nQuestion:\n{question}" 
                ) 
 
                sql_answer = f""" 
SELECT 
  SNOWFLAKE.CORTEX.COMPLETE( 
    'snowflake-arctic', 
    $${prompt}$$ 
  ) AS ANSWER; 
""" 
                df_answer = session.sql(sql_answer).to_pandas() 
                answer_text = df_answer["ANSWER"][0] 
 
        st.session_state.history.append( 
            {"role": "user", "content": question} 
        ) 
        st.session_state.history.append( 
            { 
                "role": "assistant", 
                "content": answer_text, 
                "citations": citations, 
                "mode": mode, 
            } 
        ) 
 
# Render history 
for msg in st.session_state.history: 
    if msg["role"] == "user": 
        st.markdown(f"**You:** {msg['content']}") 
    else: 
        mode_label = msg.get("mode", "Summary + citations") 
        st.markdown(f"**Assistant** ({mode_label}):") 
        st.markdown(msg["content"]) 
 
        cites = msg.get("citations") or [] 
        if cites: 
            with st.expander("Sources", expanded=False): 
                for i, c in enumerate(cites, start=1): 
                    rel_path = c.get("relative_path", "") 
                    snippet = c.get("snippet", "") 
                    st.markdown(f"**{i}.** `{rel_path}` - {snippet}")