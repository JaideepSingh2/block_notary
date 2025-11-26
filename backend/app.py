from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime

from config import Config
from contract import blockchain
from utils import compute_sha256, generate_otp, send_otp_email
from document_signer import document_signer

# Initialize Flask app
app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
app.config.from_object(Config)


# ===== IN-MEMORY USER STORE (for demo) =====

# In a real system this would be in a database.
# Keys are Aadhaar numbers (as strings); values contain email and name.
REGISTERED_USERS = {
    "123412341234": {"email": "js452@snu.edu.in", "name": "Jaideep Singh"},
    "123456789012": {"email": "ab363@snu.edu.in", "name": "Ballu"},
}

# Document types available for notarization
DOCUMENT_TYPES = {
    "birth_certificate": "Birth Certificate",
    "degree_certificate": "Degree/Education Certificate", 
    "property_deed": "Property Deed",
    "employment_letter": "Employment Letter",
    "legal_contract": "Legal Contract/Agreement",
    "identity_document": "Identity Document",
    "other": "Other Document"
}

# ===== DOCUMENT METADATA STORE =====
# In production, use a database. For demo, using a JSON file.
METADATA_FILE = os.path.join(os.path.dirname(__file__), 'instance', 'document_metadata.json')

def load_document_metadata():
    """Load document metadata from JSON file."""
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_document_metadata(metadata):
    """Save document metadata to JSON file."""
    os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

def store_document_info(doc_hash, aadhaar, doc_type, filename):
    """Store document metadata after blockchain notarization."""
    metadata = load_document_metadata()
    user = REGISTERED_USERS.get(aadhaar, {})
    metadata[doc_hash] = {
        "owner_aadhaar": aadhaar,
        "owner_name": user.get("name", "Unknown"),
        "document_type": doc_type,
        "document_type_label": DOCUMENT_TYPES.get(doc_type, "Other Document"),
        "filename": filename,
        "created_at": datetime.now().isoformat()
    }
    save_document_metadata(metadata)

def get_document_info(doc_hash):
    """Get document metadata by hash."""
    metadata = load_document_metadata()
    return metadata.get(doc_hash)


# ===== ROUTES =====

