import json
import pandas as pd
import uuid
import os
import smtplib
from datetime import datetime
from typing import List, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# مكتبات MongoDB الرسمية مع شهادة الأمان لمنع كراش الاتصال
from pymongo import MongoClient
import certifi

from mcp.server.fastmcp import FastMCP

# Initialize MCP Server
mcp = FastMCP("stock-ai-tools")

# ==============================================================================
# 🎯 NEW TOOL: MONGODB CRM LEAD CAPTURING
# ==============================================================================
@mcp.tool()
async def save_kayfa_crm_lead(
    customer_name: str,
    phone: str,
    current_level: str,
    email: str = "لم يذكر بعد",
    city: str = "غير محدد",
    products_of_interest: str = "منصة كيف التعليمية",
    goal: str = "تطوير المهارات التقنية",
    conversation_summary: str = "استفسار أولي وتجميع بيانات التواصل الأساسية") -> str:
    """
    Use this tool to save a qualified customer lead into MongoDB CRM Atlas 
    as soon as the user provides their core credentials: Username, Level, and Phone number.
    """
    try:
        mongo_uri = "mongodb+srv://elhosenyhassan007_db_user:jLPu7mYfy8Jyox0u@cluster0.x5jk1ox.mongodb.net/"
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
                "lead_temperature": "hot",       
                "buying_signals": "العميل سجل بياناته الأساسية (الاسم، الهاتف، المستوى) بنجاح",
                "objections_handled": "تم الالتقاط الأوتوماتيكي الفوري لبدء المتابعة مبيعاتياً"
            },
            "conversation_metadata": {
                "summary_ar": conversation_summary,      
                "timestamp": datetime.now()
            }
        }
        
        tickets_collection.insert_one(ticket)
        return f"✅ Success: Lead captured and registered into MongoDB with Ticket ID: {ticket['ticket_id']}"
        
    except Exception as e:
        return f"❌ Failed to save lead to MongoDB CRM: {str(e)}"

@mcp.tool()
async def get_stock_info(symbol: str) -> str:
    """Get basic information and current price for a stock symbol"""
    try:
        return f"""
Stock: {symbol.upper()}
Current Price: $245.67 (Mock Data)
Change: +2.34 (+0.96%)
Volume: 12.4M
Market Cap: $1.23T
Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
        """
    except Exception as e:
        return f"Error fetching stock info: {str(e)}"


@mcp.tool()
async def analyze_uploaded_data(query: str) -> str:
    """Analyze the uploaded CSV dataset. Use this when user asks about the uploaded file."""
    return "This tool will analyze the uploaded dataset. The client will provide context."


@mcp.tool()
async def technical_analysis(symbol: str, indicator: str = "all") -> str:
    """Perform technical analysis on a stock"""
    indicators = ["SMA", "EMA", "RSI", "MACD"]
    if indicator.lower() != "all":
        indicators = [indicator.upper()]
    
    result = f"Technical Analysis for {symbol.upper()}\n\n"
    for ind in indicators:
        result += f"{ind}: Bullish Signal (Mock)\n"
    return result


@mcp.tool()
async def get_stock_recommendation(symbol: str) -> str:
    """Get investment recommendation (Buy, Sell, Hold) for a specific stock with target price and analysis."""
    symbol_upper = symbol.upper()
    
    if symbol_upper in ["NVDA", "TSLA", "AMD", "AAPL"]:
        rec = "STRONG BUY"
        target = "$290.00"
        reason = "Strong momentum, high volume expansion, and bullish moving average crossovers."
    elif symbol_upper in ["MSFT", "GOOGL", "AMZN"]:
        rec = "BUY / HOLD"
        target = "$460.00"
        reason = "Consolidating near historical support lines with stable RSI metrics."
    else:
        rec = "HOLD"
        target = "Market Value"
        reason = "Neutral indicators with declining volatility. Awaiting major volume breakout."

    return f"""
📈 INVESTMENT RECOMMENDATION FOR {symbol_upper}
--------------------------------------------------
Recommendation: Status -> **{rec}**
Target Price (12M): {target}
Risk Rating: Medium
Analysis Summary: {reason}
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}
"""


@mcp.tool()
async def calculate_portfolio_performance(
    holdings: List[Dict[str, Any]],
    period: str = "1y"
) -> str:
    """Calculate portfolio performance"""
    total_value = 0
    for holding in holdings:
        total_value += holding.get("shares", 0) * holding.get("price", 0)
    
    return f"""
Portfolio Summary:
Total Holdings: {len(holdings)} stocks
Estimated Total Value: ${total_value:,.2f}
Period: {period}
Recommendation: Diversified Portfolio - Good Risk Management
    """


@mcp.tool()
async def get_market_summary() -> str:
    """Get general market summary"""
    return """
Market Summary (Mock Data):
• S&P 500: +0.8%
• NASDAQ: +1.2%
• Dow Jones: +0.4%
• VIX: 18.5 (Moderate Fear)
• Top Gainers: NVDA, TSLA, AMD
• Top Losers: Some traditional stocks
    """

# 🎯 التعديل والإصلاح الجوهري هنا:
@mcp.tool()
async def send_confirmation_email(user_email: str, user_name: str, experience_level: str) -> str:
    """
    Send a confirmation and onboarding email to the user when they provide their enrollment details 
    (Name, Email, and Experience level) for Kayfa programs.
    """
    sender_email = "your_academy@gmail.com"
    sender_password = "your_app_password"  # باسورد التطبيقات الخاص بحساب جوجل (App Password)
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = user_email
    msg['Subject'] = "تأكيد التسجيل في برنامج Data Science - منصة كيفَ"
    
    body = f"""
أهلاً يا {user_name}،

تم استلام بياناتك بنجاح لمستوى ({experience_level}):
برجاء العلم أنه تم تسجيلك مبدئياً في برنامج الـ Data Science وجاري تحضير جدول المحاضرات وإرساله لك قريباً.

بالتوفيق،
فريق العمل بمنصة كيفَ
    """
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    try:
        # الاتصال بسيرفر جوجل لإرسال الإيميل حقيقياً
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return f"SUCCESS: Confirmation email sent successfully to {user_email}!"
    except Exception as e:
        return f"ERROR: Failed to send email due to: {str(e)}"


# ====================== MAIN ======================
if __name__ == "__main__":
    mcp.run(transport="stdio")
