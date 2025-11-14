from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from config import Config
from contract import notary_contract
from utils import compute_sha256, allowed_file, handle_errors, format_timestamp, validate_hash

# Initialize Flask app
app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

app.config.from_object(Config)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ================================
# PAGE ROUTES
# ================================

@app.route('/')
def index():
    """Homepage"""
    return render_template('index.html')

@app.route('/notarize')
def notarize_page():
    """Document notarization page"""
    return render_template('notarize.html')

@app.route('/verify')
def verify_page():
    """Document verification page"""
    return render_template('verify.html')

# ================================
# API ROUTES
# ================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        connected = notary_contract.w3.is_connected()
        chain_id = notary_contract.w3.eth.chain_id if connected else None
        
        return jsonify({
            'success': True,
            'blockchain_connected': connected,
            'chain_id': chain_id,
            'contract_address': Config.CONTRACT_ADDRESS,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/compute-hash', methods=['POST'])
@handle_errors
def compute_hash():
    """
    Compute SHA-256 hash of uploaded file
    Returns hash to frontend (MetaMask will handle transaction)
    """
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file provided'
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'No file selected'
        }), 400
    
    # Validate file type
    if not allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
        return jsonify({
            'success': False,
            'error': 'File type not allowed'
        }), 400
    
    # Compute hash
    document_hash = compute_sha256(file)
    
    # Check if already notarized
    is_notarized = notary_contract.is_notarized(document_hash)
    
    return jsonify({
        'success': True,
        'hash': document_hash,
        'filename': secure_filename(file.filename),
        'already_notarized': is_notarized
    })

@app.route('/api/notarize', methods=['POST'])
@handle_errors
def api_notarize():
    """
    Notarize document hash on blockchain
    This is called from backend (server-side transaction)
    """
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file provided'
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'No file selected'
        }), 400
    
    # Compute hash
    document_hash = compute_sha256(file)
    
    # Store on blockchain
    result = notary_contract.store_hash(document_hash)
    
    return jsonify({
        'success': True,
        'hash': document_hash,
        'filename': secure_filename(file.filename),
        'transaction': result
    })

@app.route('/api/verify', methods=['POST'])
@handle_errors
def api_verify():
    """
    Verify document hash on blockchain
    Accepts either file upload or hash string
    """
    document_hash = None
    filename = None
    
    # Check if hash is provided directly
    if request.is_json:
        data = request.get_json()
        document_hash = data.get('hash')
        
        if not document_hash:
            return jsonify({
                'success': False,
                'error': 'Hash not provided'
            }), 400
            
        # Validate hash format
        if not validate_hash(document_hash):
            return jsonify({
                'success': False,
                'error': 'Invalid hash format'
            }), 400
    
    # Check if file is uploaded
    elif 'file' in request.files:
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        document_hash = compute_sha256(file)
        filename = secure_filename(file.filename)
    
    else:
        return jsonify({
            'success': False,
            'error': 'No file or hash provided'
        }), 400
    
    # Verify on blockchain
    result = notary_contract.get_notarization_details(document_hash)
    
    response = {
        'success': True,
        'hash': document_hash,
        'exists': result['exists'],
        'notarizer': result['notarizer'],
        'timestamp': result['timestamp'],
        'formatted_timestamp': format_timestamp(result['timestamp']),
        'block_explorer_url': result['block_explorer_url']
    }
    
    if filename:
        response['filename'] = filename
    
    return jsonify(response)

@app.route('/api/contract-info', methods=['GET'])
def contract_info():
    """Get contract information"""
    try:
        return jsonify({
            'success': True,
            'contract_address': Config.CONTRACT_ADDRESS,
            'rpc_url': Config.RPC_URL.split('/')[-1] if Config.RPC_URL else None,
            'chain_id': notary_contract.w3.eth.chain_id,
            'connected': notary_contract.w3.is_connected()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ================================
# ERROR HANDLERS
# ================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

# ================================
# MAIN
# ================================

if __name__ == '__main__':
    # Validate configuration
    if not Config.validate_config():
        print("⚠️ Please configure .env file properly")
        print("Required: RPC_URL, PRIVATE_KEY, CONTRACT_ADDRESS")
    
    print("\n" + "="*50)
    print("🚀 Starting Notary DApp Backend")
    print("="*50)
    print(f"📍 Contract Address: {Config.CONTRACT_ADDRESS}")
    print(f"🌐 RPC URL: {Config.RPC_URL[:50]}...")
    print(f"⚙️  Environment: {Config.FLASK_ENV}")
    print("="*50 + "\n")
    
    app.run(
        debug=Config.DEBUG,
        host='0.0.0.0',
        port=5000
    )