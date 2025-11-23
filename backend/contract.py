from web3 import Web3
from config import Config

class BlockchainContract:
    """Handles interaction with the Notary smart contract"""
    
    def __init__(self):
        """Initialize Web3 connection and contract instance"""
        self.w3 = None
        self.contract = None
        self.account = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Establish connection to blockchain"""
        try:
            # Connect to RPC endpoint
            if Config.RPC_URL:
                self.w3 = Web3(Web3.HTTPProvider(Config.RPC_URL))
                
                if not self.w3.is_connected():
                    print("Warning: Unable to connect to blockchain")
                    return
                
                # Load contract
                if Config.CONTRACT_ADDRESS:
                    abi = Config.load_contract_abi()
                    self.contract = self.w3.eth.contract(
                        address=Web3.to_checksum_address(Config.CONTRACT_ADDRESS),
                        abi=abi
                    )
                
                # Load account from private key
                if Config.PRIVATE_KEY:
                    self.account = self.w3.eth.account.from_key(Config.PRIVATE_KEY)
                
                print(f"✓ Connected to blockchain: {self.w3.is_connected()}")
            else:
                print("Warning: RPC_URL not configured")
                
        except Exception as e:
            print(f"Error initializing blockchain connection: {str(e)}")
    
    def verify_hash(self, hash_hex):
        """
        Verify if a hash exists on blockchain and return timestamp.
        
        Args:
            hash_hex: Hexadecimal hash string
            
        Returns:
            int: Timestamp (0 if not found)
        """
        try:
            if not self.contract:
                return {"error": "Contract not initialized"}
            
            # Convert hash to bytes32
            hash_bytes = bytes.fromhex(hash_hex)
            
            # Call verifyHash function
            timestamp = self.contract.functions.verifyHash(hash_bytes).call()
            
            return int(timestamp)
            
        except Exception as e:
            print(f"Error verifying hash: {str(e)}")
            return {"error": str(e)}
    
    def store_hash_transaction(self, hash_hex):
        """
        Create transaction data for storing hash (to be signed by MetaMask).
        
        Args:
            hash_hex: Hexadecimal hash string
            
        Returns:
            dict: Transaction details
        """
        try:
            if not self.contract:
                return {"error": "Contract not initialized"}
            
            # Convert hash to bytes32
            hash_bytes = bytes.fromhex(hash_hex)
            
            # Build transaction
            return {
                "to": Config.CONTRACT_ADDRESS,
                "data": self.contract.encodeABI(fn_name="storeHash", args=[hash_bytes])
            }
            
        except Exception as e:
            print(f"Error creating transaction: {str(e)}")
            return {"error": str(e)}
    
    def get_gas_estimate(self, hash_hex, from_address):
        """
        Estimate gas for storeHash transaction.
        
        Args:
            hash_hex: Hexadecimal hash string
            from_address: User's wallet address
            
        Returns:
            int: Estimated gas
        """
        try:
            if not self.contract:
                return 100000  # Default estimate
            
            hash_bytes = bytes.fromhex(hash_hex)
            
            gas = self.contract.functions.storeHash(hash_bytes).estimate_gas({
                'from': Web3.to_checksum_address(from_address)
            })
            
            return gas
            
        except Exception as e:
            print(f"Error estimating gas: {str(e)}")
            return 100000  # Default estimate


# Create global instance
blockchain = BlockchainContract()
