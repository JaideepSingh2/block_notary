import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    
    # Blockchain settings
    RPC_URL = os.getenv('RPC_URL')
    PRIVATE_KEY = os.getenv('PRIVATE_KEY')
    CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    
    # ABI file path
    ABI_PATH = os.path.join(os.path.dirname(__file__), '..', 'blockchain', 'artifacts', 'contracts', 'Notary.sol', 'Notary.json')
    
    @staticmethod
    def get_abi():
        """Load contract ABI from artifacts"""
        try:
            with open(Config.ABI_PATH, 'r') as f:
                contract_json = json.load(f)
                return contract_json['abi']
        except FileNotFoundError:
            print("⚠️ ABI file not found. Make sure to compile the smart contract first.")
            return None
    
    @staticmethod
    def validate_config():
        """Validate required configuration"""
        required = ['RPC_URL', 'PRIVATE_KEY', 'CONTRACT_ADDRESS']
        missing = [key for key in required if not os.getenv(key)]
        
        if missing:
            print(f"⚠️ Missing configuration: {', '.join(missing)}")
            return False
        return True