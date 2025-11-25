from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from config import Config
from contract import blockchain
from utils import compute_sha256, generate_otp, send_otp_email

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
    return render_template("notarize.html", user_name=user.get("name", aadhaar), user_aadhaar=aadhaar)


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
    Compute hash of uploaded document.
    Frontend will use MetaMask to submit transaction.
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
        
        return jsonify({
            "success": True,
            "hash": doc_hash,
            "filename": secure_filename(file.filename)
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
            
            return jsonify({
                "success": True,
                "notarized": True,
                "hash": doc_hash,
                "timestamp": timestamp,
                "date": notarized_date,
                "message": "Document is authentic and was notarized on blockchain"
            })
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
