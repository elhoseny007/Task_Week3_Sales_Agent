import os
import json
import time
import asyncio
import sys
from contextlib import AsyncExitStack
from typing import Optional

import pandas as pd
import streamlit as st
import chromadb
import nest_asyncio

# LlamaIndex Imports
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.core.schema import TextNode, Document as LlamaDocument
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq as LlamaGroq
from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes

# Groq Official & MCP Imports
from groq import Groq
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Initialize Asyncio Patch
nest_asyncio.apply()

from dotenv import load_dotenv
load_dotenv()

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

/* Chat Messages & Input Styling */
[data-testid="stChatMessage"], 
[data-testid="stChatMessage"] p, 
[data-testid="stChatMessage"] span, 
.stMarkdown p {
    color: #FFFFFF !important;
}

[data-testid="stChatInput"] {
    border-radius: 12px !important;
    padding: 2px !important;
    background-color: transparent !important;
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
</style>
""", unsafe_allow_html=True)

# Render Navbar & Hero
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
# 2. SESSION STATE INITIALIZATION
# ==============================================================================
if "uploaded_files_dict" not in st.session_state:
    st.session_state.uploaded_files_dict = {}

if "messages" not in st.session_state:
    st.session_state.messages = []

# ==============================================================================
# 3. SIDEBAR (DATA MANAGEMENT)
# ==============================================================================
with st.sidebar:
    st.header("🕒 Chat History")
    
    # زر لبدء محادثة جديدة وتصفير الذاكرة
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.uploaded_files_dict = {}
        st.rerun()
        
    st.markdown("---")
    
    # عرض العناوين السابقة أو ملخص بسيط للأسئلة
    if st.session_state.messages:
        user_prompts = [msg["content"] for msg in st.session_state.messages if msg["role"] == "user"]
        for idx, saved_prompt in enumerate(user_prompts[-5:]): # عرض آخر 5 أسئلة
            # تم إصلاح السطر هنا
            short_title = saved_prompt[:25] + "..." if len(saved_prompt) > 25 else saved_prompt
            st.caption(f"💬 {short_title}")
    else:
        st.info("No recent conversations yet.")
# ==============================================================================
# 4. CONFIGURATIONS & CONSTANTS
# ==============================================================================
Groq_api_key = os.getenv("GROQ_API_KEY", "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")
embedding_model = 'sentence-transformers/all-MiniLM-L6-v2'
groq_model = 'llama-3.3-70b-versatile'

path = r"my_mcp_server.py"
path2 = r"hubspot_server.js"

MD_DIR = r"D:text"
JSON_DIR = r"json"

# ==============================================================================
# 5. LLM RESOURCE INITIALIZATION (FIXED LOGIC & ORDER)
# ==============================================================================
@st.cache_resource
def init_llama_resources():
    Settings.llm = LlamaGroq(model=groq_model, api_key=Groq_api_key, temperature=0)
    Settings.embed_model = HuggingFaceEmbedding(model_name=embedding_model)
    cache_idx = VectorStoreIndex(nodes=[], embed_model=Settings.embed_model)
    kb_idx = VectorStoreIndex(nodes=[], embed_model=Settings.embed_model)
    return cache_idx, kb_idx

# Trigger initialization
try:
    kb_index, cache_index = init_llama_resources()
except Exception as e:
    st.error(f"Resource Initialization Error: {e}")
    st.stop()

# ==============================================================================
# 6. SEMANTIC CACHE ACTIONS
# ==============================================================================
def update_cache(query: str, answer: str):
    node = TextNode(
        text=query,
        metadata={
            'answer': str(answer),
            'timestamp': time.time(),
            'is_valid': True
        }
    )
    cache_index.insert_nodes([node])

def check_semantic_cache(query: str, threshold: float = 0.85):
    MAX_TTL = 24 * 60 * 60
    retriever = cache_index.as_retriever(similarity_top_k=1)
    try:
        results = retriever.retrieve(query)
        if results and results[0].score >= threshold:
            node = results[0].node
            metadata = node.metadata
            age = time.time() - metadata.get("timestamp", 0)
            if metadata.get("is_valid", True) and age <= MAX_TTL:
                return metadata["answer"], "fresh"
    except Exception:
        pass
    return None, "miss"

# ==============================================================================
# 7. MCP CLIENT SUBSYSTEM
# ==============================================================================
class MCPClient:
    def __init__(self):
        self.sessions: list[ClientSession] = []
        self.exit_stack = AsyncExitStack()
        self.grok = Groq(api_key=Groq_api_key)
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
        # Step 1: Hit/Miss Check on Cache
        cached, status = check_semantic_cache(query)
        if cached:
            return f"**[Cache Hit]** {cached}"

        # Step 2: Fetch Context from Base Enterprise RAG Pipeline
        rag_context = ""
        try:
            kb_retriever = kb_index.as_retriever(similarity_top_k=3)
            kb_results = kb_retriever.retrieve(query)
            if kb_results:
                rag_context = "Relevant Knowledge Base Context from Kayfa Catalog:\n"
                for res in kb_results:
                    rag_context += f"-[Source: {res.node.metadata.get('source')}]: {res.node.text}\n\n"
        except Exception as e:
            rag_context = f"[RAG Error fetching catalog: {e}]\n"

        # Step 3: Inject Runtime Analytics Context from Sidebar
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

        # Master Prompt Compilation
        full_system_prompt = (
            f"{system_context}\n"
            f"{rag_context}\n"
            "You are an expert sales and data analyst assistant for Kayfa. "
            "Always stay grounded strictly in the provided Knowledge Base Context for courses, prices, and policies. "
            "Answer clearly, support both Arabic and English perfectly, and use tools to update CRMs or communicate if requested."
        )

        messages = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": query}
        ]

        if not self.sessions:
            response = self.grok.chat.completions.create(
                model=groq_model,
                messages=messages,
                temperature=0.2
            )
            actual_answer = response.choices[0].message.content
            update_cache(query, actual_answer)
            return actual_answer

        # Agent Tool-Calling Flow
        try:
            groq_formatted_tools = await self._get_all_tools()

            response = self.grok.chat.completions.create(
                model=groq_model,
                messages=messages,
                tools=groq_formatted_tools if groq_formatted_tools else None,
                temperature=0.2
            )

            assistant_message = response.choices[0].message
            final_outputs = []

            if assistant_message.content:
                final_outputs.append(assistant_message.content)

            if assistant_message.tool_calls:
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
                    messages=messages
                )
                final_outputs.append(final_response.choices[0].message.content)

            actual_answer = "\n\n".join(final_outputs)
            
        except Exception:
            response = self.grok.chat.completions.create(
                model=groq_model,
                messages=messages,
                temperature=0.2
            )
            actual_answer = response.choices[0].message.content

        update_cache(query, actual_answer)
        return actual_answer

    async def cleanup(self):
        if self.sessions:
            await self.exit_stack.aclose()

# ==============================================================================
# 8. CHAT INTERFACE RENDER (STREAMLIT)
# ==============================================================================
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("💬 Chat AI Assistant (General & Data Analysis)")

def is_arabic_line(text: str) -> bool:
    """فحص ما إذا كان السطر الحالي يحتوي على حروف عربية"""
    arabic_chars = set(chr(x) for x in range(0x0600, 0x06FF))
    return any(char in arabic_chars for char in text)

def render_styled_message(role: str, content: str):
    """تفكيك النص وعرض كل سطر بالمحاذاة والاتجاه المناسب له باللون الأبيض الصافي"""
    with st.chat_message(role):
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

# عرض تاريخ المحادثة
for msg in st.session_state.messages:
    render_styled_message(msg["role"], msg["content"])

# -------------------------------------------------------------
# هيكل الإدخال المطور: دمج زر الـ (+) والملفات مع الشات
# -------------------------------------------------------------
st.markdown("---")

# إنشاء عمودين سفليين: الأول لزر الرفع المدمج والثاني لصندوق النص
input_col1, input_col2 = st.columns([1, 12], gap="small")

with input_col1:
    # استخدام الـ Popover لفتح نافذة رفع ملفات عائمة وأنيقة عند الضغط على الـ (+)
    with st.popover("➕", help="Upload datasets for analysis", use_container_width=True):
        uploaded_files = st.file_uploader(
            "Upload CSV datasets", 
            type=["csv"], 
            accept_multiple_files=True,
            key="chat_uploader"
        )
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
    prompt = st.chat_input("Ask me anything, or click the (+) button to upload datasets to analyze!")

# معالجة إرسال البيانات والـ Pipeline
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    render_styled_message("user", prompt)

    with st.chat_message("assistant"):
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
                    
                    res = await client.process_query(prompt)
                    return res
                except Exception as e:
                    return f"Error during execution: {e}"
                finally:
                    await client.cleanup()

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            response = loop.run_until_complete(run_mcp_pipeline())
            st.session_state.messages.append({"role": "assistant", "content": response})
            
    st.rerun()

# إشعار سريع للمستخدم في الأسفل يوضح حالة الملفات المرفوعة حالياً إن وُجدت
if st.session_state.uploaded_files_dict:
    loaded_names = ", ".join(st.session_state.uploaded_files_dict.keys())
    st.caption(f"📁 **Active Datasets for Analysis:** {loaded_names}")
else:
    st.caption("Note: Dashboard is fully operational. Use the (+) button to attach data analysis files anytime.")
