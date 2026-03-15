import streamlit as st
import requests

API_BASE = "http://localhost:8005/api"

st.set_page_config(
    page_title="Legal RAG System",
    page_icon="&#9878;",
    layout="wide",
)

st.title("Legal RAG System")
st.markdown("Upload legal documents and query them using AI-powered search.")

# Sidebar for document upload
with st.sidebar:
    st.header("Document Upload")
    st.markdown("Upload PDF or DOCX files for processing.")

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["pdf", "docx", "doc"],
        help="Supported formats: PDF, DOCX",
    )

    if uploaded_file is not None:
        if st.button("Process Document", type="primary"):
            with st.spinner("Uploading and processing..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                    response = requests.post(f"{API_BASE}/upload", files=files, timeout=300)

                    if response.status_code == 200:
                        result = response.json()
                        if result["is_duplicate"]:
                            st.warning(f"'{result['filename']}' has already been processed.")
                        else:
                            st.success(
                                f"'{result['filename']}' processed successfully!\n\n"
                                f"Chunks created: {result['chunks_created']}"
                            )
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to the backend. Make sure the API is running on port 8000.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    st.divider()
    st.markdown("**Settings**")
    top_k = st.slider("Number of results (Top-K)", 1, 10, 5)
    alpha = st.slider("Semantic vs Keyword weight", 0.0, 1.0, 0.7, 0.05,
                       help="Higher = more semantic similarity, Lower = more keyword matching")

# Main chat interface
st.header("Chat with Legal Documents")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "citations" in message and message["citations"]:
            with st.expander("View Citations"):
                for i, cit in enumerate(message["citations"], 1):
                    st.markdown(
                        f"**[{i}]** {cit['citation']} "
                        f"(Relevance: {cit['relevance_score']:.2%})\n\n"
                        f"> {cit['text_snippet']}"
                    )

# Chat input
if prompt := st.chat_input("Ask a question about your legal documents..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get response
    with st.chat_message("assistant"):
        with st.spinner("Searching and generating answer..."):
            try:
                response = requests.post(
                    f"{API_BASE}/chat",
                    json={"query": prompt, "top_k": top_k, "alpha": alpha},
                    timeout=120,
                )

                if response.status_code == 200:
                    result = response.json()
                    answer = result["answer"]
                    citations = result["citations"]

                    st.markdown(answer)

                    if citations:
                        with st.expander("View Citations"):
                            for i, cit in enumerate(citations, 1):
                                st.markdown(
                                    f"**[{i}]** {cit['citation']} "
                                    f"(Relevance: {cit['relevance_score']:.2%})\n\n"
                                    f"> {cit['text_snippet']}"
                                )

                    # Save to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "citations": citations,
                    })
                else:
                    error_msg = f"Error: {response.json().get('detail', 'Unknown error')}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

            except requests.exceptions.ConnectionError:
                msg = "Cannot connect to the backend. Make sure the API is running on port 8000."
                st.error(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
            except Exception as e:
                msg = f"Error: {str(e)}"
                st.error(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