@app.route("/")
def home():
    """Homepage - redirect to login if not authenticated"""
    if not session.get("is_authenticated"):
        return redirect(url_for("login"))
    aadhaar = session.get("user_aadhaar")
    user = REGISTERED_USERS.get(aadhaar, {})
    return render_template("index.html", user_name=user.get("name", aadhaar), user_aadhaar=aadhaar)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page using Aadhaar and email OTP."""
    if request.method == "GET":
        return render_template("login.html")

    data = request.form
    aadhaar = (data.get("aadhaar") or "").strip()

    if not aadhaar:
        return render_template("login.html", error="Aadhaar number is required")

    user = REGISTERED_USERS.get(aadhaar)
    if not user:
        return render_template("login.html", error="User not found. Please contact administrator.")

    otp = generate_otp()
    session["pending_aadhaar"] = aadhaar
    session["pending_otp"] = otp

    send_otp_email(user["email"], otp)

    return render_template("verify_otp.html", aadhaar=aadhaar, info="OTP has been sent to your registered email.")


@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    """Verify submitted OTP and create logged-in session."""
    submitted_otp = (request.form.get("otp") or "").strip()
    aadhaar = session.get("pending_aadhaar")
    expected_otp = session.get("pending_otp")

    if not aadhaar or not expected_otp:
        return redirect(url_for("login"))

    if submitted_otp != expected_otp:
        return render_template("verify_otp.html", aadhaar=aadhaar, error="Invalid OTP. Please try again.")

    # OTP valid: establish logged-in session
    session.pop("pending_otp", None)
    session["user_aadhaar"] = aadhaar
    session["is_authenticated"] = True

    return redirect(url_for("home"))


@app.route("/logout", methods=["POST"])
def logout():
    """Log out the current user."""
    session.clear()
    return redirect(url_for("home"))


@app.route("/notarize")
def notarize_page():
    """Document notarization page"""
    if not session.get("is_authenticated"):
        return redirect(url_for("login"))
    aadhaar = session.get("user_aadhaar")
    user = REGISTERED_USERS.get(aadhaar, {})
    return render_template("notarize.html", 
                           user_name=user.get("name", aadhaar), 
                           user_aadhaar=aadhaar,
                           document_types=DOCUMENT_TYPES)


@app.route("/verify")
def verify_page():
    """Document verification page"""
    if not session.get("is_authenticated"):
        return redirect(url_for("login"))
    aadhaar = session.get("user_aadhaar")
    user = REGISTERED_USERS.get(aadhaar, {})
    return render_template("verify.html", user_name=user.get("name", aadhaar), user_aadhaar=aadhaar)


# ===== API ENDPOINTS =====

@app.route("/api/notarize", methods=["POST"])
def api_notarize():
    """
    Compute hash of uploaded document and verify signature.
    Frontend will use MetaMask to submit transaction.
    """
    try:
        if not session.get("is_authenticated"):
            return jsonify({"error": "Authentication required"}), 401
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        document_type = request.form.get('document_type', 'other')
        skip_verification = request.form.get('skip_verification', 'false') == 'true'
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if document_type not in DOCUMENT_TYPES:
            return jsonify({"error": "Invalid document type"}), 400
        
        # Read file content for verification
        file_content = file.read()
        file.seek(0)  # Reset for hash computation
        
        # Get user's Aadhaar from session
        aadhaar = session.get("user_aadhaar")
        
        # Verify document signature (unless skipped for unsigned docs)
        if not skip_verification:
            verification_result = document_signer.verify_signature(
                file_content=file_content,
                expected_aadhaar=aadhaar,
                expected_doc_type=document_type
            )
            
            if not verification_result["valid"]:
                return jsonify({
                    "error": verification_result["error"],
                    "verification_failed": True,
                    "owner_match": verification_result.get("owner_match", False),
                    "type_match": verification_result.get("type_match", False)
                }), 400
        
        # Compute SHA-256 hash
        doc_hash = compute_sha256(file)
        
        return jsonify({
            "success": True,
            "hash": doc_hash,
            "filename": secure_filename(file.filename),
            "document_type": document_type,
            "document_type_label": DOCUMENT_TYPES.get(document_type),
            "verified": not skip_verification
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/notarize/confirm", methods=["POST"])
def api_notarize_confirm():
    """
    Confirm notarization after blockchain transaction is complete.
    Stores document metadata in backend.
    """
    try:
        if not session.get("is_authenticated"):
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json()
        doc_hash = data.get("hash")
        document_type = data.get("document_type")
        filename = data.get("filename")
        tx_hash = data.get("tx_hash")
        
        if not doc_hash or not document_type:
            return jsonify({"error": "Missing required fields"}), 400
        
        aadhaar = session.get("user_aadhaar")
        
        # Store document metadata
        store_document_info(doc_hash, aadhaar, document_type, filename)
        
        return jsonify({
            "success": True,
            "message": "Document metadata stored successfully"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/verify", methods=["POST"])
def api_verify():
    """
    Verify if document hash exists on blockchain.
    """
    try:
        if not session.get("is_authenticated"):
            return jsonify({"error": "Authentication required"}), 401
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Compute SHA-256 hash
        doc_hash = compute_sha256(file)
        
        # Verify on blockchain
        timestamp = blockchain.verify_hash(doc_hash)
        
        if isinstance(timestamp, dict) and "error" in timestamp:
            return jsonify(timestamp), 500
        
        # Check if document was notarized
        if timestamp > 0:
            # Convert timestamp to readable format
            notarized_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            
            # Get document metadata
            doc_info = get_document_info(doc_hash)
            
            response_data = {
                "success": True,
                "notarized": True,
                "hash": doc_hash,
                "timestamp": timestamp,
                "date": notarized_date,
                "message": "Document is authentic and was notarized on blockchain"
            }
            
            # Add owner info if metadata exists
            if doc_info:
                owner_aadhaar = doc_info.get("owner_aadhaar", "")
                response_data["document_type"] = doc_info.get("document_type_label", "Unknown")
                response_data["owner_name"] = doc_info.get("owner_name", "Unknown")
                response_data["owner_aadhaar_last4"] = owner_aadhaar[-4:] if len(owner_aadhaar) >= 4 else "****"
            else:
                # Document notarized before metadata feature was added
                response_data["document_type"] = "Unknown (Legacy)"
                response_data["owner_name"] = "Unknown"
                response_data["owner_aadhaar_last4"] = "****"
            
            return jsonify(response_data)
        else:
            return jsonify({
                "success": True,
                "notarized": False,
                "hash": doc_hash,
                "message": "Document not found on blockchain"
            })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/contract-info", methods=["GET"])
def api_contract_info():
    """
    Get contract address and network info for MetaMask interaction.
    """
    try:
        return jsonify({
            "contractAddress": Config.CONTRACT_ADDRESS,
            "rpcUrl": Config.RPC_URL
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===== ERROR HANDLERS =====

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({"error": "File too large. Maximum size is 16MB"}), 413


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template("index.html"), 404


# ===== RUN APPLICATION =====

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 Blockchain Document Notarization System")
    print("="*50)
    print(f"📝 Contract Address: {Config.CONTRACT_ADDRESS or 'Not configured'}")
    print(f"🌐 RPC URL: {Config.RPC_URL or 'Not configured'}")
    print("="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
