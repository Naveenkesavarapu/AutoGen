import requests
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class CursorClient:
    """Client for interacting with MCP server from Cursor"""
    
    def __init__(self, 
                 base_url: str = "http://localhost:5000",
                 bitbucket_url: Optional[str] = None,
                 bitbucket_api_key: Optional[str] = None):
        """
        Initialize the cursor client
        
        Args:
            base_url: MCP server URL
            bitbucket_url: Bitbucket server URL
            bitbucket_api_key: Bitbucket API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.bitbucket_url = bitbucket_url.rstrip('/') if bitbucket_url else None
        self.session = requests.Session()
        if bitbucket_api_key:
            self.session.headers.update({
                "x-api-key": bitbucket_api_key,
                "Content-Type": "application/json"
            })
    
    def check_server_health(self) -> Dict:
        """Check if the MCP server is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            raise
    
    def generate_tests(self, 
                      ticket_id: str, 
                      source_files: Optional[List[str]] = None,
                      workspace_root: Optional[str] = None) -> Dict:
        """
        Generate tests using the MCP server
        
        Args:
            ticket_id: Jira ticket ID
            source_files: List of source files to analyze
            workspace_root: Root directory of the workspace
            
        Returns:
            Dictionary containing generated tests and analysis
        """
        try:
            # Prepare source files
            if source_files and workspace_root:
                # Convert paths to be relative to workspace root
                workspace_path = Path(workspace_root)
                source_files = [
                    str(Path(f).relative_to(workspace_path))
                    for f in source_files
                ]
            
            # Prepare request payload
            payload = {
                "ticket_id": ticket_id,
                "source_files": source_files or []
            }
            
            # Make request to server
            response = self.session.post(
                f"{self.base_url}/cursor/generate_tests",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Log test generation summary
            test_count = len(result.get('test_cases', []))
            file_count = len(result.get('test_files', []))
            logger.info(f"Generated {test_count} test cases and {file_count} test file suggestions")
            
            return result
            
        except Exception as e:
            logger.error(f"Test generation failed: {str(e)}")
            raise
    
    def get_ticket_details(self, ticket_id: str) -> Dict:
        """Get Jira ticket details with code analysis"""
        try:
            response = self.session.get(f"{self.base_url}/jira/ticket/{ticket_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get ticket details: {str(e)}")
            raise

    def get_pr_details(self, repo: str, pr_id: int) -> Dict:
        """
        Get pull request details from Bitbucket
        
        Args:
            repo: Repository name (format: org/repo)
            pr_id: Pull request ID
            
        Returns:
            Dictionary containing PR details
        """
        if not self.bitbucket_url:
            raise ValueError("Bitbucket URL not configured")
            
        try:
            url = f"{self.bitbucket_url}/repositories/{repo}/pullrequests/{pr_id}"
            print(f"Requesting PR details from: {url}")  # Debug logging
            response = self.session.get(url)
            
            if response.status_code == 401:
                logger.error("Authentication failed. Please check your Bitbucket API key.")
                raise ValueError("Invalid Bitbucket API key")
            elif response.status_code == 404:
                logger.error(f"PR not found. URL: {url}")
                raise ValueError(f"PR #{pr_id} not found")
                
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get PR details: {str(e)}")
            raise

    def get_pr_changes(self, repo: str, pr_id: int) -> Dict:
        """
        Get changes (diff) from a pull request
        
        Args:
            repo: Repository name (format: org/repo)
            pr_id: Pull request ID
            
        Returns:
            Dictionary containing file changes
        """
        if not self.bitbucket_url:
            raise ValueError("Bitbucket URL not configured")
            
        try:
            url = f"{self.bitbucket_url}/repositories/{repo}/pullrequests/{pr_id}/diff"
            print(f"Requesting PR changes from: {url}")  # Debug logging
            response = self.session.get(url)
            
            if response.status_code == 401:
                logger.error("Authentication failed. Please check your Bitbucket API key.")
                raise ValueError("Invalid Bitbucket API key")
            elif response.status_code == 404:
                logger.error(f"PR not found. URL: {url}")
                raise ValueError(f"PR #{pr_id} not found")
                
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get PR changes: {str(e)}")
            raise

    def generate_pr_tests(self,
                         ticket_id: str,
                         repo: str,
                         pr_id: int,
                         workspace_root: Optional[str] = None) -> Dict:
        """
        Generate tests by analyzing a pull request
        
        Args:
            ticket_id: Jira ticket ID
            repo: Repository name
            pr_id: Pull request ID
            workspace_root: Root directory of workspace
            
        Returns:
            Dictionary containing generated tests and analysis
        """
        try:
            # Get PR details and changes
            pr_details = self.get_pr_details(repo, pr_id)
            pr_changes = self.get_pr_changes(repo, pr_id)
            
            # Extract changed files
            changed_files = [
                change['path']['toString']
                for change in pr_changes.get('values', [])
            ]
            
            # Get ticket details for context
            ticket_details = self.get_ticket_details(ticket_id)
            
            # Generate tests with PR context
            payload = {
                "ticket_id": ticket_id,
                "source_files": changed_files,
                "pr_context": {
                    "source_branch": pr_details['fromRef']['displayId'],
                    "target_branch": pr_details['toRef']['displayId'],
                    "title": pr_details['title'],
                    "description": pr_details['description'],
                    "ticket_details": ticket_details
                }
            }
            
            if workspace_root:
                payload["workspace_root"] = workspace_root
            
            response = self.session.post(
                f"{self.base_url}/cursor/generate_tests",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Generated {len(result.get('test_cases', []))} test cases for PR #{pr_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate PR tests: {str(e)}")
            raise

def create_test_file(test_data: Dict, output_dir: str) -> str:
    """
    Create a test file from generated test data
    
    Args:
        test_data: Test data from server
        output_dir: Directory to create test file in
        
    Returns:
        Path to created test file
    """
    try:
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Get test file suggestion
        test_file = test_data['test_files'][0]['test_file']
        file_path = Path(output_dir) / Path(test_file).name
        
        # Write test code
        test_code = test_data['test_snippets'][0]['code']
        file_path.write_text(test_code)
        
        logger.info(f"Created test file: {file_path}")
        return str(file_path)
        
    except Exception as e:
        logger.error(f"Failed to create test file: {str(e)}")
        raise 