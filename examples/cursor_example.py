from src.cursor_client import CursorClient
import os

def main():
    # Initialize the client with Bitbucket configuration
    client = CursorClient(
        base_url="http://localhost:5000",
        bitbucket_url="https://bitbucket.org",
        bitbucket_api_key=os.getenv("BITBUCKET_API_KEY")  # Changed from BITBUCKET_TOKEN
    )
    
    # Check server health
    health = client.check_server_health()
    print(f"Server health: {health}")
    
    # Example: Generate tests for a Jira ticket
    ticket_id = "PROJ-123"  # Replace with your ticket ID
    workspace_root = os.getcwd()
    source_files = [
        "src/cursor_client.py",
        "src/mcp_server/server.py"
    ]
    
    # Get ticket details
    ticket_details = client.get_ticket_details(ticket_id)
    print(f"\nTicket details: {ticket_details}")
    
    # Example: Get PR details
    try:
        pr_details = client.get_pr_details("zenotiengineeringteam/maindbsql", 21991)
        print(f"\nPR details: {pr_details}")
    except ValueError as e:
        print(f"Error getting PR details: {e}")

if __name__ == "__main__":
    main() 