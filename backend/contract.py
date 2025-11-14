from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
import os
from config import Config

class NotaryContract:
    """Interface to interact with Notary smart contract"""
    
    def __init__(self):
        """Initialize Web3 connection and contract instance"""
        self.w3 = None
        self.contract = None
        self.account = None
        self._initialize()
    
    def _initialize(self):
        """Set up Web3 and contract connection"""
        try:
            # Connect to RPC endpoint
            self.w3 = Web3(Web3.HTTPProvider(Config.RPC_URL))
            
            # Add PoA middleware for networks like Polygon
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            # Check connection
            if not self.w3.is_connected():
                raise Exception("Failed to connect to Ethereum node")
            
            print(f"✅ Connected to network. Chain ID: {self.w3.eth.chain_id}")
            
            # Load account from private key
            if Config.PRIVATE_KEY:
                self.account = self.w3.eth.account.from_key(Config.PRIVATE_KEY)
                print(f"📍 Using account: {self.account.address}")
            
            # Load contract
            if Config.CONTRACT_ADDRESS:
                abi = Config.get_abi()
                if abi:
                    self.contract = self.w3.eth.contract(
                        address=Web3.to_checksum_address(Config.CONTRACT_ADDRESS),
                        abi=abi
                    )
                    print(f"📜 Contract loaded at: {Config.CONTRACT_ADDRESS}")
                else:
                    print("⚠️ ABI not found. Compile smart contract first.")
            else:
                print("⚠️ CONTRACT_ADDRESS not set in .env")
                
        except Exception as e:
            print(f"❌ Error initializing contract: {str(e)}")
            raise
    
    def store_hash(self, document_hash):
        """
        Store document hash on blockchain
        
        Args:
            document_hash: SHA-256 hash as hex string (without 0x prefix)
            
        Returns:
            dict: Transaction details
        """
        if not self.contract or not self.account:
            raise Exception("Contract or account not initialized")
        
        try:
            # Convert hash to bytes32
            hash_bytes = bytes.fromhex(document_hash)
            
            # Check if already notarized
            if self.is_notarized(document_hash):
                raise Exception("Document already notarized")
            
            # Build transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            # Estimate gas
            gas_estimate = self.contract.functions.storeHash(hash_bytes).estimate_gas({
                'from': self.account.address
            })
            
            # Build transaction
            transaction = self.contract.functions.storeHash(hash_bytes).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': gas_estimate + 10000,  # Add buffer
                'gasPrice': self.w3.eth.gas_price,
            })
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction, 
                private_key=self.account.key
            )
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for receipt
            print(f"⏳ Waiting for transaction {tx_hash.hex()}...")
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            return {
                'success': True,
                'transaction_hash': tx_hash.hex(),
                'block_number': tx_receipt['blockNumber'],
                'gas_used': tx_receipt['gasUsed'],
                'status': tx_receipt['status']
            }
            
        except Exception as e:
            print(f"❌ Error storing hash: {str(e)}")
            raise Exception(f"Failed to store hash: {str(e)}")
    
    def verify_hash(self, document_hash):
        """
        Verify if document hash exists on blockchain
        
        Args:
            document_hash: SHA-256 hash as hex string
            
        Returns:
            dict: Verification details
        """
        if not self.contract:
            raise Exception("Contract not initialized")
        
        try:
            # Convert hash to bytes32
            hash_bytes = bytes.fromhex(document_hash)
            
            # Call contract
            timestamp, notarizer = self.contract.functions.verifyHash(hash_bytes).call()
            
            return {
                'exists': timestamp > 0,
                'timestamp': int(timestamp),
                'notarizer': notarizer,
                'hash': document_hash
            }
            
        except Exception as e:
            print(f"❌ Error verifying hash: {str(e)}")
            raise Exception(f"Failed to verify hash: {str(e)}")
    
    def is_notarized(self, document_hash):
        """
        Check if document is notarized
        
        Args:
            document_hash: SHA-256 hash as hex string
            
        Returns:
            bool: True if notarized
        """
        try:
            hash_bytes = bytes.fromhex(document_hash)
            return self.contract.functions.isNotarized(hash_bytes).call()
        except:
            return False
    
    def get_notarization_details(self, document_hash):
        """
        Get full notarization details
        
        Args:
            document_hash: SHA-256 hash as hex string
            
        Returns:
            dict: Complete details
        """
        if not self.contract:
            raise Exception("Contract not initialized")
        
        try:
            hash_bytes = bytes.fromhex(document_hash)
            timestamp, notarizer, exists = self.contract.functions.getNotarizationDetails(hash_bytes).call()
            
            return {
                'exists': exists,
                'timestamp': int(timestamp),
                'notarizer': notarizer,
                'hash': document_hash,
                'block_explorer_url': self._get_explorer_url(document_hash)
            }
            
        except Exception as e:
            raise Exception(f"Failed to get details: {str(e)}")
    
    def _get_explorer_url(self, tx_hash=None):
        """Get block explorer URL based on network"""
        chain_id = self.w3.eth.chain_id
        
        explorers = {
            1: "https://etherscan.io",
            11155111: "https://sepolia.etherscan.io",
            137: "https://polygonscan.com",
            80001: "https://mumbai.polygonscan.com"
        }
        
        base_url = explorers.get(chain_id, "https://etherscan.io")
        
        if tx_hash:
            return f"{base_url}/tx/{tx_hash}"
        return base_url

# Create global instance
notary_contract = NotaryContract()