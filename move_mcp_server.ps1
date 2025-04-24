# PowerShell script to move MCP server files to standalone package

# Create necessary directories
New-Item -ItemType Directory -Force -Path "..\mcp_server_standalone\src\mcp_server\config"

# Copy MCP server files
Copy-Item ".\src\mcp_server\*.py" -Destination "..\mcp_server_standalone\src\mcp_server\"
Copy-Item ".\src\mcp_server\config\*" -Destination "..\mcp_server_standalone\src\mcp_server\config\"

# Create example .env file
@"
# Jira Configuration
JIRA_URL=your_jira_url
JIRA_USERNAME=your_jira_username
JIRA_TOKEN=your_jira_api_token

# TestRail Configuration
TESTRAIL_URL=your_testrail_url
TESTRAIL_EMAIL=your_testrail_email
TESTRAIL_TOKEN=your_testrail_api_token

# Server Configuration
FLASK_SECRET_KEY=your_secret_key
FLASK_ENV=development

# Optional Configuration
TESTRAIL_SECTION_ID=1
TESTRAIL_PROJECT_ID=1
WEBHOOK_SECRET=your_webhook_secret
"@ | Out-File -FilePath "..\mcp_server_standalone\.env.example" -Encoding UTF8

Write-Host "MCP Server files have been moved to mcp_server_standalone directory."
Write-Host "You can now install it as a package in other projects." 