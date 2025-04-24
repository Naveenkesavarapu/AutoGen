# AutoGen Project

This repository contains the AutoGen project with a clean and organized structure.

## Project Structure

```
.
├── config/                 # Configuration files
│   ├── mcp-server.nginx.conf
│   ├── mcp-server.service
│   └── mcp.json
├── src/                   # Source code
│   ├── mcp_server/       # Server implementation
│   ├── models/           # Data models
│   ├── services/         # Business logic services
│   ├── ui/              # User interface components
│   ├── utils/           # Utility functions
│   ├── main.py          # Main application entry point
│   └── use_mcp.py       # MCP usage implementation
├── scripts/              # Utility scripts
├── requirements.txt      # Python dependencies
├── run.py               # Application runner
└── README.md            # Project documentation
```

## Setup and Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the server:
```bash
python src/mcp_server/run_server.py
```

2. Run the main application:
```bash
python run.py
```

## Development

- The project follows a modular structure with clear separation of concerns
- Configuration files are stored in the `config` directory
- Core business logic is in the `src` directory
- Utility scripts are in the `scripts` directory

## License

[Add your license information here]

# Cursor MCP Integration

This project provides integration with Cursor's MCP server for automated test generation and other IDE-related functionalities.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure the MCP server is running (default: http://localhost:5000)

## Usage

The project provides a `CursorClient` class that handles communication with the MCP server. Here's how to use it:

```python
from src.cursor_client import CursorClient

# Initialize the client
client = CursorClient(base_url="http://localhost:5000")

# Check server health
health = client.check_server_health()

# Generate tests for source files
result = client.generate_tests(
    ticket_id="PROJ-123",
    source_files=["path/to/source1.py", "path/to/source2.py"],
    workspace_root="/path/to/workspace"
)
```

See `examples/cursor_example.py` for a complete example of how to use the client.

## Features

- Server health check
- Automated test generation based on source files
- Jira ticket integration
- Test file creation in specified output directory

## API Endpoints

The client interacts with the following MCP server endpoints:

- `GET /health` - Check server health
- `POST /cursor/generate_tests` - Generate tests for source files
- `GET /jira/ticket/{ticket_id}` - Get Jira ticket details

## Error Handling

The client includes robust error handling for:
- Connection issues
- Invalid responses
- Missing files
- Permission errors

## Logging

The client uses Python's built-in logging module. You can configure logging level and handlers as needed:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Contributing

Feel free to submit issues and pull requests for additional features or bug fixes.

# Cursor Test Generator

A tool for automatically generating test cases from code using the Cursor AI platform.

## Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.env`:
```bash
MCP_URL=http://localhost:5000
MCP_WORKSPACE_ROOT=/path/to/your/workspace
MCP_TEST_OUTPUT_DIR=tests/generated

# Bitbucket Configuration
BITBUCKET_URL=https://bitbucket.org
BITBUCKET_API_KEY=your_api_key_here  # Changed from BITBUCKET_TOKEN
BITBUCKET_ORG=your_organization
BITBUCKET_REPO=your_repository
```

## Authentication

The application uses Bitbucket's API key authentication. To get your API key:

1. Log in to Bitbucket
2. Go to your personal settings
3. Navigate to "API Keys" under "Access Management"
4. Create a new API key with appropriate permissions
5. Copy the API key and add it to your `.env` file as `BITBUCKET_API_KEY`

## Usage

### Basic Example
```python
from src.cursor_client import CursorClient

# Initialize client
client = CursorClient(
    base_url="http://localhost:5000",
    bitbucket_url="https://bitbucket.org",
    bitbucket_api_key="your_api_key_here"  # Changed from bitbucket_token
)

# Get PR details
pr_details = client.get_pr_details("org/repo", 123)
print(pr_details)
```

### Running Examples
```bash
# Run the basic example
python examples/cursor_example.py

# Generate tests from a PR
python examples/pr_test_generator.py
```

## Development

### Running Tests
```bash
pytest tests/
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details 