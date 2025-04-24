import os
import logging
from dotenv import load_dotenv
from mcp_server.server import app
from services.processor import DataProcessor
from utils.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_app():
    """Initialize the application components"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize configuration
        config = Config()
        
        # Initialize services
        processor = DataProcessor(config)
        
        logger.info("Application initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing application: {str(e)}")
        return False

def main():
    """Main application entry point"""
    if initialize_app():
        # Get port from environment or use default
        port = int(os.environ.get('PORT', 5000))
        
        # Start the server
        logger.info(f"Starting server on port {port}")
        app.run(host='0.0.0.0', port=port)
    else:
        logger.error("Failed to initialize application")
        exit(1)

if __name__ == '__main__':
    main() 