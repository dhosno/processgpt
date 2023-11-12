import openai
from openai import OpenAI
import re
import streamlit as st
from prompts import get_system_prompt

openai.api_key = st.secrets.OPENAI_API_KEY

st.title("ProcessGPT - Snowflake & ChatGPT")
import json

def import_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

# Initialize the chat messages history

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": get_system_prompt()}]

# Prompt for user input 
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "results" in message:
            st.dataframe(message["results"])

# If last message is not from assistant, we need to generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        response = ""
        resp_container = st.empty()

        client = OpenAI()
        for part in client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
        ):
            response += part.choices[0].delta.content or ""
            resp_container.markdown(response)

        message = {"role": "assistant", "content": response}

        # Parse the response for a SQL query and execute if available
        sql_match = re.search(r"```sql\n(.*)\n```", response, re.DOTALL)

        if sql_match:
            sql = sql_match.group(1)
            conn = st.connection("snowflake")
            message["results"] = conn.query(sql)
            st.dataframe(message["results"])
        
        st.session_state.messages.append(message)
