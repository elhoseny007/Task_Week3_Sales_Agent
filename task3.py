import os
import json
import time
import asyncio
import sys
import uuid
from contextlib import AsyncExitStack
from typing import Optional

import pandas as pd
import streamlit as st

# LlamaIndex Imports
from llama_index.core import Settings
from llama_index.core.schema import Document as LlamaDocument
from llama_index.llms.groq import Groq as LlamaGroq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.vector_stores import SimpleVectorStore

# 🎯 استيراد الـ Callback Manager لربط LlamaIndex بـ Langfuse أوتوماتيكياً
from llama_index.core.callbacks import CallbackManager
from langfuse.llama_index import LlamaIndexCallbackHandler

# Groq Official & MCP Imports
from groq import Groq
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# التعديل الصحيح لاستيراد كلاس التتبع المتوافق مع Groq وتجنب كراش الـ Import
from langfuse.openai import OpenAI as LangfuseOpenAI

# 🔌 إعداد موديول لوحة التحكم لمنع الـ Caching الناتجة عن الـ exec
sys.path.append(r"C:\Users\ELZAHBIA\Vs_code")
try:
    from usaer_pass_page import run_admin_dashboard
except ImportError:
    run_admin_dashboard = None

from dotenv import load_dotenv
load_dotenv()
from langfuse import Langfuse
import os

lf = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-d5ec3773-fab8-4872-8bbb-219dbffe63b3"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-74f7c81c-3fa8-481b-96e5-b60c1364c629"),
    host="https://us.cloud.langfuse.com"
)

trace = lf.trace(
    name="manual-test",
    user_id="test-user"
)

lf.flush()

print("sent")
# ==============================================================================
# 1. PAGE CONFIGURATION & THEMING
# ==============================================================================
st.set_page_config(
    page_title="Stock AI Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Financial Dark Theme
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.stApp {
    background: #0B0E14 !important; 
    color: #F4F6F8 !important;
}
[data-testid="stChatMessage"], 
[data-testid="stChatMessage"] p, 
[data-testid="stChatMessage"] span, 
.stMarkdown p {
    color: #FFFFFF !important;
}

/* 1. جعل كل صناديق الرسائل تنكمش على قد الكلام بالظبط */
[data-testid="stChatMessage"] {
    width: fit-content !important;
    max-width: 80% !important; 
    display: flex !important;
    margin-bottom: 12px !important;
}

/* 2. نقل رسائل المستخدم (User) بالكامل إلى جهة اليمين */
[data-testid="stChatMessage"]:has(img[src*="user"]),
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatar"] span:contains("👤")) {
    margin-left: auto !important;   
    margin-right: 0 !important;
    flex-direction: row-reverse !important; 
}

/* 3. تثبيت رسائل البوت (Assistant) في جهة اليسار */
[data-testid="stChatMessage"]:has(img[src*="Kayfa"]),
[data-testid="stChatMessage"]:has(img[src*="education"]),
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatar"] span:contains("🤖")) {
    margin-right: auto !important;  
    margin-left: 0 !important;
}

/* 4. تحسين محاذاة النصوص والمحتويات الداخلية */
[data-testid="stChatMessageContent"] {
    width: fit-content !important;
    text-align: right !important; 
}

.stChatInput textarea {
    background-color: #1E2330 !important; 
    color: #FFFFFF !important;            
    font-size: 15px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 10px !important;
    box-shadow: none !important;
    caret-color: #FFFFFF !important; 
}

.stChatInput textarea::placeholder {
    color: #9CA3AF !important; 
}

