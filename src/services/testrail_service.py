from testrail_api import TestRailAPI
import os
from typing import List, Dict
from dotenv import load_dotenv

class TestRailService:
    def __init__(self):
        """Initialize TestRail API client"""
        load_dotenv()  # Load environment variables from .env file
        
        # Get credentials from environment variables
        base_url = os.getenv('TESTRAIL_URL')
        email = os.getenv('TESTRAIL_EMAIL')
        api_key = os.getenv('TESTRAIL_API_KEY')
        
        if not all([base_url, email, api_key]):
            raise ValueError("TestRail credentials not found in environment variables. Please run the setup wizard.")
        
        self.client = TestRailAPI(
            base_url=base_url,
            email=email,
            password=api_key
        )
        
        # Get project and suite IDs from environment variables or use defaults
        self.project_id = int(os.getenv('TESTRAIL_PROJECT_ID', '6165'))
        self.suite_id = int(os.getenv('TESTRAIL_SUITE_ID', '8208'))
    
    def create_test_cases(self, project_id: int, suite_id: int, section_id: int, 
                         test_cases: List[Dict], jira_ticket: str) -> List[Dict]:
        """Create test cases in TestRail"""
        created_cases = []
        
        for test_case in test_cases:
            case_data = {
                'title': test_case['title'],
                'type_id': self._get_case_type_id(test_case.get('type', 'Functional')),
                'priority_id': self._get_priority_id(test_case.get('priority', 'Medium')),
                'estimate': test_case.get('estimate', '15m'),
                'refs': jira_ticket,
                'custom_steps_separated': [
                    {
                        'content': step['description'],
                        'expected': step['expected_result']
                    }
                    for step in test_case.get('steps', [])
                ]
            }
            
            try:
                created_case = self.client.cases.add_case(
                    section_id=section_id,
                    case=case_data
                )
                created_cases.append(created_case)
            except Exception as e:
                print(f"Error creating test case {test_case['title']}: {str(e)}")
        
        return created_cases
    
    def create_test_run(self, project_id: int, suite_id: int, name: str, 
                       case_ids: List[int], jira_ticket: str) -> Dict:
        """Create a test run for the created test cases"""
        run_data = {
            'suite_id': suite_id,
            'name': f"Test Run for {jira_ticket} - {name}",
            'include_all': False,
            'case_ids': case_ids,
            'refs': jira_ticket
        }
        
        try:
            return self.client.runs.add_run(
                project_id=project_id,
                run=run_data
            )
        except Exception as e:
            print(f"Error creating test run: {str(e)}")
            return None
    
    def _get_case_type_id(self, case_type: str) -> int:
        """Map case type to TestRail type ID"""
        type_map = {
            'Functional': 1,
            'Acceptance': 2,
            'Accessibility': 3,
            'Automated': 4,
            'Performance': 5,
            'Regression': 6,
            'Security': 7,
            'Smoke': 8,
            'Usability': 9
        }
        return type_map.get(case_type, 1)
    
    def _get_priority_id(self, priority: str) -> int:
        """Map priority to TestRail priority ID"""
        priority_map = {
            'Critical': 1,
            'High': 2,
            'Medium': 3,
            'Low': 4
        }
        return priority_map.get(priority, 3) 