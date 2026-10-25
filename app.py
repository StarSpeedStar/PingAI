import streamlit as st
from groq import Groq
import os
import re
from datetime import datetime
from google.cloud import firestore
from google.oauth2 import service_account

# Page configuration - Must be the very first Streamlit command executed
st.set_page_config(
    page_title="Ping AI Companion (Beta)", 
    page_icon="assets/logo.png", 
    layout="centered"
)

# Custom clean styling ensuring full visibility for inputs, text, and code blocks
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
    /* Fix to ensure code snippets and multi-line pre blocks are legible against light backdrop */
    code, pre {
        color: #2d3748 !important;
        background-color: #edf2f7 !important;
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
    /* Style tweak to make the beta badge pop */
    .beta-badge {
        background-color: #e2e8f0;
        color: #4a5568;
        font-size: 0.75rem;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 8px;
        vertical-align: middle;
    }
    </style>
""", unsafe_allow_html=True)

def format_latex_for_streamlit(text: str) -> str:
    """
    Translates raw block/inline LaTeX formats, structural anomalies, 
    and blockquote markings into Streamlit-native math delimiters ($ and $$).
    """
    if not text or not isinstance(text, str):
        return ""
        
    text = text.replace("> ", "").replace(" >", "")
    
    if "$$" in text and text.count("$$") % 2 != 0:
        text = "$$\n" + text

    text = re.sub(r'\\\[(.*?)\\\]', r'\n$$\1$$\n', text, flags=re.DOTALL)
    text = re.sub(r'(?m)^\[\s*(.*?)\s*\]$', r'$$\1$$', text)
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text)
    return text

@st.cache_resource
def get_firestore_client():
    """
    Production Engine: Loads the perfectly preserved flat string directly 
    from secrets and instantiates a clean Firebase Firestore connection.
    """
    try:
        import json

        # Fetch the flat string sequence
        raw_json_payload = st.secrets.get("FIREBASE_RAW_JSON")
        if not raw_json_payload:
            # Fallback silently or output configuration notice if empty
            return None

        # Standardize double-escaped structural newlines cleanly across systems
        fixed_string = raw_json_payload.replace("\\\\n", "\\n")
        
        # Parse the clean text string straight into a working credential map dictionary
        credentials_dict = json.loads(fixed_string)
        
        if "private_key" in credentials_dict:
            credentials_dict["private_key"] = credentials_dict["private_key"].replace("\\n", "\n")

        creds = service_account.Credentials.from_service_account_info(credentials_dict)
        return firestore.Client(credentials=creds, project=credentials_dict.get("project_id"))
    except Exception as e:
        st.error(f"Failed to connect to Firebase database cloud storage: {e}")
        return None


def save_feedback_to_firebase(rating: int, comments: str):
    """
    Streams the submitted user feedback entry live into a Firestore collection named 'beta_feedback'.
    """
    db = get_firestore_client()
    if db is not None:
        try:
            doc_ref = db.collection("beta_feedback").document()
            doc_ref.set({
                "timestamp": datetime.utcnow(),
                "rating": rating,
                "comments": comments
            })
            st.sidebar.success("🎉 Thank you! Your feedback has been securely logged to Firebase.")
        except Exception as e:
            st.sidebar.error(f"Could not push feedback payload to Firestore server: {e}")

# Fetch API Key securely from secrets configuration
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

if not GROQ_API_KEY:
    st.error("⚠️ Error: GROQ_API_KEY is missing from your Streamlit secrets vault.")
    st.stop()

# Instantiate the standard API client connection safely
client = Groq(api_key=GROQ_API_KEY)

# Header Section
st.title("💬 Ping AI Assistant")
st.caption("Your friendly, fast, and intelligent daily companion.")

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar Controls & Model Selector
with st.sidebar:
    # Universal App Branding Block
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(logo_path, width=45)
        with col2:
            st.markdown('<div class="sidebar-branding-text" style="line-height: 45px;">Ping AI <span class="beta-badge">BETA</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="sidebar-branding-text">💬 Ping AI <span class="beta-badge">BETA</span></div>', unsafe_allow_html=True)
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

    # --- BETA USER FEEDBACK ENGINE (Saves securely to Firebase Cloud Firestore) ---
    st.markdown("---")
    st.header("📣 Beta Feedback")
    with st.form("feedback_form", clear_on_submit=True):
        rating = st.slider("Rate your experience:", 1, 5, 5, help="1 = Poor, 5 = Excellent")
        comments = st.text_area("Help us improve Ping AI:", placeholder="What features should we add? Did you hit any bugs?", max_chars=500)
        submitted = st.form_submit_button("Submit Beta Feedback")
        
        if submitted:
            if comments.strip():
                save_feedback_to_firebase(rating, comments.strip())
            else:
                st.warning("Please add a short comment before submitting.")

    st.markdown("---")
    st.caption(f"Active Model: {selected_model_name}")
    st.caption("Status: 🟢 Online & Optimized")

# Display historical messages in viewport chronological sequence
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(format_latex_for_streamlit(msg["content"]))

# Chat Input & Processing Loop
if user_input := st.chat_input("Type your message here..."):
    
    # Render user message instantly to the local screen context
    with st.chat_message("user"):
        st.markdown(user_input)
        
    # Append the raw interface message cleanly to your history log
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Prepare active payload context isolation layer
    active_payload = user_input
    if document_context:
        active_payload = f"{user_input}\n\n--- ATTACHED DOCUMENT ({uploaded_file.name}) ---\n{document_context}"

    # Fast intent classification (Gatekeeper) with safe error isolation boundaries
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
            "Keep your tone encouraging, clear, and direct. When providing mathematical "
            "formulas or physics calculations, always wrap block math in $$...$$ or single $...$ "
            "for inline text to ensure ideal readability."
        )
        chat_messages = [{"role": "system", "content": system_prompt}]
        
        # Load historical conversation elements up to the last turn context
        for m in st.session_state.messages[:-1]:
            chat_messages.append({"role": m["role"], "content": m["content"]})
            
        # Append latest user interaction turn with attached parsing context loaded
        chat_messages.append({"role": "user", "content": active_payload})
        
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
                    sanitized_stream = format_latex_for_streamlit(full_response)
                    response_placeholder.markdown(sanitized_stream + " ▌")
                    
            response_placeholder.markdown(format_latex_for_streamlit(full_response))
        except Exception as e:
            full_response = f"⚠️ Request couldn't be completed with model {selected_model_name}. Error details: {str(e)}"
            response_placeholder.error(full_response)
            
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.rerun()

