import hashlib
import os
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP code."""
    return "".join(random.choices(string.digits, k=length))


def send_otp_email(email: str, otp: str) -> bool:
    """Send OTP to user's email using SMTP.
    
    Args:
        email: Recipient email address
        otp: The OTP code to send
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    # Email configuration from environment variables
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    sender_email = os.getenv("SENDER_EMAIL", smtp_user)
    
    if not smtp_user or not smtp_password:
        print(f"[OTP] SMTP not configured. OTP for {email}: {otp}")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = email
        msg["Subject"] = "Your OTP for Blockchain Notary Login"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #6366f1;">🔐 Blockchain Document Notarization</h2>
            <p>Your One-Time Password (OTP) for login is:</p>
            <h1 style="color: #10b981; font-size: 36px; letter-spacing: 5px; background: #1e293b; padding: 20px; border-radius: 8px; display: inline-block;">{otp}</h1>
            <p style="color: #666;">This OTP is valid for a single use. Do not share it with anyone.</p>
            <hr style="border: 1px solid #334155;">
            <p style="color: #888; font-size: 12px;">If you did not request this OTP, please ignore this email.</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, "html"))
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        print(f"[OTP] Email sent successfully to {email}")
        return True
        
    except Exception as e:
        print(f"[OTP] Failed to send email to {email}: {str(e)}")
        print(f"[OTP] Fallback - OTP for {email}: {otp}")
        return False

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
