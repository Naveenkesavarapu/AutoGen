import sys
import os
from dotenv import load_dotenv
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QLineEdit, QPushButton, QTextEdit,
    QLabel, QProgressBar, QMessageBox, QFormLayout,
    QSpinBox
)
from PySide6.QtCore import Qt, QThread, Signal

from services.jira_service import JiraService
from services.git_service import GitService
from services.testrail_service import TestRailService
from services.ai_service import AIService
from ui.setup_wizard import SetupWizard

# Load environment variables
load_dotenv()

class TestCaseGeneratorThread(QThread):
    progress = Signal(int, str)
    finished = Signal(bool, str)
    
    def __init__(self, jira_url, project_id, suite_id, section_id):
        super().__init__()
        self.jira_url = jira_url
        self.project_id = project_id
        self.suite_id = suite_id
        self.section_id = section_id
    
    def run(self):
        try:
            # Initialize services
            jira_service = JiraService()
            git_service = GitService()
            testrail_service = TestRailService()
            ai_service = AIService()
            
            # Step 1: Get Jira ticket details
            self.progress.emit(20, "Fetching Jira ticket details...")
            ticket_data = jira_service.get_ticket_details(self.jira_url)
            
            # Step 2: Find and analyze Git branch
            self.progress.emit(40, "Analyzing code changes...")
            branch_name = git_service.find_branch_by_ticket(ticket_data['id'])
            if branch_name:
                code_analysis = git_service.analyze_code_changes(branch_name)
            else:
                code_analysis = {'changed_files': [], 'affected_components': []}
            
            # Step 3: Generate test cases
            self.progress.emit(60, "Generating test cases...")
            test_cases = ai_service.generate_test_cases(ticket_data, code_analysis)
            
            if not test_cases:
                raise Exception("No test cases were generated")
            
            # Step 4: Push to TestRail
            self.progress.emit(80, "Pushing test cases to TestRail...")
            created_cases = testrail_service.create_test_cases(
                self.project_id,
                self.suite_id,
                self.section_id,
                test_cases,
                ticket_data['id']
            )
            
            # Step 5: Create test run
            self.progress.emit(90, "Creating test run...")
            case_ids = [case['id'] for case in created_cases]
            test_run = testrail_service.create_test_run(
                self.project_id,
                self.suite_id,
                ticket_data['title'],
                case_ids,
                ticket_data['id']
            )
            
            self.progress.emit(100, "Completed!")
            self.finished.emit(True, f"Successfully created {len(created_cases)} test cases and test run in TestRail")
            
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Check if configuration exists
        if not self.check_configuration():
            # Show setup wizard
            wizard = SetupWizard(self)
            if wizard.exec() == SetupWizard.Rejected:
                # User cancelled setup
                sys.exit(0)
            # Reload environment variables after setup
            load_dotenv(override=True)
        
        self.init_ui()
    
    def check_configuration(self):
        """Check if .env file exists and contains required variables"""
        if not os.path.exists('.env'):
            return False
        
        load_dotenv()
        required_vars = [
            'JIRA_URL', 'JIRA_EMAIL', 'JIRA_API_TOKEN',
            'TESTRAIL_URL', 'TESTRAIL_EMAIL', 'TESTRAIL_API_KEY',
            'LLM_API_KEY'
        ]
        
        for var in required_vars:
            if not os.getenv(var):
                return False
        
        return True
    
    def init_ui(self):
        """Initialize the main UI"""
        self.setWindowTitle("AutoGen - Test Case Generator")
        self.setMinimumSize(800, 600)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Add settings button
        settings_layout = QHBoxLayout()
        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(self.show_settings)
        settings_layout.addStretch()
        settings_layout.addWidget(settings_button)
        layout.addLayout(settings_layout)
        
        # Form layout for inputs
        form_layout = QFormLayout()
        
        # Jira URL input
        self.jira_input = QLineEdit()
        self.jira_input.setPlaceholderText("https://yourcompany.atlassian.net/browse/FEAT-123")
        form_layout.addRow("Jira Ticket URL:", self.jira_input)
        
        # TestRail project ID
        self.project_id_input = QSpinBox()
        self.project_id_input.setMinimum(1)
        self.project_id_input.setMaximum(9999)
        form_layout.addRow("TestRail Project ID:", self.project_id_input)
        
        # TestRail suite ID
        self.suite_id_input = QSpinBox()
        self.suite_id_input.setMinimum(1)
        self.suite_id_input.setMaximum(9999)
        form_layout.addRow("TestRail Suite ID:", self.suite_id_input)
        
        # TestRail section ID
        self.section_id_input = QSpinBox()
        self.section_id_input.setMinimum(1)
        self.section_id_input.setMaximum(9999)
        form_layout.addRow("TestRail Section ID:", self.section_id_input)
        
        layout.addLayout(form_layout)
        
        # Generate button
        self.generate_button = QPushButton("Generate Test Cases")
        self.generate_button.clicked.connect(self.generate_test_cases)
        layout.addWidget(self.generate_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        
        # Output area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)
    
    def show_settings(self):
        """Show settings wizard to update configuration"""
        wizard = SetupWizard(self)
        if wizard.exec() == SetupWizard.Accepted:
            # Reload environment variables after updating configuration
            load_dotenv(override=True)
            QMessageBox.information(self, "Settings Updated", 
                "Configuration has been updated successfully!")
    
    def generate_test_cases(self):
        """Start test case generation process"""
        jira_url = self.jira_input.text().strip()
        project_id = self.project_id_input.value()
        suite_id = self.suite_id_input.value()
        section_id = self.section_id_input.value()
        
        if not jira_url:
            QMessageBox.warning(self, "Error", "Please enter a Jira ticket URL")
            return
        
        if not all([project_id, suite_id, section_id]):
            QMessageBox.warning(self, "Error", "Please enter all TestRail IDs")
            return
        
        # Disable inputs during processing
        self.generate_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.output_text.clear()
        
        # Create and start worker thread
        self.worker = TestCaseGeneratorThread(jira_url, project_id, suite_id, section_id)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.process_completed)
        self.worker.start()
    
    def update_progress(self, value, message):
        """Update progress bar and status"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        self.output_text.append(message)
    
    def process_completed(self, success, message):
        """Handle process completion"""
        self.generate_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)
        
        self.output_text.append(message)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 