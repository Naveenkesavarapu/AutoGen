from PySide6.QtWidgets import (
    QWizard, QWizardPage, QLineEdit, QLabel,
    QVBoxLayout, QMessageBox, QPushButton
)
from PySide6.QtCore import Qt
from jira import JIRA
from testrail_api import TestRailAPI
import os
import json
import requests

class SetupWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AutoGen Setup Wizard")
        self.setWizardStyle(QWizard.ModernStyle)
        
        # Add pages
        self.addPage(IntroPage())
        self.addPage(JiraConfigPage())
        self.addPage(TestRailConfigPage())
        self.addPage(LLMConfigPage())
        
        self.setMinimumSize(600, 400)
    
    def accept(self):
        """Save configuration when wizard is completed"""
        try:
            # Collect all configuration
            config = {
                # Jira
                'JIRA_URL': self.page(1).jira_url_input.text().strip(),
                'JIRA_EMAIL': self.page(1).email_input.text().strip(),
                'JIRA_API_TOKEN': self.page(1).token_input.text().strip(),
                
                # TestRail
                'TESTRAIL_URL': self.page(2).url_input.text().strip(),
                'TESTRAIL_EMAIL': self.page(2).email_input.text().strip(),
                'TESTRAIL_API_KEY': self.page(2).api_key_input.text().strip(),
                
                # Zeenie LLM
                'LLM_API_ENDPOINT': self.page(3).endpoint_input.text().strip(),
                'LLM_API_KEY': self.page(3).api_key_input.text().strip()
            }
            
            # Create .env file
            with open('.env', 'w') as f:
                for key, value in config.items():
                    f.write(f'{key}={value}\n')
            
            QMessageBox.information(self, "Setup Complete", 
                "Configuration has been saved successfully!\nYou can now start using the application.")
            super().accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")

    def save_configuration(self):
        config = {
            'testrail': {
                'url': self.page(2).url_input.text().strip(),
                'email': self.page(2).email_input.text().strip(),
                'api_key': self.page(2).api_key_input.text().strip()
            }
        }
        
        # Save to config file
        config_dir = os.path.join(os.path.expanduser('~'), '.autogen')
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, 'config.json')
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)

class IntroPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to AutoGen Setup")
        
        layout = QVBoxLayout()
        intro_text = QLabel(
            "Welcome to AutoGen - Automated Test Case Generator!\n\n"
            "This wizard will help you configure the necessary API credentials "
            "for Jira, TestRail, and Zeenie LLM integration.\n\n"
            "Please have your API credentials ready for:\n"
            "• Jira\n"
            "• TestRail\n"
            "• Zeenie LLM Service\n\n"
            "Click Next to begin the setup process."
        )
        intro_text.setWordWrap(True)
        layout.addWidget(intro_text)
        self.setLayout(layout)

class JiraConfigPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Jira Configuration")
        self.setSubTitle("Enter your Jira credentials")
        
        layout = QVBoxLayout()
        
        # Jira URL
        layout.addWidget(QLabel("Jira URL:"))
        self.jira_url_input = QLineEdit()
        self.jira_url_input.setPlaceholderText("https://your-domain.atlassian.net")
        layout.addWidget(self.jira_url_input)
        
        # Email
        layout.addWidget(QLabel("Email:"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your.email@company.com")
        layout.addWidget(self.email_input)
        
        # API Token
        layout.addWidget(QLabel("API Token:"))
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setPlaceholderText("Your Jira API token")
        layout.addWidget(self.token_input)
        
        # Test connection button
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_connection)
        layout.addWidget(self.test_button)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def test_connection(self):
        """Test Jira connection"""
        try:
            jira = JIRA(
                server=self.jira_url_input.text().strip(),
                basic_auth=(
                    self.email_input.text().strip(),
                    self.token_input.text().strip()
                )
            )
            # Try to access Jira to verify credentials
            jira.myself()
            QMessageBox.information(self, "Success", "Successfully connected to Jira!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to connect to Jira: {str(e)}")

class TestRailConfigPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("TestRail Configuration")
        self.setSubTitle("Please enter your TestRail credentials")

        # Create layout
        layout = QVBoxLayout()
        
        # URL input
        url_label = QLabel("TestRail URL:")
        self.url_input = QLineEdit()
        self.url_input.setText("https://zenoti.testrail.io")
        layout.addWidget(url_label)
        layout.addWidget(self.url_input)
        
        # Email input
        email_label = QLabel("Email:")
        self.email_input = QLineEdit()
        self.email_input.setText("anushad@zenoti.com")
        layout.addWidget(email_label)
        layout.addWidget(self.email_input)
        
        # API Key input
        api_key_label = QLabel("API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setText("Prasad@994")
        layout.addWidget(api_key_label)
        layout.addWidget(self.api_key_input)
        
        self.setLayout(layout)

    def validatePage(self) -> bool:
        try:
            url = self.url_input.text().strip()
            email = self.email_input.text().strip()
            api_key = self.api_key_input.text().strip()
            
            if not url or not email or not api_key:
                QMessageBox.warning(self, "Validation Error", "All fields are required")
                return False
                
            # Test the connection
            api = TestRailAPI(base_url=url, email=email, password=api_key)
            # Try to make a simple API call to verify credentials
            api.projects.get_projects()  # This is the correct method to test connection
            
            # Save configuration if validation succeeds
            config = {
                'testrail': {
                    'url': url,
                    'email': email,
                    'api_key': api_key
                }
            }
            
            # Save to config file
            config_dir = os.path.join(os.path.expanduser('~'), '.autogen')
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, 'config.json')
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
            
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect to TestRail: {str(e)}")
            return False

class LLMConfigPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Zeenie LLM Configuration")
        self.setSubTitle("Enter your Zeenie LLM API credentials")
        
        layout = QVBoxLayout()
        
        # API Endpoint
        layout.addWidget(QLabel("API Endpoint:"))
        self.endpoint_input = QLineEdit()
        self.endpoint_input.setText("https://zeenie-llm-api.zenotibeta.com/GenericLLM")
        self.endpoint_input.setPlaceholderText("https://zeenie-llm-api.zenotibeta.com/GenericLLM")
        layout.addWidget(self.endpoint_input)
        
        # API Key
        layout.addWidget(QLabel("API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Your Zeenie LLM API key")
        layout.addWidget(self.api_key_input)
        
        # Test connection button
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_connection)
        layout.addWidget(self.test_button)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def test_connection(self):
        """Test Zeenie LLM connection"""
        try:
            api_key = self.api_key_input.text().strip()
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'x-apikey {api_key}',
                'x-api-key': api_key
            }
            
            # Simple test request
            response = requests.post(
                self.endpoint_input.text().strip(),
                headers=headers,
                json={'prompt': 'Test connection'}
            )
            
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "Successfully connected to Zeenie LLM service!")
            else:
                raise Exception(f"API returned status code {response.status_code}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to connect to Zeenie LLM service: {str(e)}") 