from jira import JIRA
import os
import re

class JiraService:
    def __init__(self):
        self.jira = JIRA(
            server=os.getenv('JIRA_URL'),
            basic_auth=(os.getenv('JIRA_EMAIL'), os.getenv('JIRA_API_TOKEN'))
        )
    
    def extract_ticket_id(self, url):
        """Extract ticket ID from Jira URL"""
        pattern = r'/browse/([A-Z]+-\d+)'
        match = re.search(pattern, url)
        if not match:
            raise ValueError("Invalid Jira ticket URL")
        return match.group(1)
    
    def get_ticket_details(self, url):
        """Fetch ticket details from Jira"""
        ticket_id = self.extract_ticket_id(url)
        issue = self.jira.issue(ticket_id)
        
        # Extract acceptance criteria from custom field if available
        acceptance_criteria = ""
        if hasattr(issue.fields, 'customfield_10001'):  # Update field ID as needed
            acceptance_criteria = issue.fields.customfield_10001
        
        return {
            'id': ticket_id,
            'title': issue.fields.summary,
            'description': issue.fields.description or "",
            'acceptance_criteria': acceptance_criteria,
            'subtasks': [
                {
                    'id': subtask.key,
                    'summary': subtask.fields.summary
                } for subtask in issue.fields.subtasks
            ],
            'linked_issues': self._get_linked_issues(issue),
            'epic': self._get_epic(issue),
            'story_points': getattr(issue.fields, 'customfield_10002', None)  # Update field ID as needed
        }
    
    def _get_linked_issues(self, issue):
        """Get linked issues"""
        linked_issues = []
        if hasattr(issue.fields, 'issuelinks'):
            for link in issue.fields.issuelinks:
                if hasattr(link, 'outwardIssue'):
                    linked_issues.append({
                        'id': link.outwardIssue.key,
                        'type': link.type.outward,
                        'summary': link.outwardIssue.fields.summary
                    })
                elif hasattr(link, 'inwardIssue'):
                    linked_issues.append({
                        'id': link.inwardIssue.key,
                        'type': link.type.inward,
                        'summary': link.inwardIssue.fields.summary
                    })
        return linked_issues
    
    def _get_epic(self, issue):
        """Get epic details if issue belongs to one"""
        epic = None
        if hasattr(issue.fields, 'customfield_10014'):  # Epic Link field
            epic_key = issue.fields.customfield_10014
            if epic_key:
                epic_issue = self.jira.issue(epic_key)
                epic = {
                    'id': epic_key,
                    'name': epic_issue.fields.summary
                }
        return epic 