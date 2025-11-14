import hashlib
from functools import wraps
from flask import jsonify

def compute_sha256(file_data):
    """
    Compute SHA-256 hash of file data
    
    Args:
        file_data: File object or bytes
        
    Returns:
        str: Hexadecimal hash string
    """
    sha256_hash = hashlib.sha256()
    
    # Handle file object
    if hasattr(file_data, 'read'):
        # Read file in chunks to handle large files
        for chunk in iter(lambda: file_data.read(4096), b''):
            sha256_hash.update(chunk)
        file_data.seek(0)  # Reset file pointer
    else:
        # Handle bytes directly
        sha256_hash.update(file_data)
    
    return sha256_hash.hexdigest()


def allowed_file(filename, allowed_extensions):
    """
    Check if file extension is allowed
    
    Args:
        filename: Name of the file
        allowed_extensions: Set of allowed extensions
        
    Returns:
        bool: True if allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def handle_errors(f):
    """
    Decorator to handle errors in route functions
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    return decorated_function


def format_timestamp(timestamp):
    """
    Format Unix timestamp to human-readable date
    
    Args:
        timestamp: Unix timestamp (int)
        
    Returns:
        str: Formatted date string
    """
    from datetime import datetime
    
    if timestamp == 0:
        return "Not notarized"
    
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def validate_hash(hash_string):
    """
    Validate if string is a valid SHA-256 hash
    
    Args:
        hash_string: String to validate
        
    Returns:
        bool: True if valid hash, False otherwise
    """
    if not hash_string:
        return False
    
    # SHA-256 produces 64 character hex string
    if len(hash_string) != 64:
        return False
    
    # Check if all characters are hexadecimal
    try:
        int(hash_string, 16)
        return True
    except ValueError:
        return False