"""
Flask server for Jira to TestRail integration with code analysis capabilities.
"""
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import logging
import os
import json
import tempfile
import subprocess
import sys
from pathlib import Path

# Add the parent directory (src) to Python path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from .jira_client import JiraClient
from .testrail_client import TestRailClient
from .test_generator import TestCaseGenerator
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from {env_path}")
else:
    logger.warning(f"No env file found at {env_path}. Using default values.")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize clients with default values for development
try:
    jira_client = JiraClient(
        url=os.getenv('JIRA_URL'),
        username=os.getenv('JIRA_USERNAME'),
        token=os.getenv('JIRA_TOKEN')
    )
    logger.info(f"Initialized Jira client with URL: {os.getenv('JIRA_URL')} and username: {os.getenv('JIRA_USERNAME')}")
except Exception as e:
    logger.error(f"Failed to initialize Jira client: {str(e)}")
    jira_client = None

try:
    testrail_client = TestRailClient(
        url=os.getenv('TESTRAIL_URL'),
        username=os.getenv('TESTRAIL_EMAIL'),
        password=os.getenv('TESTRAIL_TOKEN')
    )
    logger.info(f"Initialized TestRail client with URL: {os.getenv('TESTRAIL_URL')} and email: {os.getenv('TESTRAIL_EMAIL')}")
except Exception as e:
    logger.error(f"Failed to initialize TestRail client: {str(e)}")
    testrail_client = None

try:
    test_generator = TestCaseGenerator()
    logger.info("Initialized Test Generator")
except Exception as e:
    logger.error(f"Failed to initialize Test Generator: {str(e)}")
    test_generator = None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    status = {
        'status': 'healthy',
        'environment': os.getenv('FLASK_ENV', 'development'),
        'services': {
            'jira': {
                'connected': jira_client is not None and jira_client.is_connected(),
                'error': jira_client.get_connection_error() if jira_client else "Client not initialized"
            },
            'testrail': {
                'connected': testrail_client is not None,
                'error': None
            },
            'test_generator': {
                'connected': test_generator is not None,
                'error': None
            }
        }
    }
    return jsonify(status), 200

