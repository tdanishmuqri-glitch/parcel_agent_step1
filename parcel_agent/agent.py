import sys
from pathlib import Path

from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

from .faq import search_faq

# Connect to our tracking MCP server. ADK starts tracking_server.py as a
# separate process and asks it which tools it offers (here: track_parcel).
tracking_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,  # the same Python as this project (.venv)
            args=[str(Path(__file__).parent / "tracking_server.py")],
        ),
        timeout=30,
    ),
)

root_agent = Agent(
    name="parcel_support_agent",
    model="gemini-3.8-flash",
    instruction="""
You are a friendly customer support agent for a parcel delivery company.
Reply in the same language as the customer (English or Bahasa Melayu).

1. If the customer asks where their parcel is, ask for the tracking number,
   then call track_parcel. Only use information returned by the tool.
   If the parcel is not found, ask them to double-check the number.

2. If the customer asks about rules or services (what they can send,
   rescheduling, customs, delivery times, damaged or lost parcels, etc.),
   call search_faq first and answer ONLY from the FAQ results.
   If the results do not actually answer the question, say you are not sure
   and offer to pass them to a human agent. Never make up company policies.

A question can need both tools, e.g. "my parcel MY1004 is stuck, why?"

Keep replies short and polite.
""",
    tools=[tracking_tools, search_faq],
)
