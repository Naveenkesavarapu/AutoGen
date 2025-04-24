"""
Script to demonstrate using the MCP server.
"""
import requests
import json
from pprint import pprint

def test_health():
    """Test the health check endpoint."""
    response = requests.get('http://localhost:5000/health')
    print("\nHealth Check Response:")
    pprint(response.json())
    return response.status_code == 200

def generate_test_case():
    """Generate a test case using the MCP server."""
    payload = {
        "issue": {
            "key": "PD-250067",
            "fields": {
                "summary": "Swagger MCP",
                "description": """
                Implement Swagger documentation for the MCP API.
                
                Technical Details:
                - Use swagger-ui-express for API documentation
                - Document all endpoints and their request/response formats
                - Include authentication requirements
                - Add example requests and responses
                """,
                "issuetype": {
                    "name": "Task"
                }
            }
        }
    }

    print("\nSending test case generation request for PD-250067...")
    response = requests.post(
        'http://localhost:5000/webhook/jira',
        json=payload
    )
    
    print("\nTest Case Generation Response:")
    pprint(response.json())
    return response.status_code == 200

def main():
    """Main function to demonstrate MCP usage."""
    print("Testing MCP Server...")
    
    # Test health check
    if test_health():
        print("\n✅ Health check passed")
    else:
        print("\n❌ Health check failed")
        return
    
    # Generate test case
    if generate_test_case():
        print("\n✅ Test case generation successful")
    else:
        print("\n❌ Test case generation failed")

if __name__ == '__main__':
    main() 