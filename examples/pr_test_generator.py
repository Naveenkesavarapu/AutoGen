import os
import sys
import re
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.cursor_client import CursorClient
from src.config import Config

def parse_pr_number(pr_url):
    """Extract PR number from Bitbucket URL."""
    match = re.search(r'pull-requests/(\d+)', pr_url)
    if match:
        return int(match.group(1))  # Convert to int since API expects integer
    raise ValueError("Could not extract PR number from URL")

def main():
    # Load and validate configuration
    config = Config()
    config.prompt_for_credentials()
    
    # Initialize the client with configuration
    client = CursorClient(
        base_url=config.mcp_url,
        bitbucket_url=config.bitbucket_url,
        bitbucket_api_key=config.bitbucket_api_key
    )

    # PR URL to analyze - using the repository from config
    pr_url = f"https://bitbucket.org/{config.bitbucket_org}/{config.bitbucket_repo}/pull-requests/21991"
    print(f"\nAnalyzing PR: {pr_url}")
    
    try:
        # Extract PR number
        pr_number = parse_pr_number(pr_url)
        repo = f"{config.bitbucket_org}/{config.bitbucket_repo}"
        print(f"Fetching details for PR #{pr_number} from repository: {repo}")
        # 
        # First get basic PR details
        pr_details = client.get_pr_details(repo, pr_number)
        print("\nPull Request Details:")
        print("-" * 50)
        print(f"Title: {pr_details.get('title')}")
        print(f"Author: {pr_details.get('author', {}).get('display_name')}")
        print(f"State: {pr_details.get('state')}")
        print(f"Source Branch: {pr_details.get('source', {}).get('branch', {}).get('name')}")
        print(f"Target Branch: {pr_details.get('destination', {}).get('branch', {}).get('name')}")

        # Generate test analysis for the PR
        print("\nGenerating test analysis...")
        analysis = client.generate_pr_tests(
            ticket_id="AUTO-1",  # Using a placeholder ticket ID
            repo=repo,
            pr_id=pr_number,
            workspace_root=str(project_root)
        )
        
        # Display test cases
        print("\nGenerated Test Cases:")
        print("-" * 50)
        for test_case in analysis.get('test_cases', []):
            print(f"\nTest: {test_case.get('name')}")
            print(f"Description: {test_case.get('description')}")
            if test_case.get('steps'):
                print("\nSteps:")
                for step in test_case['steps']:
                    print(f"- {step}")
        
        # Create test files if suggested
        if analysis.get('test_files'):
            output_dir = config.test_output_path
            print(f"\nCreating test files in: {output_dir}")
            test_file_path = create_test_file(analysis, str(output_dir))
            print(f"Created test file: {test_file_path}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 