"""MCP server for the parcel tracking system.

This is a SEPARATE small program. It owns the tracking data and offers one
tool, track_parcel, using the Model Context Protocol (MCP).

Any MCP-compatible AI app (our ADK agent, Claude, IDE assistants...) can
connect to it and use the tool, without knowing how tracking works inside.
In a real company, this server would sit in front of the real tracking database.
"""
from mcp.server.mcpserver import MCPServer

server = MCPServer("parcel-tracking")

# Pretend parcel database - now lives here, not in the agent.
PARCELS = {
    "MY1001": {"status": "Out for delivery", "location": "Cyberjaya hub", "eta": "Today, before 6pm"},
    "MY1002": {"status": "In transit", "location": "Shah Alam sorting centre", "eta": "Tomorrow"},
    "MY1003": {"status": "Delivered", "location": "Nilai", "eta": "Delivered yesterday at 3:15pm"},
    "MY1004": {"status": "On hold - customs check", "location": "KLIA customs", "eta": "Unknown"},
}


@server.tool()
def track_parcel(tracking_number: str) -> dict:
    """Look up the current status of a parcel.

    Args:
        tracking_number: The parcel tracking number, for example "MY1001".
    """
    parcel = PARCELS.get(tracking_number.strip().upper())
    if parcel is None:
        return {"found": False}
    return {"found": True, "tracking_number": tracking_number.upper(), **parcel}


if __name__ == "__main__":
    server.run()  # talks to the agent over stdin/stdout ("stdio")
