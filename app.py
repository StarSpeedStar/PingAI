import streamlit as st
from groq import Groq
import os
import re

# Page configuration
st.set_page_config(
    page_title="Ping AI Companion", 
    page_icon="assets/logo.png", 
    layout="centered"
)

# Custom clean styling ensuring full visibility for inputs and responses
st.markdown("""
    <style>
    .stApp { 
        background-color: #fafbfc; 
        color: #1a202c; 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    /* Fix for invisible text while typing in the chat input */
    .stChatInput textarea {
        color: #1a202c !important;
        background-color: #ffffff !important;
    }
    /* Fix to guarantee assistant response text is clearly visible */
    .stChatMessage p, .stChatMessage div, .stMarkdown {
        color: #1a202c !important;
    }
    .stChatMessage {
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
    }
    .stButton>button { 
        border-radius: 8px;
        font-weight: 500;
        width: 100%;
    }
    div[data-testid="stSidebar"] { 
        background-color: #f4f6f8; 
        border-right: 1px solid #e2e8f0; 
    }
    /* Smooth scaling and layout alignment for the branding logo */
    .sidebar-branding-text {
        font-size: 1.35rem;
        font-weight: 700;
        color: #1a202c;
    }
    </style>
""", unsafe_allow_html=True)

def format_latex_for_streamlit(text: str) -> str:
    """
    Translates raw block/inline LaTeX formats into Streamlit-native math delimiters ($ and $$).
    """
    # Replace display block brackets \[ ... \] or standard isolated [ ... ] math patterns with $$
    text = re.sub(r'\\\[(.*?)\\\]', r'\n$$\1$$\n', text, flags=re.DOTALL)
    # Replace standalone lines that open and close with raw mathematical brackets
    text = re.sub(r'(?m)^\[\s*(.*?)\s*\]$', r'$$\1$$', text)
    
    # Replace common inline delimiters like \( ... \) with $
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text)
    return text

# Fetch API Key securely
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

if not GROQ_API_KEY:
    st.error("⚠️ Error: GROQ_API_KEY is missing from your Streamlit secrets vault.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

# Header Section
st.title("💬 Ping AI Assistant")
st.caption("Your friendly, fast, and intelligent daily companion.")

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar Controls & Model Selector
with st.sidebar:
    # Universal App Branding Block
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        col1, col2 = st.columns()
        with col1:
            st.image(logo_path, width=45)
        with col2:
            st.markdown('<div class="sidebar-branding-text" style="line-height: 45px;">Ping AI</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="sidebar-branding-text">💬 Ping AI</div>', unsafe_allow_html=True)
        st.caption("💡 Tip: Add `assets/logo.png` to display your custom brand image here.")
        
    st.markdown("---")
    
    st.header("🧠 Model Selector")
    model_options = {
        "GPT-OSS 20B": "openai/gpt-oss-20b",
        "Qwen3.8-27b": "qwen/qwen3.8-27b",
        "Llama 3.1 8B": "meta-llama/Llama-3.1-8B-Instruct:novita",
        "GPT-OSS 120B": "openai/gpt-oss-120b"
    }
    selected_model_name = st.selectbox("Choose AI Model:", list(model_options.keys()))
    selected_model = model_options[selected_model_name]

    st.markdown("---")
    st.header("📂 Document Vault")
    uploaded_file = st.file_uploader(
        "Attach a file for analysis:", 
        type=["txt", "py", "csv", "json", "md"]
    )
    
    document_context = ""
    if uploaded_file is not None:
        try:
            document_context = uploaded_file.read().decode("utf-8")
            st.success(f"Attached: {uploaded_file.name}")
        except Exception as e:
            st.error(f"Could not read file: {e}")

    st.markdown("---")
    st.header("⚙️ Controls")
    if st.button("🧹 Clear Chat History", type="secondary"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.caption(f"Active Model: {selected_model_name}")
    st.caption("Status: 🟢 Online & Optimized")

# Display historical messages (running them through our LaTeX sanitizer)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(format_latex_for_streamlit(msg["content"]))

# Chat Input & Processing Loop
if user_input := st.chat_input("Type your message here..."):
    # Combine prompt with uploaded file context if present
    active_payload = user_input
    if document_context:
        active_payload = f"{user_input}\n\n--- ATTACHED DOCUMENT ({uploaded_file.name}) ---\n{document_context}"

    # Render user message
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": active_payload})

    # Fast intent classification (Gatekeeper) with robust error handling
    gatekeeper_prompt = (
        f"Analyze this input: '{user_input}'. Is this a simple everyday query or casual chat, "
        "or does it require deep structural reasoning or coding logic? "
        "Reply with exactly one word: 'FAST' or 'DEEP'."
    )
    
    routing_decision = "FAST"
    try:
        gatekeeper_res = client.chat.completions.create(
            model=selected_model,
            messages=[{"role": "system", "content": gatekeeper_prompt}]
        )
        if gatekeeper_res.choices and gatekeeper_res.choices[0].message.content:
            routing_decision = gatekeeper_res.choices[0].message.content.strip().upper()
    except Exception as e:
        # Fallback gracefully if gatekeeper fails
        routing_decision = "FAST"

    internal_thought = ""
    if "DEEP" in routing_decision:
        with st.spinner(f"✨ Ping is analyzing your request using {selected_model_name}..."):
            try:
                reflection_res = client.chat.completions.create(
                    model=selected_model,
                    messages=[{"role": "system", "content": f"Formulate a brief strategy to answer: {user_input}"}]
                )
                if reflection_res.choices and reflection_res.choices[0].message.content:
                    internal_thought = reflection_res.choices[0].message.content
                else:
                    internal_thought = "Standard processing."
            except Exception as e:
                internal_thought = f"Reflection skipped due to API error: {str(e)}"
    else:
        internal_thought = "Standard execution."

    # Assistant Response Streaming with Exception Handling
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        system_prompt = (
            "You are Ping, a warm, polite, extremely helpful, and friendly AI assistant. "
            "Keep your tone encouraging, clear, and direct."
        )

        chat_messages = [{"role": "system", "content": system_prompt}]
        for m in st.session_state.messages:
            chat_messages.append({"role": m["role"], "content": m["content"]})

        try:
            stream = client.chat.completions.create(
                model=selected_model,
                messages=chat_messages,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_response += token
                    # Sanitize formatting actively during live-streaming text
                    sanitized_stream = format_latex_for_streamlit(full_response)
                    response_placeholder.markdown(sanitized_stream + " ▌")
                
            response_placeholder.markdown(format_latex_for_streamlit(full_response))
        except Exception as e:
            full_response = f"⚠️ Request couldn't be completed with model `{selected_model_name}`. Error details: {str(e)}"
            response_placeholder.error(full_response)
        
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun()