@app.route('/api/process', methods=['POST'])
def process_request():
    """Main processing endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Process the request (implement your logic here)
        result = {"status": "success", "message": "Request processed successfully"}
        
        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/jira/ticket/<ticket_id>')
def get_ticket_details(ticket_id):
    """Get Jira ticket details with analysis."""
    try:
        if not jira_client:
            return jsonify({
                'error': 'Jira client not initialized',
                'details': 'Check environment variables: JIRA_URL, JIRA_USERNAME, JIRA_TOKEN'
            }), 503
            
        if not jira_client.is_connected():
            return jsonify({
                'error': 'Jira client not connected',
                'details': jira_client.get_connection_error()
            }), 503
            
        issue_details = jira_client.get_issue(ticket_id)
        if not issue_details:
            return jsonify({
                'error': 'Failed to fetch issue details',
                'details': f"Issue {ticket_id} not found or access denied"
            }), 404
            
        # Extract PR information
        pr_info = issue_details.get('pull_requests', [])
        if not pr_info:
            return jsonify({
                'ticket': issue_details,
                'warning': 'No pull requests found in ticket'
            })
            
        # Create a temporary directory for code analysis
        with tempfile.TemporaryDirectory() as temp_dir:
            # For each PR, try to clone and analyze the code
            code_analysis = []
            for pr in pr_info:
                pr_url = pr['url']
                pr_number = pr['number']
                
                try:
                    # Extract repository URL from PR URL
                    repo_url = pr_url.split('/pull/')[0] if '/pull/' in pr_url else None
                    if not repo_url:
                        logger.warning(f"Could not extract repository URL from PR: {pr_url}")
                        continue
                        
                    # Clone the repository
                    repo_path = os.path.join(temp_dir, f"repo_{pr_number}")
                    clone_cmd = ['git', 'clone', repo_url, repo_path]
                    subprocess.run(clone_cmd, check=True, capture_output=True)
                    
                    # Fetch PR branch
                    fetch_cmd = ['git', 'fetch', 'origin', f"pull/{pr_number}/head:pr_{pr_number}"]
                    subprocess.run(fetch_cmd, cwd=repo_path, check=True, capture_output=True)
                    
                    # Checkout PR branch
                    checkout_cmd = ['git', 'checkout', f"pr_{pr_number}"]
                    subprocess.run(checkout_cmd, cwd=repo_path, check=True, capture_output=True)
                    
                    # Get list of changed files
                    diff_cmd = ['git', 'diff', '--name-only', 'HEAD^']
                    diff_result = subprocess.run(diff_cmd, cwd=repo_path, check=True, capture_output=True, text=True)
                    changed_files = diff_result.stdout.splitlines()
                    
                    # Analyze each changed file
                    if test_generator:
                        analysis = test_generator.analyze_source_files(
                            [os.path.join(repo_path, file) for file in changed_files]
                        )
                        
                        code_analysis.append({
                            'pr_number': pr_number,
                            'pr_url': pr_url,
                            'changed_files': changed_files,
                            'analysis': analysis
                        })
                    else:
                        logger.warning("Test generator not initialized, skipping code analysis")
                        
                except Exception as e:
                    logger.error(f"Error analyzing PR {pr_number}: {str(e)}")
                    code_analysis.append({
                        'pr_number': pr_number,
                        'pr_url': pr_url,
                        'error': str(e)
                    })
                    
            return jsonify({
                'ticket': issue_details,
                'code_analysis': code_analysis
            })
            
    except Exception as e:
        logger.error(f"Error processing ticket {ticket_id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/cursor/generate_tests', methods=['POST'])
def generate_tests_with_code():
    """Generate test cases with code context."""
    try:
        if not all([jira_client, testrail_client, test_generator]):
            return jsonify({'error': 'One or more required services not initialized'}), 503
            
        data = request.get_json()
        if not data or 'ticket_id' not in data:
            return jsonify({'error': 'Missing ticket_id in request'}), 400
            
        ticket_id = data['ticket_id']
        source_files = data.get('source_files', [])
        
        # Get issue details
        issue_details = jira_client.get_issue(ticket_id)
        if not issue_details:
            return jsonify({'error': 'Failed to fetch issue details'}), 404
            
        # Generate test cases with code context
        test_cases = test_generator.generate_test_cases(issue_details, source_files)
        
        # Get test file suggestions if source files provided
        test_file_suggestions = []
        test_snippets = []
        if source_files:
            analysis = test_generator.analyze_ticket(issue_details)
            test_file_suggestions = test_generator.suggest_test_files(analysis, source_files)
            test_snippets = test_generator.generate_test_snippets(analysis, source_files)
            
        response = {
            'ticket': issue_details,
            'test_cases': test_cases,
            'test_files': test_file_suggestions,
            'test_snippets': test_snippets
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error generating tests: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/webhook/jira', methods=['POST'])
def handle_jira_webhook():
    """Handle Jira webhook events."""
    try:
        if not all([jira_client, testrail_client, test_generator]):
            return jsonify({'error': 'One or more required services not initialized'}), 503
            
        event = request.get_json()
        if not event:
            return jsonify({'error': 'No event data received'}), 400
            
        # Validate webhook payload
        if 'issue' not in event:
            return jsonify({'error': 'Invalid webhook payload'}), 400
            
        issue = event['issue']
        issue_key = issue['key']
        
        # Check if this is a status change event
        changelog = event.get('changelog', {})
        status_change = None
        for item in changelog.get('items', []):
            if item.get('field') == 'status':
                status_change = item
                break
                
        if not status_change:
            return jsonify({'message': 'Not a status change event'}), 200
            
        # Check if the new status is QA
        if status_change['toString'].lower() != 'qa':
            return jsonify({'message': 'Status not changed to QA'}), 200
            
        # Get full issue details
        issue_details = jira_client.get_issue(issue_key)
        if not issue_details:
            return jsonify({'error': 'Failed to fetch issue details'}), 404
            
        # Generate test cases
        test_cases = test_generator.generate_test_cases(issue_details)
        if not test_cases:
            logger.warning(f"No test cases generated for {issue_key}")
            return jsonify({'message': 'No test cases generated'}), 200
            
        # Format test cases as a structured comment
        comment = "h2. Test Cases Generated\n\n"
        
        # Group test cases by type
        test_cases_by_type = {}
        for test_case in test_cases:
            test_type = test_case.get('type', 'Other')
            if test_type not in test_cases_by_type:
                test_cases_by_type[test_type] = []
            test_cases_by_type[test_type].append(test_case)
        
        # Add each group of test cases to the comment
        for test_type, cases in test_cases_by_type.items():
            comment += f"h3. {test_type} Tests\n\n"
            for idx, test_case in enumerate(cases, 1):
                comment += f"h4. {idx}. {test_case['title']}\n"
                comment += f"*Priority:* {test_case['priority']}\n\n"
                
                if test_case.get('preconditions'):
                    comment += "*Preconditions:*\n"
                    for precond in test_case['preconditions']:
                        comment += f"* {precond}\n"
                    comment += "\n"
                
                comment += "*Steps:*\n"
                for step_idx, step in enumerate(test_case['steps'], 1):
                    comment += f"# {step}\n"
                comment += "\n"
                
                comment += "*Expected Results:*\n"
                if isinstance(test_case['expected'], list):
                    for result in test_case['expected']:
                        comment += f"* {result}\n"
                else:
                    comment += f"* {test_case['expected']}\n"
                comment += "\n----\n\n"
        
        # Add a summary section
        comment += f"h3. Summary\n"
        comment += f"* Total Test Cases: {len(test_cases)}\n"
        for test_type, cases in test_cases_by_type.items():
            comment += f"* {test_type} Tests: {len(cases)}\n"
        
        # Add the comment to Jira
        success = jira_client.add_comment(issue_key, comment)
        if not success:
            return jsonify({'error': 'Failed to add comment to Jira'}), 500
        
        # Create test cases in TestRail if configured
        created_cases = []
        if testrail_client:
            for test_case in test_cases:
                case_id = testrail_client.create_test_case(test_case)
                if case_id:
                    created_cases.append({
                        'id': case_id,
                        'title': test_case['title']
                    })
                    
            if created_cases:
                # Add TestRail links in a separate comment
                testrail_comment = "h2. TestRail Test Cases\n\n"
                for case in created_cases:
                    testrail_comment += f"* [{case['title']}]({os.getenv('TESTRAIL_URL')}/index.php?/cases/view/{case['id']})\n"
                jira_client.add_comment(issue_key, testrail_comment)
        
        return jsonify({
            'status': 'success',
            'message': f"Added {len(test_cases)} test cases to ticket",
            'test_cases': len(test_cases),
            'testrail_cases': len(created_cases)
        })
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

def start_server(host='0.0.0.0', port=5000):
    """Start the Flask server."""
    app.run(host=host, port=port, debug=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 