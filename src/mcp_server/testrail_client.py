"""
TestRail API client for MCP server.
"""
import os
import requests
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class TestRailClient:
    def __init__(self, url=None, username=None, password=None):
        """Initialize TestRail client."""
        self.url = url.rstrip('/') if url else None
        self.username = username  # This should be the email address
        self.password = password  # This should be the API token
        self.session = None
        self.connection_error = None
        
        if not all([url, username, password]):
            missing = []
            if not url: missing.append('TESTRAIL_URL')
            if not username: missing.append('TESTRAIL_EMAIL')  # Changed from USERNAME to EMAIL
            if not password: missing.append('TESTRAIL_TOKEN')  # Using TOKEN instead of PASSWORD
            self.connection_error = f"Missing required environment variables: {', '.join(missing)}"
            logger.warning(self.connection_error)
            return
            
        try:
            logger.info(f"Initializing TestRail client for {self.url} with username {self.username}")
            self.session = requests.Session()
            self.session.auth = (self.username, self.password)
            self.session.headers.update({'Content-Type': 'application/json'})
            
            # Test connection
            response = self.session.get(f"{self.url}/api/v2/get_user_by_email&email={self.username}")
            if response.status_code == 200:
                logger.info("Successfully connected to TestRail")
                self.connection_error = None
            else:
                self.session = None
                self.connection_error = f"TestRail authentication failed: {response.status_code}"
                logger.error(self.connection_error)
        except Exception as e:
            self.session = None
            self.connection_error = f"Failed to initialize TestRail client: {str(e)}"
            logger.error(self.connection_error)
            
    def is_connected(self) -> bool:
        """Check if client is properly connected."""
        return self.session is not None
        
    def get_connection_error(self) -> Optional[str]:
        """Get the connection error message if any."""
        return self.connection_error
        
    def create_test_case(self, test_case: Dict[str, Any]) -> Optional[int]:
        """Create a test case in TestRail."""
        if not self.is_connected():
            error = self.get_connection_error() or "TestRail client not connected"
            logger.warning(error)
            return None
            
        try:
            section_id = int(os.getenv('TESTRAIL_DEFAULT_SECTION_ID', '1'))
            data = {
                'title': test_case['title'],
                'type_id': 1,  # Automated test case
                'priority_id': 2,  # Medium priority
                'estimate': '1m',  # 1 minute estimate
                'refs': test_case.get('refs', ''),
                'custom_steps_separated': [
                    {'content': step, 'expected': ''} for step in test_case['steps']
                ]
            }
            
            response = self.session.post(
                f"{self.url}/api/v2/add_case/{section_id}",
                json=data
            )
            
            if response.status_code == 200:
                case = response.json()
                logger.info(f"Created test case {case['id']}: {test_case['title']}")
                return case['id']
            else:
                logger.error(f"Failed to create test case: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating test case: {str(e)}")
            return None
        
    def _send_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Send request to TestRail API.
        
        Args:
            method: HTTP method (GET or POST)
            endpoint: API endpoint
            data: Request data for POST requests
            
        Returns:
            Response JSON data or None if request failed
        """
        url = f"{self.url}/index.php?/api/v2/{endpoint}"
        try:
            if method == 'GET':
                response = self.session.get(url, timeout=(10, 30))
            elif method == 'POST':
                response = self.session.post(url, json=data, timeout=(10, 30))
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"TestRail API request failed: {str(e)}", exc_info=True)
            return None
            
    def validate_credentials(self) -> bool:
        """
        Test connection to TestRail.
        
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            response = self._send_request('GET', 'get_user_by_email&email=' + self.username)
            return response is not None
        except Exception as e:
            logger.error(f"Failed to validate TestRail credentials: {str(e)}", exc_info=True)
            return False
            
    def create_section(self, project_id: int, suite_id: int, name: str, parent_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new section in TestRail.
        
        Args:
            project_id: TestRail project ID
            suite_id: TestRail suite ID
            name: Section name
            parent_id: Parent section ID (optional)
            
        Returns:
            Created section data or None if creation failed
        """
        data = {
            'name': name,
            'suite_id': suite_id,
            'description': 'Test cases imported from Jira'
        }
        if parent_id:
            data['parent_id'] = parent_id
            
        return self._send_request('POST', f'add_section/{project_id}', data)
        
    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """
        Get project details.
        
        Args:
            project_id: TestRail project ID
            
        Returns:
            Project data or None if request failed
        """
        return self._send_request('GET', f'get_project/{project_id}')
        
    def get_suite(self, suite_id: int) -> Optional[Dict[str, Any]]:
        """
        Get test suite details.
        
        Args:
            suite_id: TestRail suite ID
            
        Returns:
            Suite data or None if request failed
        """
        return self._send_request('GET', f'get_suite/{suite_id}')
        
    def get_cases(self, project_id: int, suite_id: int, section_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get test cases.
        
        Args:
            project_id: TestRail project ID
            suite_id: TestRail suite ID
            section_id: TestRail section ID (optional)
            
        Returns:
            List of test cases or None if request failed
        """
        endpoint = f'get_cases/{project_id}&suite_id={suite_id}'
        if section_id:
            endpoint += f'&section_id={section_id}'
        return self._send_request('GET', endpoint) 