"""
Test case generator for MCP server with code analysis capabilities.
"""
import logging
import os
from typing import Dict, Any, List
import ast
import re

logger = logging.getLogger(__name__)

class TestCaseGenerator:
    def __init__(self):
        self.test_types = {
            'unit': 'Unit Test',
            'integration': 'Integration Test',
            'api': 'API Test',
            'ui': 'UI Test',
            'performance': 'Performance Test'
        }
        
    def analyze_ticket(self, issue_details: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a Jira ticket and extract key information."""
        try:
            analysis = {
                'key': issue_details['key'],
                'summary': {
                    'title': issue_details['fields']['summary'],
                    'type': issue_details['fields']['issuetype']['name']
                },
                'description': {
                    'raw': issue_details['fields']['description'],
                    'sections': self._parse_description(issue_details['fields']['description'])
                },
                'metadata': {
                    'components': [c['name'] for c in issue_details['fields'].get('components', [])],
                    'labels': issue_details['fields'].get('labels', []),
                    'status': issue_details['fields']['status']['name']
                }
            }
            
            # Extract code-related information
            analysis['code_context'] = self._extract_code_context(analysis['description']['raw'])
            analysis['test_suggestions'] = self._generate_test_suggestions(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing ticket: {str(e)}", exc_info=True)
            return None
            
    def _extract_code_context(self, description: str) -> Dict[str, Any]:
        """Extract code-related information from description."""
        code_context = {
            'functions': [],
            'classes': [],
            'database_tables': [],
            'apis': []
        }
        
        # Extract function names (e.g., functionName(), method_name())
        function_pattern = r'\b\w+\([^)]*\)'
        code_context['functions'] = list(set(re.findall(function_pattern, description)))
        
        # Extract class names (typically PascalCase)
        class_pattern = r'\b[A-Z][a-zA-Z0-9]+\b'
        code_context['classes'] = list(set(re.findall(class_pattern, description)))
        
        # Extract database tables (typically mentioned with 'table', 'tbl', or in SQL-like context)
        table_pattern = r'\b(tbl|table)\s*[A-Za-z0-9_]+\b'
        code_context['database_tables'] = list(set(re.findall(table_pattern, description, re.IGNORECASE)))
        
        # Extract API endpoints
        api_pattern = r'/api/[a-zA-Z0-9/_-]+'
        code_context['apis'] = list(set(re.findall(api_pattern, description)))
        
        return code_context
        
    def _parse_description(self, description: str) -> Dict[str, Any]:
        """Parse different sections from the description."""
        if not description:
            return {}
            
        sections = {
            'acceptance_criteria': [],
            'technical_details': [],
            'requirements': [],
            'notes': []
        }
        
        current_section = 'notes'
        for line in description.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            lower_line = line.lower()
            if 'acceptance criteria' in lower_line:
                current_section = 'acceptance_criteria'
                continue
            elif 'technical' in lower_line or 'implementation' in lower_line:
                current_section = 'technical_details'
                continue
            elif 'requirement' in lower_line:
                current_section = 'requirements'
                continue
                
            if line.startswith('- ') or line.startswith('* '):
                sections[current_section].append(line[2:])
            else:
                sections[current_section].append(line)
                
        return sections
        
    def _analyze_source_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a source code file."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            tree = ast.parse(content)
            analysis = {
                'classes': [],
                'functions': [],
                'imports': [],
                'file_path': file_path
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    analysis['classes'].append({
                        'name': node.name,
                        'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                    })
                elif isinstance(node, ast.FunctionDef):
                    analysis['functions'].append(node.name)
                elif isinstance(node, ast.Import):
                    analysis['imports'].extend(n.name for n in node.names)
                elif isinstance(node, ast.ImportFrom):
                    analysis['imports'].append(f"{node.module}.{node.names[0].name}")
                    
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {str(e)}", exc_info=True)
            return None
            
    def suggest_test_files(self, analysis: Dict[str, Any], source_files: List[str]) -> List[Dict[str, Any]]:
        """Suggest test file names and locations based on analysis."""
        suggestions = []
        
        for source_file in source_files:
            file_analysis = self._analyze_source_file(source_file)
            if not file_analysis:
                continue
                
            base_name = os.path.basename(source_file)
            dir_name = os.path.dirname(source_file)
            
            # Suggest test file name
            if base_name.endswith('.py'):
                test_file = f"test_{base_name}"
            else:
                test_file = f"test_{base_name}.py"
                
            suggestions.append({
                'source_file': source_file,
                'test_file': os.path.join(dir_name, test_file),
                'classes_to_test': file_analysis['classes'],
                'functions_to_test': file_analysis['functions']
            })
            
        return suggestions
        
    def generate_test_snippets(self, analysis: Dict[str, Any], source_files: List[str]) -> List[Dict[str, Any]]:
        """Generate test code snippets based on analysis."""
        snippets = []
        
        for source_file in source_files:
            file_analysis = self._analyze_source_file(source_file)
            if not file_analysis:
                continue
                
            # Generate test class
            class_name = f"Test{os.path.splitext(os.path.basename(source_file))[0].title()}"
            
            test_methods = []
            for func in file_analysis['functions']:
                test_methods.append(f"""
    def test_{func}(self):
        \"\"\"Test {func} functionality.\"\"\"
        # Setup
        # TODO: Set up test environment
        
        # Execute
        # TODO: Call {func}
        
        # Verify
        # TODO: Add assertions
        """)
                
            for cls in file_analysis['classes']:
                for method in cls['methods']:
                    test_methods.append(f"""
    def test_{cls['name']}_{method}(self):
        \"\"\"Test {cls['name']}.{method} functionality.\"\"\"
        # Setup
        # TODO: Create {cls['name']} instance
        
        # Execute
        # TODO: Call {method}
        
        # Verify
        # TODO: Add assertions
        """)
                    
            snippet = f"""import unittest
from {os.path.splitext(os.path.basename(source_file))[0]} import *

class {class_name}(unittest.TestCase):
    def setUp(self):
        \"\"\"Set up test fixtures.\"\"\"
        pass
        
    def tearDown(self):
        \"\"\"Tear down test fixtures.\"\"\"
        pass
        
{''.join(test_methods)}

if __name__ == '__main__':
    unittest.main()
"""
            
            snippets.append({
                'source_file': source_file,
                'test_class': class_name,
                'code': snippet
            })
            
        return snippets
        
    def _generate_test_suggestions(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate test case suggestions based on ticket analysis."""
        suggestions = []
        
        # Add test cases based on acceptance criteria
        for criteria in analysis['description']['sections'].get('acceptance_criteria', []):
            suggestions.append({
                'title': f"Verify {criteria}",
                'type': 'Functional Test',
                'priority': 'High',
                'based_on': 'Acceptance Criteria'
            })
            
        # Add test cases based on technical details
        for detail in analysis['description']['sections'].get('technical_details', []):
            suggestions.append({
                'title': f"Technical Validation: {detail}",
                'type': 'Technical Test',
                'priority': 'Medium',
                'based_on': 'Technical Details'
            })
            
        # Add test cases based on code context
        for func in analysis['code_context']['functions']:
            suggestions.append({
                'title': f"Unit Test: {func}",
                'type': 'Unit Test',
                'priority': 'High',
                'based_on': 'Code Analysis'
            })
            
        for cls in analysis['code_context']['classes']:
            suggestions.append({
                'title': f"Class Test: {cls}",
                'type': 'Unit Test',
                'priority': 'High',
                'based_on': 'Code Analysis'
            })
            
        return suggestions
        
    def generate_test_cases(self, issue_details: Dict[str, Any], source_files: List[str] = None) -> List[Dict[str, Any]]:
        """Generate test cases based on issue information and source code."""
        analysis = self.analyze_ticket(issue_details)
        if not analysis:
            return []
            
        test_cases = []
        
        # Extract notification types from description
        notification_types = {
            'statement_generation': {
                'trigger': 'When a new statement is generated',
                'content': [
                    'Statement generation date',
                    'Statement due date',
                    'Penalty/late fee applicable'
                ],
                'channels': ['Email', 'SMS (optional)']
            },
            'collection_attempt': {
                'trigger': 'After each collection attempt (success or failure)',
                'content': {
                    'success': [
                        'Message confirming successful payment',
                        'Updated account balance'
                    ],
                    'failure': [
                        'Reason for failure',
                        'Decline fee applied',
                        'Total remaining dues'
                    ]
                },
                'macros': [
                    'Guest Name',
                    'Guest ID',
                    'Payment date',
                    'Payment Amount',
                    'Statement duration',
                    'Invoice number',
                    'Decline reason',
                    'Payment method used',
                    'Decline fee'
                ],
                'channels': ['Email', 'SMS (optional)']
            },
            'statement_movement': {
                'trigger': 'When overdue statements are rolled into the current statement',
                'content': [
                    'Total number of statements moved',
                    'Late fee/penalty applied',
                    'Updated total dues'
                ],
                'channels': ['Email', 'SMS (optional)']
            }
        }
        
        # Generate test cases for each notification type
        for notif_type, details in notification_types.items():
            # Basic notification delivery test
            test_cases.append({
                'title': f"Verify {notif_type.replace('_', ' ').title()} Notification Delivery",
                'type': 'Functional',
                'priority': 'High',
                'preconditions': [
                    'Test environment is set up',
                    'Test user has valid email and phone number',
                    'House Account feature is enabled'
                ],
                'steps': [
                    f"Trigger the notification by: {details['trigger']}",
                    'Wait for notification processing',
                    'Check email delivery',
                    'Check SMS delivery (if enabled)'
                ],
                'expected': [
                    'Notification is delivered via configured channels',
                    'Delivery timing meets performance requirements',
                    'No errors in notification logs'
                ]
            })
            
            # Content verification test
            content_items = (details['content'] if isinstance(details['content'], list) 
                           else details['content'].get('success', []) + details['content'].get('failure', []))
            test_cases.append({
                'title': f"Verify {notif_type.replace('_', ' ').title()} Notification Content",
                'type': 'Functional',
                'priority': 'High',
                'preconditions': [
                    'Test environment is set up',
                    'Test data is prepared'
                ],
                'steps': [
                    f"Trigger the notification by: {details['trigger']}",
                    'Capture the notification content',
                    'Verify all required content elements'
                ],
                'expected': [f"Content includes: {item}" for item in content_items]
            })
            
            # If it's collection attempt notification, add success/failure scenarios
            if notif_type == 'collection_attempt':
                # Success scenario
                test_cases.append({
                    'title': 'Verify Successful Collection Attempt Notification',
                    'type': 'Functional',
                    'priority': 'High',
                    'preconditions': [
                        'Test environment is set up',
                        'Valid payment method is configured',
                        'Sufficient balance for payment'
                    ],
                    'steps': [
                        'Initiate a collection attempt',
                        'Ensure payment succeeds',
                        'Capture the notification'
                    ],
                    'expected': [f"Content includes: {item}" for item in details['content']['success']]
                })
                
                # Failure scenario
                test_cases.append({
                    'title': 'Verify Failed Collection Attempt Notification',
                    'type': 'Functional',
                    'priority': 'High',
                    'preconditions': [
                        'Test environment is set up',
                        'Invalid/expired payment method is configured'
                    ],
                    'steps': [
                        'Initiate a collection attempt',
                        'Ensure payment fails',
                        'Capture the notification'
                    ],
                    'expected': [f"Content includes: {item}" for item in details['content']['failure']]
                })
                
                # Macro validation
                test_cases.append({
                    'title': 'Verify Collection Attempt Notification Macros',
                    'type': 'Functional',
                    'priority': 'High',
                    'preconditions': ['Test environment is set up'],
                    'steps': [
                        'Set up test data with known values',
                        'Trigger collection attempt notification',
                        'Capture the notification'
                    ],
                    'expected': [f"Macro {macro} is correctly populated" for macro in details['macros']]
                })
            
        # Add edge cases and validation tests
        test_cases.extend([
            {
                'title': 'Verify Notification Retry Mechanism',
                'type': 'Integration',
                'priority': 'Medium',
                'preconditions': ['Test environment is set up'],
                'steps': [
                    'Configure email/SMS service to fail temporarily',
                    'Trigger a notification',
                    'Verify retry attempts',
                    'Restore email/SMS service',
                    'Monitor notification delivery'
                ],
                'expected': [
                    'System attempts to retry failed notifications',
                    'Notification is delivered after service is restored',
                    'Retry attempts are logged correctly'
                ]
            },
            {
                'title': 'Verify Notification Templates Customization',
                'type': 'Functional',
                'priority': 'Medium',
                'preconditions': ['Test environment is set up'],
                'steps': [
                    'Modify notification templates',
                    'Trigger notifications',
                    'Verify template changes'
                ],
                'expected': [
                    'Modified templates are used for notifications',
                    'Template changes are applied correctly',
                    'No formatting issues in modified templates'
                ]
            },
            {
                'title': 'Verify Notification Preferences',
                'type': 'Functional',
                'priority': 'High',
                'preconditions': ['Test environment is set up'],
                'steps': [
                    'Configure different notification preferences',
                    'Trigger notifications',
                    'Verify delivery based on preferences'
                ],
                'expected': [
                    'Notifications respect user preferences',
                    'Email-only users do not receive SMS',
                    'SMS-only users do not receive email',
                    'Users can opt-out of optional notifications'
                ]
            }
        ])
        
        # Add performance test cases
        test_cases.extend([
            {
                'title': 'Verify Notification System Performance',
                'type': 'Performance',
                'priority': 'High',
                'preconditions': ['Test environment is set up with monitoring'],
                'steps': [
                    'Generate high volume of notifications',
                    'Monitor system performance',
                    'Check notification delivery times'
                ],
                'expected': [
                    'System handles high notification volume',
                    'Notification delivery meets SLA requirements',
                    'No degradation in notification processing'
                ]
            },
            {
                'title': 'Verify Notification System Under Load',
                'type': 'Performance',
                'priority': 'Medium',
                'preconditions': ['Load testing environment is set up'],
                'steps': [
                    'Simulate multiple concurrent notification triggers',
                    'Monitor system resources',
                    'Check notification queue processing'
                ],
                'expected': [
                    'System maintains performance under load',
                    'No notification drops or delays',
                    'Resource utilization remains within limits'
                ]
            }
        ])
        
        return test_cases

    def analyze_source_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """Analyze source files and extract test-relevant information."""
        analysis = {
            'files': {},
            'test_suggestions': []
        }
        
        for file_path in file_paths:
            try:
                if not os.path.exists(file_path):
                    logger.warning(f"File not found: {file_path}")
                    continue
                    
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                file_analysis = self._analyze_source_file(file_path)
                if file_analysis:
                    analysis['files'][file_path] = file_analysis
                    
                    # Generate test suggestions based on analysis
                    suggestions = self._generate_test_suggestions_from_code(file_analysis)
                    analysis['test_suggestions'].extend(suggestions)
                    
            except Exception as e:
                logger.error(f"Error analyzing file {file_path}: {str(e)}")
                analysis['files'][file_path] = {'error': str(e)}
                
        return analysis
        
    def _analyze_source_file(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze a source file using AST and extract relevant information."""
        try:
            tree = ast.parse(content)
            
            analysis = {
                'classes': [],
                'functions': [],
                'imports': [],
                'api_endpoints': [],
                'db_operations': [],
                'file_type': self._determine_file_type(file_path)
            }
            
            for node in ast.walk(tree):
                # Extract classes
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        'name': node.name,
                        'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                        'decorators': [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
                    }
                    analysis['classes'].append(class_info)
                    
                # Extract functions
                elif isinstance(node, ast.FunctionDef):
                    func_info = {
                        'name': node.name,
                        'args': [arg.arg for arg in node.args.args],
                        'decorators': [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
                    }
                    analysis['functions'].append(func_info)
                    
                # Extract imports
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            analysis['imports'].append(name.name)
                    else:
                        module = node.module or ''
                        for name in node.names:
                            analysis['imports'].append(f"{module}.{name.name}")
                            
            # Extract API endpoints using regex
            api_patterns = [
                r'@(?:app|router|blueprint)\.(?:route|get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]',
                r'@api\.(?:route|get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]'
            ]
            
            for pattern in api_patterns:
                endpoints = re.findall(pattern, content)
                analysis['api_endpoints'].extend(endpoints)
                
            # Extract database operations
            db_patterns = [
                r'(?:db|session)\.(?:query|add|delete|commit|execute)',
                r'Model\.(?:query|create|update|delete)',
                r'(?:insert|update|delete|select).*?(?:from|into)\s+(\w+)',
            ]
            
            for pattern in db_patterns:
                db_ops = re.findall(pattern, content)
                if db_ops:
                    analysis['db_operations'].extend(db_ops)
                    
            return analysis
            
        except SyntaxError:
            logger.warning(f"Could not parse {file_path} as Python file")
            return None
            
    def _determine_file_type(self, file_path: str) -> str:
        """Determine the type of file based on its path and name."""
        file_name = os.path.basename(file_path).lower()
        
        if 'test' in file_name:
            return 'test'
        elif any(name in file_name for name in ['api', 'endpoint', 'route']):
            return 'api'
        elif any(name in file_name for name in ['model', 'schema', 'entity']):
            return 'model'
        elif any(name in file_name for name in ['view', 'component', 'page']):
            return 'view'
        else:
            return 'unknown'
            
    def _generate_test_suggestions_from_code(self, file_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate test suggestions based on code analysis."""
        suggestions = []
        
        # Suggest unit tests for classes and methods
        for class_info in file_analysis['classes']:
            suggestions.append({
                'type': 'unit',
                'title': f"Unit Tests for {class_info['name']} class",
                'description': f"Create unit tests for the {class_info['name']} class methods: {', '.join(class_info['methods'])}",
                'priority': 'high' if any('api' in d.lower() for d in class_info['decorators']) else 'medium'
            })
            
        # Suggest API tests for endpoints
        for endpoint in file_analysis['api_endpoints']:
            suggestions.append({
                'type': 'api',
                'title': f"API Test for endpoint {endpoint}",
                'description': f"Create API tests to verify the functionality of the {endpoint} endpoint",
                'priority': 'high'
            })
            
        # Suggest integration tests for database operations
        if file_analysis['db_operations']:
            suggestions.append({
                'type': 'integration',
                'title': "Database Integration Tests",
                'description': f"Create integration tests for database operations: {', '.join(file_analysis['db_operations'])}",
                'priority': 'high'
            })
            
        return suggestions 