[data-testid="stChatInputSubmitButton"] {
    color: #10B981 !important; 
}
.upload-btn-container {
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Navbar Components */
.navbar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 999;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 50px;
    background: rgba(11, 14, 20, 0.9);
    backdrop-filter: blur(16px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.logo {
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: #FFFFFF;
}
.logo span { color: #10B981; }

/* Hero Banner */
.hero {
    min-height: 40vh;
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;
    overflow: hidden;
    padding: 110px 20px 30px 20px;
    background: linear-gradient(rgba(11, 14, 20, 0.88), rgba(11, 14, 20, 0.98)),
                url("https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=2070");
    background-size: cover;
    background-position: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}
.hero-content {
    position: relative;
    z-index: 5;
    text-align: center;
    max-width: 950px;
}
.badge {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 100px;
    border: 1px solid rgba(16, 185, 129, 0.2);
    background: rgba(16, 185, 129, 0.06);
    color: #34D399;
    letter-spacing: 1px;
    margin-bottom: 18px;
    font-size: 11px;
    font-weight: 600;
}
.main-title {
    font-size: 48px;
    font-weight: 800;
    line-height: 1.2;
    margin-bottom: 15px;
    color: #FFFFFF;
    letter-spacing: -1px;
}
.highlight {
    background: linear-gradient(90deg, #10B981, #FBBF24);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.subtitle {
    color: #9CA3AF;
    font-size: 15px;
    line-height: 1.6;
    max-width: 750px;
    margin: auto;
}

/* Form Styling for Credentials view */
.credentials-box {
    background-color: #111827;
    border: 1px solid #1F2937;
    padding: 30px;
    border-radius: 16px;
    max-width: 500px;
    margin: 40px auto;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
}
</style>
""", unsafe_allow_html=True)

# Render Navbar & Hero
col_logo, col_title = st.columns([1, 4])
with col_logo:
    try:
        st.image(r"mortarboard.png", width=180)
    except:
        pass
with col_title:
    st.markdown("""
<div class="navbar">
    <div class="logo">Kayfa <span>Sales AI</span></div>
    <div class="menu">🧠</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div class="hero-content">
        <div class="badge">🚀 Automated Agentic Sales & Enterprise RAG Platform</div>
        <h1 class="main-title">
            Kayfa AI Sales Agent <br>
            <span class="highlight">Intelligent Enrollment Assistant</span>
        </h1>
        <p class="subtitle">
            An advanced sales agent grounded in Kayfa's official catalog. Converses naturally in Arabic and English, handles objections, and logs qualified leads to MongoDB CRM.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. STATE INITIALIZATION
# ==============================================================================
if "uploaded_files_dict" not in st.session_state:
    st.session_state.uploaded_files_dict = {}

if "current_view" not in st.session_state:
    st.session_state.current_view = "chat"

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if "user_password" not in st.session_state:
    st.session_state.user_password = ""

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "all_chats" not in st.session_state:
    first_chat_id = str(uuid.uuid4())
    st.session_state.all_chats = {first_chat_id: []}
    st.session_state.current_chat_id = first_chat_id

# Link active conversation reference safely
st.session_state.messages = st.session_state.all_chats[st.session_state.current_chat_id]


# ==============================================================================
# 🧭 3. SIDEBAR (NAVIGATION & HISTORY)
# ==============================================================================
with st.sidebar:
    try:
        st.image(r"Kayfa_logo.png", width=160)
    except:
        pass
    st.header("🧭 Navigation")
    
    if st.button("💬 AI Chat Assistant", use_container_width=True, type="primary" if st.session_state.current_view == "chat" else "secondary", key="sb_chat_nav_btn"):
        st.session_state.current_view = "chat"
        st.rerun()
        
    if st.button("🔑 Kayfa Stuff", use_container_width=True, type="primary" if st.session_state.current_view == "credentials" else "secondary", key="sb_credentials_nav_btn"):
        st.session_state.current_view = "credentials"
        st.rerun()
        
    st.markdown("---")
    
    st.header("🕒 Chat History")
    if st.button("➕ New Chat", use_container_width=True, type="secondary", key="new_chat_btn"):
        new_chat_id = str(uuid.uuid4())
        st.session_state.all_chats[new_chat_id] = []
        st.session_state.current_chat_id = new_chat_id
        st.session_state.current_view = "chat"
        st.rerun()
        
    st.markdown("<br>", unsafe_allow_html=True)

    # عرض المحادثات السابقة
    if st.session_state.all_chats:
        for chat_id, messages_list in list(st.session_state.all_chats.items()):
            user_prompts = [msg["content"] for msg in messages_list if msg["role"] == "user"]
            if user_prompts:
                first_prompt = user_prompts[0]
                title = first_prompt[:20] + "..." if len(first_prompt) > 20 else first_prompt
            else:
                title = "New Conversation"
            
            is_current = (chat_id == st.session_state.current_chat_id)
            btn_label = f"🎯 {title}" if is_current else f"📁 {title}"
            btn_type = "primary" if is_current else "secondary"
            
            if st.button(btn_label, key=f"chat_btn_{chat_id}", use_container_width=True, type=btn_type):
                st.session_state.current_chat_id = chat_id
                st.session_state.current_view = "chat"
                st.rerun()
    else:
        st.info("No recent conversations yet.")
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # 🔄 زر تسجيل الخروج
    if st.session_state.get("current_view") == "credentials":
        if st.button("🚪 Log Out & Lock Dashboard", type="secondary", key="dashboard_logout", use_container_width=True):
            cost_data_backup = st.session_state.get("cost_data", None)
            st.session_state.clear()
            st.session_state.authenticated = False
            st.session_state.current_view = "credentials"
            if cost_data_backup:
                st.session_state.cost_data = cost_data_backup
            st.rerun()

# ==============================================================================
# 4. CONFIGURATIONS & CONSTANTS
# ==============================================================================
Groq_api_key = os.getenv("GROQ_API_KEY", "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")
if not Groq_api_key:
    st.error("🚨 Critical Error: `GROQ_API_KEY` is missing from environment variables.")
    st.stop()

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = Groq_api_key

groq_model = 'qwen/qwen3.6-27b'  
embedding_model = 'sentence-transformers/all-MiniLM-L6-v2'
path = r"my_mcp_server.py"
path2 = r"hubspot_server.js"

MD_DIR = r"text"
JSON_DIR = r"json"

# ==============================================================================
# 5. LLM RESOURCE INITIALIZATION (LlamaIndex Integration)
# ==============================================================================
@st.cache_resource
def init_llama_resources():
    try:
        langfuse_callback_handler = LlamaIndexCallbackHandler()
        Settings.callback_manager = CallbackManager([langfuse_callback_handler])
    except Exception as e:
        st.warning(f"Langfuse LlamaIndex Handler Warning: {e}")

    Settings.llm = LlamaGroq(model=groq_model, api_key=Groq_api_key, temperature=0)
    Settings.embed_model = HuggingFaceEmbedding(model_name=embedding_model)

    vector_store = SimpleVectorStore()
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    all_documents = []
    
    if os.path.exists(MD_DIR):
        md_files = [f for f in os.listdir(MD_DIR) if f.lower().endswith('.md')][:12]
        for file_name in md_files:
            file_path = os.path.join(MD_DIR, file_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                all_documents.append(LlamaDocument(
                    text=f.read(),
                    metadata={"source": file_name, "type": "markdown"}
                ))
                
    if os.path.exists(JSON_DIR):
        json_files = [f for f in os.listdir(JSON_DIR) if f.lower().endswith('.json')][:2]
        for file_name in json_files:
            file_path = os.path.join(JSON_DIR, file_name)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    all_documents.append(LlamaDocument(
                        text=json.dumps(content, ensure_ascii=False),
                        metadata={"source": file_name, "type": "json"}
                    ))
            except Exception as e:
                st.error(f"Error loading JSON {file_name}: {str(e)}")

    if all_documents:
        kb_idx = VectorStoreIndex.from_documents(
            all_documents,
            storage_context=storage_context,
            embed_model=Settings.embed_model
        )
    else:
        kb_idx = VectorStoreIndex([], embed_model=Settings.embed_model)

    return kb_idx

try:
    kb_index = init_llama_resources()
except Exception as e:
    st.error(f"Resource Initialization Error: {e}")
    st.stop()

# ==============================================================================
# 6. MCP CLIENT SUBSYSTEM (Agent Tracing Integration)
# ==============================================================================
class MCPClient:
    def __init__(self):
        self.sessions: list[ClientSession] = []
        self.exit_stack = AsyncExitStack()
        
        self.grok = LangfuseOpenAI(
            api_key=Groq_api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.tool_to_session_map = {}

    async def connect_to_server(self, server_script_path: str):
        if not os.path.exists(server_script_path):
            raise FileNotFoundError(f"Server script not found: {server_script_path}")

        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = sys.executable if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=os.environ.copy()
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport
        session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))
        await session.initialize()
        self.sessions.append(session)

    async def _get_all_tools(self):
        groq_formatted_tools = []
        self.tool_to_session_map.clear()
        for session in self.sessions:
            try:
                mcp_tools_resp = await session.list_tools()
                for tool in mcp_tools_resp.tools:
                    self.tool_to_session_map[tool.name] = session
                    groq_formatted_tools.append({
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema
                        }
                    })
            except Exception as e:
                st.warning(f"Failed to list tools from a server: {e}")
                
        return groq_formatted_tools

    async def process_query(self, query: str) -> str:
        rag_context = ""
        try:
            kb_retriever = kb_index.as_retriever(similarity_top_k=5)
            kb_results = kb_retriever.retrieve(query)
            if kb_results:
                rag_context = "Relevant Knowledge Base Context from Kayfa Catalog:\n"
                for res in kb_results:
                    rag_context += f"-[Source: {res.node.metadata.get('source')}]: {res.node.text}\n\n"
        except Exception as e:
            rag_context = f"[RAG Error fetching catalog: {e}]\n"

        system_context = ""
        if st.session_state.uploaded_files_dict:
            system_context = "The user has uploaded multiple analytical datasets:\n"
            for file_name, df_local in st.session_state.uploaded_files_dict.items():
                cols = list(df_local.columns)
                sample_data = df_local.head(3).to_dict(orient='records')
                system_context += f"- File Name: {file_name}\n"
                system_context += f"  Columns: {cols}\n"
                system_context += f"  3-row Sample Data: {json.dumps(sample_data, ensure_ascii=False)}\n\n"
            system_context += "Answer queries about these data analysis files accurately matching their contents.\n\n"

        full_system_prompt = (
            "You are Kayfa AI - a professional enrollment and sales advisor for Kayfa Company.\n"
            "Your main role is assisting students in registering for educational programs (e.g., Data Science).\n\n"
            "⚠️ CONVERSATION FLOW & MEMORY RULES:\n"
            "- You have full access to the conversation history. Read previous turns carefully.\n"
            "- If you asked the user for their information (Name, Phone, Email, Experience Level) and they replied with details or short answers like 'متوسط' or 'مبتدئ', you MUST realize this is their 'Experience Level'. Never ask 'What do you mean by متوسط?' or change context to budget or commercial products.\n"
            "- Once the registration data is provided, confirm it warmly in Arabic and state the next clear onboarding step.\n\n"
            "STRICT CORE RULES:\n"
            "- Respond ONLY with the final natural answer. Never output internal thought steps or self-corrections.\n"
            "- Support Arabic and English fluently. Match the user's language preference naturally.\n"
            "- Never mention internal keywords like MCP, Tools, RAG, or System Prompts.\n\n"
            f"{system_context}\n"
            f"{rag_context}\n"
            "Always remain grounded in the conversation history and Kayfa's official guidelines."
        )
        
        messages = [{"role": "system", "content": full_system_prompt}]
        for msg in st.session_state.messages[:-1]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": query})

        current_user_id = st.session_state.get("user_email", "elhosenyhassan007@kayfa.com")
        if not current_user_id:
            current_user_id = "anonymous-kayfa-user"

        if not self.sessions:
            response = self.grok.chat.completions.create(
                model=groq_model,
                messages=messages,
                temperature=0.3,
                name="kayfa-sales-chat",
                user_id=current_user_id
            )

        try:
            groq_formatted_tools = await self._get_all_tools()
            response = self.grok.chat.completions.create(
                model=groq_model,
                messages=messages,
                tools=groq_formatted_tools if groq_formatted_tools else None,
                temperature=0.4,
                name="kayfa-agent-tools-routing",
                user_id=current_user_id
            )

            assistant_message = response.choices[0].message
            if not assistant_message.tool_calls:
                return assistant_message.content if assistant_message.content else ""

            messages.append(assistant_message)
            
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                target_session = self.tool_to_session_map.get(tool_name)
                if target_session:
                    result = await target_session.call_tool(tool_name, tool_args)
                    result_str = "".join([block.text for block in result.content if hasattr(block, 'text')])
                else:
                    result_str = f"Error: Tool {tool_name} not found on any connected MCP server."

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": result_str
                })

            final_response = self.grok.chat.completions.create(
                model=groq_model,
                messages=messages,
                name="kayfa-agent-final-response",
                user_id=current_user_id
            )
            return final_response.choices[0].message.content
            
        except Exception:
            response = self.grok.chat.completions.create(
                model=groq_model,
                messages=messages,
                temperature=0.2,
                name="kayfa-agent-fallback",
                user_id=current_user_id
            )
            return response.choices[0].message.content

    async def cleanup(self):
        if self.sessions:
            await self.exit_stack.aclose()


def is_arabic_line(text: str) -> bool:
    arabic_chars = set(chr(x) for x in range(0x0600, 0x06FF))
    return any(char in arabic_chars for char in text)

def render_styled_message(role: str, content: str):
    avatar_to_show = r"mortarboard.png" if role == "assistant" else None
    with st.chat_message(role, avatar=avatar_to_show):
        lines = content.split("\n")
        inside_code_block = False
        current_block = []

        for line in lines:
            if line.strip().startswith("```"):
                inside_code_block = not inside_code_block
                current_block.append(line)
                if not inside_code_block:
                    st.markdown("\n".join(current_block))
                    current_block = []
                continue

            if inside_code_block:
                current_block.append(line)
                continue

            if line.strip() == "":
                st.markdown("")  
                continue

            if is_arabic_line(line):
                st.markdown(
                    f'<div style="direction: rtl; text-align: right; margin-bottom: 4px; color: #FFFFFF !important;">{line}</div>', 
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div style="direction: ltr; text-align: left; margin-bottom: 4px; color: #FFFFFF !important;">{line}</div>', 
                    unsafe_allow_html=True
                )

# ==============================================================================
# 7. CONDITIONAL VIEW RENDERING & ROUTING
# ==============================================================================

# --- VIEW 1: AI CHAT VIEW ---
if st.session_state.current_view == "chat":
    st.markdown("<br>", unsafe_allow_html=True)
    for msg in st.session_state.messages:
        render_styled_message(msg["role"], msg["content"])

    st.markdown("---")
    input_col1, input_col2 = st.columns([1, 12], gap="small")

    with input_col1:
        with st.popover("➕", help="Upload datasets for analysis", use_container_width=True):
            uploaded_files = st.file_uploader("Upload CSV datasets", type=["csv"], accept_multiple_files=True, key="chat_uploader")
            if uploaded_files:
                current_files_dict = {}
                for file in uploaded_files:
                    try:
                        df_temp = pd.read_csv(file)
                        current_files_dict[file.name] = df_temp
                        st.success(f"📎 {file.name} loaded successfully!")
                    except Exception as e:
                        st.error(f"Error: {e}")
                st.session_state.uploaded_files_dict = current_files_dict
            else:
                st.session_state.uploaded_files_dict = {}

    with input_col2:
        prompt = st.chat_input("Hi, I'm Kayfa, how can I help you? 😊")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        render_styled_message("user", prompt)

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with st.chat_message("assistant", avatar=r"mortarboard.png"):
            with st.spinner("Thinking..."):
                async def run_mcp_pipeline():
                    client = MCPClient()
                    try:
                        if os.path.exists(path):
                            try:
                                await client.connect_to_server(path)
                            except Exception as e:
                                st.error(f"Error connecting to Python server: {e}")

                        if os.path.exists(path2):
                            try:
                                await client.connect_to_server(path2)
                            except Exception as e:
                                st.error(f"Error connecting to HubSpot JS server: {e}")
                        
                        last_user_query = st.session_state.messages[-1]["content"]
                        res = await client.process_query(last_user_query)
                        return res
                    except Exception as e:
                        return f"Error during execution: {e}"
                    finally:
                        await client.cleanup()

                try:
                    response = asyncio.run(run_mcp_pipeline())
                    clean_response = response.strip()

                    unwanted_phrases = [
                        "Here's a thinking process", "Output matches response",
                        "Self-Correction", "Proceeds.", "[Output Generation]",
                        "Final check", "✅"
                    ]
                    
                    for phrase in unwanted_phrases:
                        if phrase in clean_response:
                            clean_response = clean_response.split(phrase)[-1].strip()
                    
                    if "Yes," in clean_response or "نعم" in clean_response or "Hi" in clean_response or "مرحبا" in clean_response:
                        lines = clean_response.split("\n")
                        for i, line in enumerate(lines):
                            if line.strip() and not line.strip().startswith("*") and not line.strip().startswith("["):
                                clean_response = "\n".join(lines[i:]).strip()
                                break
                                
                except Exception as e:
                    clean_response = f"حدث خطأ أثناء معالجة الطلب: {e}"

                # 🎯 Force flush the callback queue so Langfuse receives metrics updates immediately
                try:
                    if hasattr(Settings, "callback_manager"):
                        for handler in Settings.callback_manager.handlers:
                            if hasattr(handler, "flush"):
                                handler.flush()
                except Exception:
                    pass

                st.session_state.messages.append({"role": "assistant", "content": clean_response})
                st.rerun()

    if st.session_state.uploaded_files_dict:
        loaded_names = ", ".join(st.session_state.uploaded_files_dict.keys())
        st.caption(f"📁 **Active Datasets for Analysis:** {loaded_names}")
    else:
        st.caption("Note: Dashboard is fully operational. Use the (+) button to attach data analysis files anytime.")

# --- VIEW 2: CREDENTIALS VIEW ---
elif st.session_state.current_view == "credentials":
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 🔌 الاستدعاء المباشر للموديول النظيف لتفادي تجمد الواجهة ومشاكل ثبات البيانات
    if run_admin_dashboard is not None:
        try:
            run_admin_dashboard()
        except Exception as e:
            st.error(f"❌ حدث خطأ أثناء تشغيل صفحة الـ Credentials: {e}")
    else:
        # Fallback Interface inside the main box if script is unreached
        with st.container():
            st.markdown('<div class="credentials-box">', unsafe_allow_html=True)
            st.markdown("<h4 style='text-align: center; color: white; margin-bottom: 20px;'>Kayfa Authentic Stuff</h4>", unsafe_allow_html=True)
            
            email_input = st.text_input("Email Address / Username", value=st.session_state.user_email, placeholder="name@kayfa.ai")
            password_input = st.text_input("Password", value=st.session_state.user_password, type="password", placeholder="••••••••")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Save & Link Credentials", use_container_width=True, type="primary"):
                if email_input and password_input:
                    st.session_state.user_email = email_input
                    st.session_state.user_password = password_input
                    st.success("🔒 Credentials verified and mapped successfully!")
                    time.sleep(1)
                    st.session_state.current_view = "chat"
                    st.rerun()
                else:
                    st.error("Please fill out both fields.")
            st.markdown('</div>', unsafe_allow_html=True)
