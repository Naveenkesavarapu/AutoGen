# AutoGen - Automated Test Case Generator

A Windows application that automatically generates test cases from Jira tickets and pushes them to TestRail.

## Features

- Fetch Jira ticket details using ticket URL
- Analyze code changes from Git repositories
- Generate test cases using AI (GPT/Claude)
- Push generated test cases to TestRail
- User-friendly GUI interface

## Setup

1. Install Python 3.8 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your credentials:
   ```
   JIRA_URL=your_jira_instance_url
   JIRA_EMAIL=your_email
   JIRA_API_TOKEN=your_api_token
   
   TESTRAIL_URL=your_testrail_url
   TESTRAIL_EMAIL=your_email
   TESTRAIL_API_KEY=your_api_key
   
   OPENAI_API_KEY=your_openai_api_key
   ```

## Running the Application

Run the main application:
```bash
python src/main.py
```

## Project Structure

- `src/` - Source code directory
  - `main.py` - Main application entry point
  - `ui/` - GUI components
  - `services/` - Core services (Jira, Git, TestRail integration)
  - `models/` - Data models
  - `utils/` - Utility functions

## License

MIT License 