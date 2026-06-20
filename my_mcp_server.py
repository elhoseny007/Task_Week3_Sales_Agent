import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

from mcp.server.fastmcp import FastMCP

# Initialize MCP Server
mcp = FastMCP("stock-ai-tools")

# ====================== TOOLS ======================

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
    
    # محاكاة ذكية للتوصيات بناءً على الرموز الشهيرة
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

# ====================== MAIN ======================
if __name__ == "__main__":
    # التشغيل الصريح عبر stdio لضمان التوافق الكامل مع الـ Client في Streamlit
    mcp.run(transport="stdio")


