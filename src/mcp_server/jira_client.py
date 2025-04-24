"""
Jira API client for MCP server.
"""
from jira import JIRA, JIRAError
from typing import Dict, Any, Optional, List
import logging
import os
import re

logger = logging.getLogger(__name__)

class JiraClient:
    def __init__(self, url=None, username=None, token=None):
        """
        Initialize Jira client.
        
        Args:
            url: Jira instance URL
            username: Jira username/email
            token: Jira API token
        """
        self.url = url.rstrip('/') if url else None
        self.username = username
        self.token = token
        self.jira = None
        self.connection_error = None
        
        if not all([url, username, token]):
            missing = []
            if not url: missing.append('JIRA_URL')
            if not username: missing.append('JIRA_USERNAME')
            if not token: missing.append('JIRA_TOKEN')
            self.connection_error = f"Missing required environment variables: {', '.join(missing)}"
            logger.warning(self.connection_error)
            return
            
        try:
            logger.info(f"Initializing Jira client for {self.url} with username {self.username}")
            self.jira = JIRA(
                server=self.url,
                basic_auth=(self.username, self.token),
                validate=True
            )
            # Test connection
            self.jira.myself()
            logger.info("Successfully connected to Jira")
            self.connection_error = None
        except JIRAError as e:
            self.jira = None
            self.connection_error = f"Jira authentication failed: {str(e)}"
            logger.error(self.connection_error)
        except Exception as e:
            self.jira = None
            self.connection_error = f"Failed to initialize Jira client: {str(e)}"
            logger.error(self.connection_error)
            
    def extract_pr_info(self, description: str) -> List[Dict[str, str]]:
        """Extract PR information from text."""
        pr_info = []
        if not description:
            return pr_info
            
        # Pattern to match PR links in various formats
        patterns = [
            # GitHub PR format
            r'https://github\.com/[^/]+/[^/]+/pull/(\d+)',
            # BitBucket PR format
            r'https://bitbucket\.org/[^/]+/[^/]+/pull-requests/(\d+)',
            # Azure DevOps PR format
            r'https://dev\.azure\.com/[^/]+/[^/]+/_git/[^/]+/pullrequest/(\d+)',
            # Generic PR mention
            r'PR[:\s#]+(\d+)',
            # Pull Request mention
            r'[Pp]ull [Rr]equest[:\s#]+(\d+)',
            # Azure DevOps short format
            r'pull/(\d+)',
            # Development panel format
            r'PR-(\d+)',
            # VSTS format
            r'_git/[^/]+/pullrequest/(\d+)',
            # Generic URL with PR number
            r'/pull-requests?/(\d+)',
            # Jira development panel format
            r'pullrequest=(\d+)',
            # Additional GitHub formats
            r'github\.com/[^/]+/[^/]+/compare/[^/]+',
            r'github\.com/[^/]+/[^/]+/commits/[^/]+'
        ]
        
        logger.debug(f"Searching for PR patterns in text: {description[:100]}...")
        
        for pattern in patterns:
            matches = re.finditer(pattern, description)
            for match in matches:
                pr_number = match.group(1) if len(match.groups()) > 0 else None
                pr_url = match.group(0)
                
                # Clean up and normalize URL
                if pr_url and not pr_url.startswith('http'):
                    # Try to construct full URL based on known patterns
                    if 'github.com' in self.url:
                        pr_url = f"{self.url}/pull/{pr_number}"
                    elif 'bitbucket.org' in self.url:
                        pr_url = f"{self.url}/pull-requests/{pr_number}"
                    elif 'dev.azure.com' in self.url:
                        pr_url = f"{self.url}/pullrequest/{pr_number}"
                        
                if pr_number or (pr_url and pr_url.startswith('http')):
                    pr_entry = {
                        'number': pr_number or 'unknown',
                        'url': pr_url
                    }
                    logger.debug(f"Found PR: {pr_entry}")
                    pr_info.append(pr_entry)
        
        if pr_info:
            logger.info(f"Found {len(pr_info)} PRs in text")
        
        return pr_info

    def is_connected(self) -> bool:
        """Check if client is properly connected."""
        return self.jira is not None
        
    def get_connection_error(self) -> Optional[str]:
        """Get the connection error message if any."""
        return self.connection_error
        
    def get_development_info(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """
        Get development information using the dev-status API endpoint.
        
        Args:
            issue_id: Jira issue ID
            
        Returns:
            Dictionary containing development information or None if not found
        """
        if not self.is_connected():
            return None
            
        try:
            dev_info = self.jira._get_json(f'rest/dev-status/latest/issue/detail?issueId={issue_id}')
            logger.info(f"Retrieved development info for issue {issue_id}")
            return dev_info
        except Exception as e:
            logger.warning(f"Error fetching development info: {str(e)}")
            return None

    def get_development_field(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """
        Get development information using the development field API endpoint.
        
        Args:
            issue_key: Jira issue key (e.g., 'PROJ-123')
            
        Returns:
            Dictionary containing development information or None if not found
        """
        if not self.is_connected():
            return None
            
        try:
            dev_field = self.jira._get_json(f'rest/api/3/issue/{issue_key}?fields=development')
            logger.info(f"Retrieved development field for issue {issue_key}")
            return dev_field.get('fields', {}).get('development')
        except Exception as e:
            logger.warning(f"Error fetching development field: {str(e)}")
            return None

    def get_issue(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """
        Get issue details from Jira.
        
        Args:
            issue_key: Jira issue key (e.g., 'PROJ-123')
            
        Returns:
            Dictionary containing issue details or None if not found
        """
        if not self.is_connected():
            error = self.get_connection_error() or "Jira client not connected"
            logger.warning(error)
            return None
            
        try:
            logger.info(f"Fetching issue {issue_key}")
            
            # Get all fields to inspect available development fields
            all_fields = self.jira.fields()
            dev_field_ids = [
                field['id'] for field in all_fields 
                if any(dev_term in field['name'].lower() 
                      for dev_term in ['development', 'github', 'pull request', 'pr'])
            ]
            logger.info(f"Found development field IDs: {dev_field_ids}")
            
            # Fetch issue with all potential development fields
            issue = self.jira.issue(
                issue_key,
                expand='changelog,development,devSummary,names,schema',
                fields=','.join(['*all'] + dev_field_ids)
            )
            
            # Get basic issue details
            issue_data = {
                'key': issue.key,
                'fields': {
                    'summary': issue.fields.summary,
                    'description': issue.fields.description,
                    'issuetype': {
                        'name': issue.fields.issuetype.name
                    },
                    'components': [
                        {'name': c.name} for c in issue.fields.components
                    ] if hasattr(issue.fields, 'components') else [],
                    'labels': issue.fields.labels if hasattr(issue.fields, 'labels') else [],
                    'status': {
                        'name': issue.fields.status.name
                    }
                }
            }
            
            pr_info = []
            
            # 1. Get development info using new REST API endpoints
            dev_info = self.get_development_info(issue.id)
            if dev_info:
                # Extract PR information from dev-status API
                if 'detail' in dev_info:
                    for repository in dev_info['detail']:
                        if 'pullRequests' in repository:
                            for pr in repository['pullRequests']:
                                pr_info.append({
                                    'number': pr.get('id'),
                                    'url': pr.get('url'),
                                    'status': pr.get('status'),
                                    'title': pr.get('name'),
                                    'repository': repository.get('name'),
                                    'branch': pr.get('source', {}).get('branch'),
                                    'type': 'dev_status_api'
                                })

            # 2. Get development field info
            dev_field = self.get_development_field(issue_key)
            if dev_field:
                # Extract PR information from development field
                if 'pullRequests' in dev_field:
                    for pr in dev_field['pullRequests']:
                        pr_info.append({
                            'number': pr.get('id'),
                            'url': pr.get('url'),
                            'status': pr.get('status'),
                            'title': pr.get('name'),
                            'type': 'development_field'
                        })

            # 3. Check development fields from standard API
            for field_id in dev_field_ids:
                try:
                    field_value = getattr(issue.fields, field_id)
                    if field_value:
                        logger.info(f"Development field {field_id} value: {field_value}")
                        if isinstance(field_value, (str, dict)):
                            extracted_prs = self.extract_pr_info(str(field_value))
                            pr_info.extend(extracted_prs)
                except:
                    continue
            
            # 4. Check branch naming convention in development info
            if dev_info and 'detail' in dev_info:
                for repository in dev_info['detail']:
                    if 'branches' in repository:
                        for branch in repository['branches']:
                            # Check if branch name contains issue key
                            if issue_key.lower() in branch.get('name', '').lower():
                                pr_info.append({
                                    'type': 'branch',
                                    'name': branch.get('name'),
                                    'repository': repository.get('name'),
                                    'url': branch.get('url'),
                                    'status': branch.get('status')
                                })

            # 5. Check commit messages in development info
            if dev_info and 'detail' in dev_info:
                for repository in dev_info['detail']:
                    if 'commits' in repository:
                        for commit in repository['commits']:
                            # Check if commit message contains issue key
                            if issue_key.lower() in commit.get('message', '').lower():
                                pr_info.append({
                                    'type': 'commit',
                                    'hash': commit.get('id'),
                                    'message': commit.get('message'),
                                    'repository': repository.get('name'),
                                    'url': commit.get('url'),
                                    'author': commit.get('author')
                                })

            # Add PR information to issue data
            issue_data['development'] = {
                'pull_requests': pr_info,
                'total_prs': len(pr_info)
            }
            
            return issue_data
            
        except JIRAError as e:
            logger.error(f"Failed to get issue {issue_key}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting issue {issue_key}: {str(e)}")
            return None
            
    def add_comment(self, issue_key: str, comment: str) -> bool:
        """
        Add a comment to a Jira issue.
        
        Args:
            issue_key: Jira issue key
            comment: Comment text
            
        Returns:
            True if comment was added successfully, False otherwise
        """
        if not self.is_connected():
            error = self.get_connection_error() or "Jira client not connected"
            logger.warning(error)
            return False
            
        try:
            self.jira.add_comment(issue_key, comment)
            return True
        except Exception as e:
            logger.error(f"Error adding comment to {issue_key}: {str(e)}")
            return False
            
    def update_issue(self, issue_key: str, fields: Dict[str, Any]) -> bool:
        """
        Update Jira issue fields.
        
        Args:
            issue_key: Jira issue key
            fields: Dictionary of fields to update
            
        Returns:
            True if update was successful, False otherwise
        """
        if not self.is_connected():
            logger.warning("Jira client not connected")
            return False
            
        try:
            issue = self.jira.issue(issue_key)
            issue.update(fields=fields)
            return True
        except Exception as e:
            logger.error(f"Error updating issue {issue_key}: {str(e)}", exc_info=True)
            return False 