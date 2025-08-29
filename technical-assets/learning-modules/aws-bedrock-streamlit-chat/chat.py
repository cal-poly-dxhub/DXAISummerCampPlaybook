import streamlit as st
import boto3
from typing import List, Dict, Any

st.set_page_config(page_title="AI Chatbot", page_icon="🤖")
st.title("🤖 Simple AI Chatbot")
st.write("Chat with an AI using AWS Bedrock!")

@st.cache_resource
def get_bedrock_client() -> Any:
  return boto3.client('bedrock-runtime', region_name='us-west-2')

def invoke_model(messages: List[Dict[str, str]]) -> str:
  client = get_bedrock_client()

  bedrock_messages: List[Dict[str, Any]] = []
  for msg in messages:
    bedrock_messages.append({
      "role": msg["role"],
      "content": [{"text": msg["content"]}]
    })

  try:
    response = client.converse(
      modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
      messages=bedrock_messages,
      inferenceConfig={
        "maxTokens": 1000,
      }
    )

    return response['output']['message']['content'][0]['text']

  except Exception as e:
    return f"Sorry, I encountered an error: {str(e)}"

if "messages" not in st.session_state:
  st.session_state.messages = []

for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.write(message["content"])

if prompt := st.chat_input("Type your message here..."):
  st.session_state.messages.append({"role": "user", "content": prompt})
  
  with st.chat_message("user"):
    st.write(prompt)
  
  with st.chat_message("assistant"):
    with st.spinner("Thinking..."):
      response = invoke_model(st.session_state.messages)
  
  st.session_state.messages.append({"role": "assistant", "content": response})
  st.rerun() # refresh the app to show the new message 
             # updating session state does not automatically refresh the UI
