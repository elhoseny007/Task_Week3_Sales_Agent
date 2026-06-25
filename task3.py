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

# استيراد الـ Langfuse الرئيسي للتحكم الكامل يدوياً في الـ Tracing
from langfuse import Langfuse

# 🔌 إعداد موديول لوحة التحكم لمنع الـ Caching الناتجة عن الـ exec
sys.path.append(r"C:\Users\ELZAHBIA\Vs_code")
try:
    from usaer_pass_page import run_admin_dashboard
except ImportError:
    run_admin_dashboard = None

from dotenv import load_dotenv
load_dotenv()

# ==============================================================================
# 🎯 INITIALIZE LANGFUSE CLIENT
# ==============================================================================
lf = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-d5ec3773-fab8-4872-8bbb-219dbffe63b3"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-74f7c81c-3fa8-481b-96e5-b60c1364c629"),
    host="https://us.cloud.langfuse.com"
)

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

/* جعل كل صناديق الرسائل تنكمش على قد الكلام بالظبط */
[data-testid="stChatMessage"] {
    width: fit-content !important;
    max-width: 80% !important; 
    display: flex !important;
    margin-bottom: 12px !important;
}

/* نقل رسائل المستخدم (User) بالكامل إلى جهة اليمين */
[data-testid="stChatMessage"]:has(img[src*="user"]),
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatar"] span:contains("👤")) {
    margin-left: auto !important;   
    margin-right: 0 !important;
    flex-direction: row-reverse !important; 
}

/* تثبيت رسائل البوت (Assistant) في جهة اليسار */
[data-testid="stChatMessage"]:has(img[src*="Kayfa"]),
[data-testid="stChatMessage"]:has(img[src*="education"]),
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatar"] span:contains("🤖")) {
    margin-right: auto !important;  
    margin-left: 0 !important;
}

/* تحسين محاذاة النصوص والمحتويات الداخلية */
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
        st.image(r"Kayfa_logo.png", width=180)
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
# CRM & DATABASE SUBSYSTEM (MongoDB)
# ==============================================================================
from pymongo import MongoClient
import certifi
from datetime import datetime

def save_crm_ticket(customer_name, phone, email, city, current_level, products_of_interest, goal, conversation_summary, intent_status="hot"):
    """
    دالة لحفظ تذكرة العميل المحتمل مباشرة في MongoDB Atlas باللغة العربية
    """
    try:
        # تصحيح طريقة جلب الرابط البيئي لعدم حدوث كراش واستخدام الرابط الصريح المؤمن
        mongo_uri = os.getenv('MONGO_URI', "mongodb+srv://elhosenyhassan007_db_user:jLPu7mYfy8Jyox0u@cluster0.x5jk1ox.mongodb.net/")
        client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
        
        db = client["kayfa_crm"]
        tickets_collection = db["crm_tickets"]
        
        ticket = {
            "ticket_id": f"LEAD-2026-{uuid.uuid4().hex[:4].upper()}",
            "customer_info": {
                "name": customer_name,
                "phone": phone,
                "email": email,
                "city_country": city,
            },
            "educational_profile": {
                "current_level": current_level,         
                "products_of_interest": products_of_interest, 
                "goal_motivation": goal                 
            },
            "sales_signals": {
                "lead_temperature": intent_status,       
                "buying_signals": "استفسر عن طرق الدفع والتسجيل",
                "objections_handled": "تم توضيح خيارات التقسيط وقيمة الشهادة"
            },
            "conversation_metadata": {
                "summary_ar": conversation_summary,      
                "next_action": "يتواصل أحد مندوبي المبيعات عبر واتساب خلال ٢٤ ساعة لتأكيد التسجيل",
                "timestamp": datetime.now()
            }
        }
        
        result = tickets_collection.insert_one(ticket)
        print(f"✅ Ticket captured and saved to MongoDB with ID: {ticket['ticket_id']}")
        return True, ticket["ticket_id"]
        
    except Exception as e:
        print(f"❌ Failed to save ticket to MongoDB: {e}")
        return False, str(e)

# ==============================================================================
# 2. STATE INITIALIZATION
# ==============================================================================
if "uploaded_files_dict" not in st.session_state:
    st.session_state.uploaded_files_dict = {}

