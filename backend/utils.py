import hashlib

def compute_sha256(file):
    """
    Compute SHA-256 hash of uploaded file.
    
    Args:
        file: FileStorage object from Flask request.files
        
    Returns:
        str: Hexadecimal hash string
    """
    sha256_hash = hashlib.sha256()
    
    # Read file in chunks to handle large files efficiently
    for byte_block in iter(lambda: file.read(4096), b""):
        sha256_hash.update(byte_block)
    
    # Reset file pointer to beginning
    file.seek(0)
    
    return sha256_hash.hexdigest()


def hash_to_bytes32(hash_hex):
    """
    Convert hex hash string to bytes32 format for Solidity.
    
    Args:
        hash_hex: Hexadecimal hash string
        
    Returns:
        bytes: 32-byte hash
    """
    if hash_hex.startswith('0x'):
        hash_hex = hash_hex[2:]
    return bytes.fromhex(hash_hex)
