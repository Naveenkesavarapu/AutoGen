from git import Repo
import os
import ast
from typing import List, Dict

class GitService:
    def __init__(self, repo_path: str = None):
        """Initialize GitService with repository path"""
        self.repo_path = repo_path or os.getcwd()
        self.repo = Repo(self.repo_path)
    
    def find_branch_by_ticket(self, ticket_id: str) -> str:
        """Find branch containing ticket ID"""
        for branch in self.repo.heads:
            if ticket_id.lower() in branch.name.lower():
                return branch.name
        return None
    
    def get_changed_files(self, branch_name: str) -> List[Dict]:
        """Get list of changed files in the branch"""
        main_branch = 'main' if 'main' in self.repo.heads else 'master'
        diff_index = self.repo.heads[main_branch].commit.diff(branch_name)
        
        changed_files = []
        for diff in diff_index:
            if diff.a_path:
                changed_files.append({
                    'path': diff.a_path,
                    'change_type': diff.change_type,
                    'file_type': os.path.splitext(diff.a_path)[1][1:] if '.' in diff.a_path else None
                })
        
        return changed_files
    
    def analyze_code_changes(self, branch_name: str) -> Dict:
        """Analyze code changes for test impact"""
        changed_files = self.get_changed_files(branch_name)
        analysis = {
            'changed_files': changed_files,
            'affected_components': [],
            'dependencies': []
        }
        
        for file in changed_files:
            if file['file_type'] in ['py', 'js', 'ts', 'jsx', 'tsx']:
                try:
                    file_path = os.path.join(self.repo_path, file['path'])
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        if file['file_type'] == 'py':
                            self._analyze_python_file(content, analysis)
                        # Add analyzers for other file types as needed
                            
                except Exception as e:
                    print(f"Error analyzing file {file['path']}: {str(e)}")
        
        return analysis
    
    def _analyze_python_file(self, content: str, analysis: Dict):
        """Analyze Python file for components and dependencies"""
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    analysis['affected_components'].append({
                        'type': 'class',
                        'name': node.name,
                        'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                    })
                elif isinstance(node, ast.Import):
                    for name in node.names:
                        analysis['dependencies'].append({
                            'type': 'import',
                            'name': name.name
                        })
                elif isinstance(node, ast.ImportFrom):
                    analysis['dependencies'].append({
                        'type': 'import_from',
                        'module': node.module,
                        'names': [n.name for n in node.names]
                    })
        except Exception as e:
            print(f"Error in Python analysis: {str(e)}") 