import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
import re

class Config:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        
        # MCP Server settings
        self.mcp_url = os.getenv("MCP_URL", "http://localhost:5000")
        self.mcp_workspace_root = os.getenv("MCP_WORKSPACE_ROOT", os.getcwd())
        self.mcp_test_output_dir = os.getenv("MCP_TEST_OUTPUT_DIR", "tests/generated")
        
        # Bitbucket settings
        self.bitbucket_url = os.getenv("BITBUCKET_URL", "https://bitbucket.org")
        self.bitbucket_api_key = os.getenv("BITBUCKET_API_KEY")
        self.bitbucket_org = os.getenv("BITBUCKET_ORG", "zenotiengineeringteam")
        self.bitbucket_repo = os.getenv("BITBUCKET_REPO", "maindbsql")
        
    def validate_bitbucket_config(self) -> tuple[bool, list[str]]:
        """Validate Bitbucket configuration and return missing fields"""
        missing = []
        if not self.bitbucket_url:
            missing.append("BITBUCKET_URL")
        if not self.bitbucket_api_key:
            missing.append("BITBUCKET_API_KEY")
        if not self.bitbucket_org:
            missing.append("BITBUCKET_ORG")
        if not self.bitbucket_repo:
            missing.append("BITBUCKET_REPO")
        return len(missing) == 0, missing
    
    def prompt_for_credentials(self) -> None:
        """Prompt user for missing Bitbucket credentials and configuration"""
        is_valid, missing = self.validate_bitbucket_config()
        if is_valid:
            return
            
        print("\nBitbucket Configuration Setup")
        print("============================")
        print("Please provide the following Bitbucket details:")
        print("1. URL: The Bitbucket server URL")
        print("2. API Key: Your Bitbucket API key")
        print("3. Organization: Your Bitbucket organization/team name")
        print("4. Repository: The repository name\n")
        
        env_path = Path(".env")
        env_content = env_path.read_text() if env_path.exists() else ""
        
        for field in missing:
            value = input(f"{field}: ")
            if value:
                if field not in env_content:
                    with env_path.open("a") as f:
                        f.write(f"\n{field}={value}")
                else:
                    env_content = re.sub(
                        f"{field}=.*",
                        f"{field}={value}",
                        env_content
                    )
                    env_path.write_text(env_content)
    
    @property
    def repository_path(self) -> str:
        """Get the full repository path in org/repo format"""
        return f"{self.bitbucket_org}/{self.bitbucket_repo}"
    
    @property
    def test_output_path(self) -> Path:
        """Get the full path to the test output directory"""
        return Path(self.mcp_workspace_root) / self.mcp_test_output_dir