import json 
import streamlit as st 
from snowflake.snowpark.context import get_active_session 
 
session = get_active_session() 
 
st.title("American Refrigeration Policy Assistant") 
 
st.write( 
    "Ask questions about SOPs, safety procedures, and internal policies. " 
    "Answers are summarized by an LLM and grounded in retrieved policy text." 
) 
 
if "history" not in st.session_state: 
    st.session_state.history = [] 
 
question = st.text_input( 
    "Question", 
    placeholder="e.g. When is a full-face respirator required?", 
) 
 
ask_clicked = st.button("Ask") 
 
if ask_clicked and question.strip(): 
    with st.spinner("Thinking..."): 
 
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
), 
search_results AS ( 
  SELECT 
    value:"RELATIVE_PATH"::string AS rel_path, 
    value:"CHUNK"::string        AS chunk 
  FROM raw, 
  LATERAL FLATTEN(input => resp:"results") 
), 
context AS ( 
  SELECT 
    LISTAGG(chunk, '\\n\\n') AS context_text 
  FROM search_results 
), 
answer AS ( 
  SELECT 
    SNOWFLAKE.CORTEX.COMPLETE( 
      'snowflake-arctic', 
      'You are a safety and policy assistant for American Refrigeration. ' 
      || 'Answer using ONLY the provided policy text. If the policy text is ' 
      || 'unclear or does not answer the question, say so explicitly.' 
      || '\\n\\nContext:\\n' || context_text 
      || '\\n\\nQuestion:\\n' || $${question}$$ 
    ) AS ANSWER, 
    1 AS key 
  FROM context 
), 
citation_json AS ( 
  SELECT 
    ARRAY_AGG( 
      OBJECT_CONSTRUCT( 
        'relative_path', rel_path, 
        'snippet', SUBSTR(chunk, 1, 200) 
      ) 
    ) AS CITATIONS, 
    1 AS key 
  FROM search_results 
) 
SELECT ANSWER, CITATIONS 
FROM answer 
JOIN citation_json USING (key); 
""" 
 
        df = session.sql(sql).to_pandas() 
        row = df.iloc[0] 
        answer = row["ANSWER"] 
        citations_raw = row["CITATIONS"] 
 
        if isinstance(citations_raw, str): 
            try: 
                citations = json.loads(citations_raw) 
            except Exception: 
                citations = [] 
        else: 
            citations = citations_raw or [] 
 
        st.session_state.history.append( 
            {"role": "user", "content": question} 
        ) 
        st.session_state.history.append( 
            {"role": "assistant", "content": answer, "citations": citations} 
        ) 
 
for msg in st.session_state.history: 
    if msg["role"] == "user": 
        st.markdown(f"**You:** {msg['content']}") 
    else: 
        st.markdown(f"**Assistant:** {msg['content']}") 
        cites = msg.get("citations") or [] 
        if cites: 
            with st.expander("Sources", expanded=False): 
                for i, c in enumerate(cites, start=1): 
                    rel_path = c.get("relative_path", "") 
                    snippet = c.get("snippet", "") 
                    st.markdown(f"**{i}.** `{rel_path}` - {snippet}")