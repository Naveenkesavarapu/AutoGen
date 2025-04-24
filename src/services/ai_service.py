import os
import requests
from typing import List, Dict
import json

class AIService:
    def __init__(self):
        """Initialize Zeenie LLM client"""
        self.api_endpoint = os.getenv('LLM_API_ENDPOINT', 'https://zeenie-llm-api.zenotibeta.com/GenericLLM')
        self.api_key = os.getenv('LLM_API_KEY')
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'x-apikey {self.api_key}',
            'x-api-key': self.api_key
        }
    
    def generate_test_cases(self, ticket_data: Dict, code_analysis: Dict) -> List[Dict]:
        """Generate test cases using Zeenie LLM API"""
        prompt = self._create_prompt(ticket_data, code_analysis)
        
        try:
            # Call Zeenie LLM API
            response = requests.post(
                self.api_endpoint,
                headers=self.headers,
                json={
                    'prompt': prompt
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"API returned status code {response.status_code}")
            
            # Parse the response into test cases
            response_data = response.json()
            # Get the generated text from the response
            generated_text = response_data.get('response', response_data.get('generated_text', ''))
            
            test_cases = self._parse_response(generated_text)
            return test_cases
            
        except Exception as e:
            print(f"Error generating test cases: {str(e)}")
            return []
    
    def _create_prompt(self, ticket_data: Dict, code_analysis: Dict) -> str:
        """Create prompt for test case generation"""
        prompt = f"""As a QA expert, generate comprehensive test cases for the following feature:

Title: {ticket_data['title']}
Description: {ticket_data['description']}

Acceptance Criteria:
{ticket_data['acceptance_criteria']}

Code Changes:
- Changed Files: {', '.join([f['path'] for f in code_analysis['changed_files']])}
- Affected Components: {', '.join([c['name'] for c in code_analysis['affected_components']])}

Generate test cases covering:
1. Positive scenarios
2. Negative scenarios
3. Edge cases
4. Integration points
5. Performance considerations
6. Security aspects (if applicable)

Format your response as a JSON array of test cases with this structure:
{{
    "title": "string",
    "type": "string",
    "priority": "string",
    "steps": [
        {{
            "description": "string",
            "expected_result": "string"
        }}
    ]
}}

Each test case should include:
- Title: Clear and descriptive
- Type: One of [Functional, Integration, Performance, Security]
- Priority: One of [Critical, High, Medium, Low]
- Steps: Array of test steps with description and expected result
"""
        return prompt
    
    def _parse_response(self, response_text: str) -> List[Dict]:
        """Parse API response into test cases"""
        try:
            # Try to find JSON content in the response
            # This handles cases where the LLM might include explanatory text
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                test_cases = json.loads(json_str)
            else:
                # If no JSON array found, try parsing the entire response
                test_cases = json.loads(response_text)
            
            # Validate test case format
            if not isinstance(test_cases, list):
                test_cases = [test_cases]
            
            # Ensure each test case has required fields
            for test_case in test_cases:
                if 'title' not in test_case:
                    test_case['title'] = 'Untitled Test Case'
                if 'type' not in test_case:
                    test_case['type'] = 'Functional'
                if 'priority' not in test_case:
                    test_case['priority'] = 'Medium'
                if 'steps' not in test_case:
                    test_case['steps'] = []
            
            return test_cases
            
        except Exception as e:
            print(f"Error parsing LLM response: {str(e)}")
            return [] 