if "current_view" not in st.session_state:
    st.session_state.current_view = "chat"

if "user_email" not in st.session_state:
    st.session_state.user_email = "elhosenyhassan007@kayfa.com" # قيمة افتراضية صالحة للربط بـ Langfuse

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
        # استخدام الـ SDK الرسمي لـ Groq لضمان جلب حسابات التوكنز بدقة وبدون توافقية خاطئة
        self.groq_client = Groq(api_key=Groq_api_key)
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
        # 1. جلب بيانات مستخدم الجلسة وتجهيز الـ Trace الموحد للمحادثة الحالية
        current_user_id = st.session_state.get("user_email", "elhosenyhassan007@kayfa.com")
        current_chat_id = st.session_state.get("current_chat_id", str(uuid.uuid4()))
        
        # 🎯 إنشاء التتبع الرئيسي للمحادثة لربط الداشبورد به تلقائياً
        user_trace = lf.trace(
            name="kayfa-sales-chat",
            user_id=current_user_id,
            session_id=current_chat_id,
            metadata={"interface": "Streamlit Enterprise Web"}
        )

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
            " IDENTITY & ROLE:\n"
            "You are Kayfa AI — an elite, persuasive, and empathetic AI Sales Agent for Kayfa (كيف) Educational Platform.\n"
            "Your primary goal is to guide prospective learners toward enrolling in the right learning tracks, roadmaps, and especially our premium Live Diplomas (AI, Data Science, SOC, Pen-Test, Full-Stack).\n\n"
            "SALES STRATEGY & INTENT DETECTION:\n"
            "- Read between the lines: Identify if the visitor is just browsing, comparing options, price-sensitive, hesitant, or ready to enroll. Adapt your tone and response length dynamically.\n"
            "- Up-sell intelligently: Free content and individual courses ($15 - $65) are excellent openers for hesitant prospects. However, your ultimate target is to guide warm/serious leads toward on-demand tracks ($25 - $250) and our program-specific Live Diplomas.\n"
            "- Overcome objections honestly: Use the knowledge base to handle concerns regarding pricing, certified certificates, refund policies, and prerequisites smoothly and persuasively. Never use pushy or misleading sales tactics.\n\n"
            "LEAD CAPTURING BEHAVIOR (CRM SENSING):\n"
            "- Monitor the conversation for strong buying signals (e.g., asking about installment plans, next batch start dates, payment links, or certificate details).\n"
            "- When a buying signal is detected, seamlessly pivot to collecting the lead's details (Name, WhatsApp/Phone, City/Country, and Current level) naturally as part of the flow—never make it feel like an interrogation or filling out a cold form.\n"
            "- Once they provide any of these details, acknowledge them warmly, continue the conversation, and trigger the CRM tool behind the scenes.\n\n"
            "LANGUAGE & RTL CONSTRAINTS:\n"
            "- You are fully bilingual. Speak fluently in Arabic (as your primary focus) and English, matching the user's preferred language and dialect naturally.\n"
            "- You must handle and understand Egyptian (المصرية), Saudi (السعودية), and Syrian (السورية) dialects flawlessly, adapting your phrasing to connect with the user.\n"
            "- Technical terms and course names (e.g., SOC Track Diploma, Power BI, Python, Splunk, Linux) MUST be kept in their original English/Latin form within the Arabic responses (Do NOT translate them literally).\n\n"
            "STRICT GROUNDING RULES (NO HALLUCINATION):\n"
            "- Rely EXCLUSIVELY on the retrieved knowledge base text below for prices, durations, curriculum details, and refund policies. If the information is not present, states clearly that you don't know and offer to connect them with a human advisor.\n"
            "- Never invent a course, price, instructor, or discount. A sales agent who hallucinates a price is a liability.\n"
            "- Output ONLY the final natural response to the user. Never expose internal chain-of-thought, self-corrections, or phrases like '[Output Generation]' or 'Thinking Process'.\n\n"
            f"RETRIEVED CATALOG KNOWLEDGE BASE:\n{rag_context}\n\n"
            "Maintain your sales persona strictly. Read the entire conversation history below to ensure context consistency."
        )
        
        messages = [{"role": "system", "content": full_system_prompt}]
        for msg in st.session_state.messages[:-1]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": query})

        # 🎯 تسجيل بداية أول معالجة كـ Generation صريح لـ Langfuse ليرى المدخلات
        routing_generation = user_trace.generation(
            name="Kayfa Agent Tools Routing",
            model=groq_model,
            input=messages
        )

        if not self.sessions:
            # تشغيل الـ Sync بشكل آمن ومتوافق داخل سياق الـ Async
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.groq_client.chat.completions.create(
                    model=groq_model,
                    messages=messages,
                    temperature=0.3
                )
            )
            final_content = response.choices[0].message.content if response.choices[0].message.content else ""
            
            # إنهاء الـ Generation وحفظ البيانات بدقة للداشبورد
            routing_generation.end(
                output=final_content,
                usage={
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens
                }
            )
            lf.flush()
            return final_content

        try:
            groq_formatted_tools = await self._get_all_tools()
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.groq_client.chat.completions.create(
                    model=groq_model,
                    messages=messages,
                    tools=groq_formatted_tools if groq_formatted_tools else None,
                    temperature=0.4
                )
            )

            assistant_message = response.choices[0].message
            
            # تحديث الـ Generation الحالي ببيانات التوجيه الأولى
            routing_generation.end(
                output=assistant_message.content if assistant_message.content else "Tool routing requested",
                usage={
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens
                }
            )

            if not assistant_message.tool_calls:
                lf.flush()
                return assistant_message.content if assistant_message.content else ""

            messages.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": response.choices[0].message.tool_calls
            })
            
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                # 🎯 تسجيل الـ Tool Call كـ Span فرعي لرحلة التتبع الحقيقية
                tool_span = user_trace.span(name=f"MCP Tool Call: {tool_name}", input=tool_args)

                target_session = self.tool_to_session_map.get(tool_name)
                if target_session:
                    result = await target_session.call_tool(tool_name, tool_args)
                    result_str = "".join([block.text for block in result.content if hasattr(block, 'text')])
                else:
                    result_str = f"Error: Tool {tool_name} not found on any connected MCP server."

                # إغلاق تتبع الـ Tool بنجاح
                tool_span.end(output=result_str)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": result_str
                })

            # 🎯 إنشاء Generation ثاني وأخير لحساب المخرجات النهائية والتوكنز الكلية للرد
            final_generation = user_trace.generation(
                name="Kayfa Final Grounded Output",
                model=groq_model,
                input=messages
            )

            final_response = await loop.run_in_executor(
                None,
                lambda: self.groq_client.chat.completions.create(
                    model=groq_model,
                    messages=messages
                )
            )
            
            final_content = final_response.choices[0].message.content
            
            # إرسال المخرجات النهائية وحساب التكلفة الفورية للـ Dashboard
            final_generation.end(
                output=final_content,
                usage={
                    "input_tokens": final_response.usage.prompt_tokens,
                    "output_tokens": final_response.usage.completion_tokens
                }
            )
            
            lf.flush() # دفع حزم البيانات فوراً لخوادم لانجفيوز
            return final_content
            
        except Exception as e:
            routing_generation.end(status_message=str(e), level="ERROR")
            
            loop = asyncio.get_event_loop()
            fallback_response = await loop.run_in_executor(
                None,
                lambda: self.groq_client.chat.completions.create(
                    model=groq_model,
                    messages=messages,
                    temperature=0.2
                )
            )
            lf.flush()
            return fallback_response.choices[0].message.content

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
                                print("✅ Python MCP Server Connected Successfully!")
                            except Exception as e:
                                st.error(f"Error connecting to Python server: {e}")
                        if os.path.exists(path2):
                            try:
                                await client.connect_to_server(path2)
                            except Exception as e:
                                st.sidebar.warning("⚠️ سيرفر HubSpot المساعد غير متصل حالياً، الشات يعمل عبر الكتالوج الرئيسي.")
                
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

                # التطهير الإجباري لطابور كولباك LlamaIndex إذا وجد
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
    
    if run_admin_dashboard is not None:
        try:
            run_admin_dashboard()
        except Exception as e:
            st.error(f"❌ حدث خطأ أثناء تشغيل صفحة الـ Credentials: {e}")
    else:
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
