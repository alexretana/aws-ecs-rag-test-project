import os
import streamlit as st
import httpx

# Configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="RAG Chat",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 RAG Chat Interface")
st.markdown("Ask questions about the knowledge base.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("📚 Sources"):
                for i, source in enumerate(message["sources"], 1):
                    st.markdown(f"**Source {i}** (similarity: {source['similarity']})")
                    st.markdown(f"> {source['content']}")

# Chat input
if prompt := st.chat_input("Ask a question..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get response from backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = httpx.post(
                    f"{BACKEND_URL}/api/query",
                    json={"query": prompt, "top_k": 5},
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()
                
                st.markdown(data["answer"])
                
                # Show sources
                if data["sources"]:
                    with st.expander("📚 Sources"):
                        for i, source in enumerate(data["sources"], 1):
                            st.markdown(f"**Source {i}** (similarity: {source['similarity']})")
                            st.markdown(f"> {source['content']}")
                
                # Add to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": data["answer"],
                    "sources": data["sources"]
                })
                
            except httpx.HTTPStatusError as e:
                st.error(f"Backend error: {e.response.status_code}")
            except httpx.RequestError as e:
                st.error(f"Connection error: {str(e)}")

# Sidebar with stats
with st.sidebar:
    st.header("System Info")
    
    try:
        stats = httpx.get(f"{BACKEND_URL}/api/stats", timeout=5.0).json()
        st.metric("Documents Indexed", stats.get("chunk_count", 0))
    except:
        st.warning("Could not fetch stats")
    
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()