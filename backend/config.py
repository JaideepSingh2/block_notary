import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Flask and blockchain configuration"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Blockchain settings
    RPC_URL = os.getenv('RPC_URL')
    PRIVATE_KEY = os.getenv('PRIVATE_KEY')
    CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx', 'png', 'jpg', 'jpeg'}
    
    @staticmethod
    def allowed_file(filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    
    @staticmethod
    def load_contract_abi():
        """Load contract ABI from artifacts"""
        abi_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'blockchain', 
            'artifacts', 
            'contracts', 
            'Notary.sol', 
            'Notary.json'
        )
        
        if os.path.exists(abi_path):
            with open(abi_path, 'r') as f:
                contract_json = json.load(f)
                return contract_json['abi']
        
        # Fallback ABI if artifacts not found
        return [
            {
                "inputs": [{"internalType": "bytes32", "name": "hash", "type": "bytes32"}],
                "name": "storeHash",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "bytes32", "name": "hash", "type": "bytes32"}],
                "name": "verifyHash",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
                "name": "timestamps",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
