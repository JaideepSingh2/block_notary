#!/usr/bin/env python3
"""
Document Signing Tool for Blockchain Notary System
===================================================

This is a STANDALONE tool for signing documents before notarization.
Run this tool separately to prepare documents, then use the signed
documents in the main notarization application.

Usage:
------
    # Interactive mode (recommended)
    python sign_document.py
    
    # Command-line mode
    python sign_document.py sign --file certificate.pdf --aadhaar 123412341234 --type birth_certificate
    
    # Verify a signed document
    python sign_document.py verify --file certificate_signed.pdf --aadhaar 123412341234 --type birth_certificate
    
    # Just generate signature string (for manual embedding)
    python sign_document.py generate --aadhaar 123412341234 --type degree_certificate

Document Types:
---------------
    - birth_certificate     : Birth Certificate
    - degree_certificate    : Degree/Education Certificate
    - property_deed         : Property Deed
    - employment_letter     : Employment Letter
    - legal_contract        : Legal Contract/Agreement
    - identity_document     : Identity Document
    - other                 : Other Document

How It Works:
-------------
1. The tool embeds a cryptographic signature into your document
2. The signature contains:
   - Hash of your Aadhaar (for privacy, actual number is never stored)
   - Document type
   - Timestamp when signed
   - Issuing authority name
   - HMAC signature for tamper detection
3. When you notarize, the main app verifies this signature
4. Only documents signed by YOU with the correct type can be notarized

Author: Blockchain Notary System
"""

import os
import sys
import json
import hmac
import hashlib
import base64
import re
import argparse
from datetime import datetime
from typing import Optional, Dict, Any
from io import BytesIO

# Add parent directory to path to import from backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))
except ImportError:
    pass

# Try to import PDF libraries
try:
    from PyPDF2 import PdfReader, PdfWriter
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


# Document types available
DOCUMENT_TYPES = {
    "birth_certificate": "Birth Certificate",
    "degree_certificate": "Degree/Education Certificate", 
    "property_deed": "Property Deed",
    "employment_letter": "Employment Letter",
    "legal_contract": "Legal Contract/Agreement",
    "identity_document": "Identity Document",
    "other": "Other Document"
}


class DocumentSigner:
    """
    Handles document signing and verification for the notarization system.
    """
    
    # Signature markers
    SIG_START = "NOTARY_SIG_START:"
    SIG_END = ":NOTARY_SIG_END"
    SIG_PATTERN = r"NOTARY_SIG_START:([A-Za-z0-9+/=]+):NOTARY_SIG_END"
    
    def __init__(self, secret_key: Optional[str] = None):
        """Initialize the document signer."""
        # Match the backend's key loading order: DOCUMENT_SIGNING_KEY first, then SECRET_KEY
        self.secret_key = secret_key or os.getenv("DOCUMENT_SIGNING_KEY", "")
        
        if not self.secret_key:
            self.secret_key = os.getenv("SECRET_KEY", "default-signing-key-change-me")
        
        self.secret_key = self.secret_key.encode('utf-8')
    
    def _hash_aadhaar(self, aadhaar: str) -> str:
        """Create a SHA256 hash of Aadhaar number for privacy."""
        return hashlib.sha256(aadhaar.encode('utf-8')).hexdigest()
    
    def _create_hmac(self, data: dict) -> str:
        """Create HMAC signature for the payload data."""
        payload_str = json.dumps({
            "aadhaar_hash": data["aadhaar_hash"],
            "document_type": data["document_type"],
            "issued_at": data["issued_at"],
            "issuer": data["issuer"]
        }, sort_keys=True)
        
        signature = hmac.new(
            self.secret_key,
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _verify_hmac(self, data: dict, provided_hmac: str) -> bool:
        """Verify HMAC signature."""
        expected_hmac = self._create_hmac(data)
        return hmac.compare_digest(expected_hmac, provided_hmac)
    
    def create_signature_payload(
        self,
        aadhaar: str,
        document_type: str,
        issuer: str = "Blockchain Notary Authority"
    ) -> str:
        """Create a signature payload for embedding in documents."""
        data = {
            "aadhaar_hash": self._hash_aadhaar(aadhaar),
            "document_type": document_type,
            "issued_at": datetime.now().isoformat(),
            "issuer": issuer
        }
        
        # Add HMAC signature
        data["hmac"] = self._create_hmac(data)
        
        # Encode as base64
        payload_json = json.dumps(data)
        payload_b64 = base64.b64encode(payload_json.encode('utf-8')).decode('utf-8')
        
        return f"{self.SIG_START}{payload_b64}{self.SIG_END}"
    
    def extract_signature(self, file_content: bytes) -> Optional[dict]:
        """Extract signature payload from file content."""
        try:
            try:
                text_content = file_content.decode('utf-8', errors='ignore')
            except:
                text_content = file_content.decode('latin-1', errors='ignore')
            
            match = re.search(self.SIG_PATTERN, text_content)
            
            if not match:
                raw_match = re.search(self.SIG_PATTERN.encode(), file_content)
                if raw_match:
                    payload_b64 = raw_match.group(1).decode('utf-8')
                else:
                    return None
            else:
                payload_b64 = match.group(1)
            
            payload_json = base64.b64decode(payload_b64).decode('utf-8')
            return json.loads(payload_json)
            
        except Exception as e:
            print(f"Error extracting signature: {e}")
            return None
    
    def verify_signature(
        self,
        file_content: bytes,
        expected_aadhaar: str,
        expected_doc_type: str
    ) -> Dict[str, Any]:
        """Verify that a document's signature matches expected owner and type."""
        result = {
            "valid": False,
            "error": None,
            "signature_data": None,
            "owner_match": False,
            "type_match": False
        }
        
        sig_data = self.extract_signature(file_content)
        
        if not sig_data:
            result["error"] = "No valid signature found in document."
            return result
        
        result["signature_data"] = sig_data
        
        provided_hmac = sig_data.get("hmac", "")
        if not self._verify_hmac(sig_data, provided_hmac):
            result["error"] = "Document signature is invalid or has been tampered with."
            return result
        
        expected_hash = self._hash_aadhaar(expected_aadhaar)
        if sig_data.get("aadhaar_hash") == expected_hash:
            result["owner_match"] = True
        else:
            result["error"] = "This document does not belong to you."
            return result
        
        if sig_data.get("document_type") == expected_doc_type:
            result["type_match"] = True
        else:
            actual_type = sig_data.get("document_type", "unknown")
            result["error"] = f"Document type mismatch. Document is '{actual_type}', but you specified '{expected_doc_type}'."
            return result
        
        result["valid"] = True
        return result
    
    def sign_text_file(self, content: bytes, signature: str) -> bytes:
        """Sign a text file by appending signature."""
        signed_content = content + b"\n\n" + signature.encode('utf-8') + b"\n"
        return signed_content
    
    def sign_pdf_file(self, content: bytes, signature: str) -> bytes:
        """Sign a PDF file by adding signature to metadata/content."""
        if not PDF_SUPPORT:
            sig_comment = f"\n% {signature}\n".encode('utf-8')
            return content + sig_comment
        
        try:
            reader = PdfReader(BytesIO(content))
            writer = PdfWriter()
            
            for page in reader.pages:
                writer.add_page(page)
            
            metadata = reader.metadata or {}
            writer.add_metadata({
                **metadata,
                "/NotarySignature": signature,
                "/SignedAt": datetime.now().isoformat()
            })
            
            output = BytesIO()
            writer.write(output)
            signed = output.getvalue()
            # Always append a visible comment with the signature marker so
            # simple text scanning can reliably extract it.
            sig_comment = f"\n% {signature}\n".encode('utf-8')
            return signed + sig_comment
            
        except Exception as e:
            print(f"PDF signing error: {e}, using fallback method")
            sig_comment = f"\n% {signature}\n".encode('utf-8')
            return content + sig_comment
    
    def sign_document(
        self,
        file_content: bytes,
        filename: str,
        aadhaar: str,
        document_type: str,
        issuer: str = "Blockchain Notary Authority"
    ) -> bytes:
        """Sign a document by embedding cryptographic signature."""
        signature = self.create_signature_payload(aadhaar, document_type, issuer)
        
        ext = os.path.splitext(filename)[1].lower()
        
        if ext == '.pdf':
            return self.sign_pdf_file(file_content, signature)
        else:
            return self.sign_text_file(file_content, signature)


def interactive_mode():
    """Run the tool in interactive mode."""
    print("\n" + "=" * 60)
    print("🔏 Document Signing Tool for Blockchain Notary")
    print("=" * 60)
    print("\nThis tool prepares documents for notarization by embedding")
    print("a cryptographic signature that proves ownership and document type.\n")
    
    signer = DocumentSigner()
    
    while True:
        print("\nWhat would you like to do?")
        print("  1. Sign a document")
        print("  2. Verify a signed document")
        print("  3. Generate signature string only")
        print("  4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            # Sign document
            print("\n--- Sign Document ---\n")
            
            file_path = input("Enter file path: ").strip()
            if not os.path.exists(file_path):
                print(f"❌ Error: File not found: {file_path}")
                continue
            
            aadhaar = input("Enter Aadhaar number (12 digits): ").strip()
            if len(aadhaar) != 12 or not aadhaar.isdigit():
                print("❌ Error: Aadhaar must be exactly 12 digits")
                continue
            
            print("\nAvailable document types:")
            for i, (key, label) in enumerate(DOCUMENT_TYPES.items(), 1):
                print(f"  {i}. {label} ({key})")
            
            type_choice = input("\nEnter document type number or key: ").strip()
            
            if type_choice.isdigit():
                type_idx = int(type_choice) - 1
                if 0 <= type_idx < len(DOCUMENT_TYPES):
                    document_type = list(DOCUMENT_TYPES.keys())[type_idx]
                else:
                    print("❌ Error: Invalid selection")
                    continue
            elif type_choice in DOCUMENT_TYPES:
                document_type = type_choice
            else:
                print("❌ Error: Invalid document type")
                continue
            
            issuer = input("Enter issuing authority (press Enter for default): ").strip()
            if not issuer:
                issuer = "Blockchain Notary Authority"
            
            # Read and sign
            with open(file_path, 'rb') as f:
                content = f.read()
            
            signed_content = signer.sign_document(
                file_content=content,
                filename=file_path,
                aadhaar=aadhaar,
                document_type=document_type,
                issuer=issuer
            )
            
            # Output path
            base, ext = os.path.splitext(file_path)
            output_path = f"{base}_signed{ext}"
            
            with open(output_path, 'wb') as f:
                f.write(signed_content)
            
            print(f"\n✅ Document signed successfully!")
            print(f"   Output: {output_path}")
            print(f"   Owner Aadhaar: ****{aadhaar[-4:]}")
            print(f"   Document Type: {DOCUMENT_TYPES[document_type]}")
            print(f"   Issuer: {issuer}")
            print(f"\n📋 Use this signed document in the notarization app.")
        
        elif choice == "2":
            # Verify document
            print("\n--- Verify Signed Document ---\n")
            
            file_path = input("Enter file path: ").strip()
            if not os.path.exists(file_path):
                print(f"❌ Error: File not found: {file_path}")
                continue
            
            aadhaar = input("Enter expected owner's Aadhaar: ").strip()
            
            print("\nAvailable document types:")
            for i, (key, label) in enumerate(DOCUMENT_TYPES.items(), 1):
                print(f"  {i}. {label} ({key})")
            
            type_choice = input("\nEnter expected document type number or key: ").strip()
            
            if type_choice.isdigit():
                type_idx = int(type_choice) - 1
                if 0 <= type_idx < len(DOCUMENT_TYPES):
                    document_type = list(DOCUMENT_TYPES.keys())[type_idx]
                else:
                    print("❌ Error: Invalid selection")
                    continue
            elif type_choice in DOCUMENT_TYPES:
                document_type = type_choice
            else:
                print("❌ Error: Invalid document type")
                continue
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            result = signer.verify_signature(content, aadhaar, document_type)
            
            print()
            if result["valid"]:
                print("✅ Document verification PASSED!")
                print(f"   Owner Match: ✓")
                print(f"   Type Match: ✓")
                if result["signature_data"]:
                    print(f"   Issued At: {result['signature_data'].get('issued_at', 'Unknown')}")
                    print(f"   Issuer: {result['signature_data'].get('issuer', 'Unknown')}")
            else:
                print("❌ Document verification FAILED!")
                print(f"   Error: {result['error']}")
        
        elif choice == "3":
            # Generate signature only
            print("\n--- Generate Signature String ---\n")
            
            aadhaar = input("Enter Aadhaar number: ").strip()
            
            print("\nAvailable document types:")
            for i, (key, label) in enumerate(DOCUMENT_TYPES.items(), 1):
                print(f"  {i}. {label} ({key})")
            
            type_choice = input("\nEnter document type number or key: ").strip()
            
            if type_choice.isdigit():
                type_idx = int(type_choice) - 1
                if 0 <= type_idx < len(DOCUMENT_TYPES):
                    document_type = list(DOCUMENT_TYPES.keys())[type_idx]
                else:
                    print("❌ Error: Invalid selection")
                    continue
            elif type_choice in DOCUMENT_TYPES:
                document_type = type_choice
            else:
                print("❌ Error: Invalid document type")
                continue
            
            issuer = input("Enter issuing authority (press Enter for default): ").strip()
            if not issuer:
                issuer = "Blockchain Notary Authority"
            
            signature = signer.create_signature_payload(aadhaar, document_type, issuer)
            
            print("\n" + "-" * 60)
            print("Generated Signature:")
            print("-" * 60)
            print(signature)
            print("-" * 60)
            print("\nYou can manually add this signature to your document.")
        
        elif choice == "4":
            print("\nGoodbye! 👋\n")
            break
        
        else:
            print("Invalid choice. Please enter 1-4.")


def cli_mode():
    """Run the tool in command-line mode."""
    parser = argparse.ArgumentParser(
        description="Sign documents for Blockchain Notary System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Sign a document:
    python sign_document.py sign --file certificate.pdf --aadhaar 123412341234 --type birth_certificate
  
  Verify a document:
    python sign_document.py verify --file certificate.pdf --aadhaar 123412341234 --type birth_certificate
  
  Generate signature only:
    python sign_document.py generate --aadhaar 123412341234 --type degree_certificate
  
  Interactive mode:
    python sign_document.py
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Sign command
    sign_parser = subparsers.add_parser("sign", help="Sign a document")
    sign_parser.add_argument("--file", "-f", required=True, help="Path to document file")
    sign_parser.add_argument("--aadhaar", "-a", required=True, help="Owner's Aadhaar number")
    sign_parser.add_argument("--type", "-t", required=True, help="Document type",
                            choices=list(DOCUMENT_TYPES.keys()))
    sign_parser.add_argument("--issuer", "-i", default="Blockchain Notary Authority", help="Issuing authority")
    sign_parser.add_argument("--output", "-o", help="Output file path (default: adds _signed suffix)")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a document signature")
    verify_parser.add_argument("--file", "-f", required=True, help="Path to signed document")
    verify_parser.add_argument("--aadhaar", "-a", required=True, help="Expected owner's Aadhaar")
    verify_parser.add_argument("--type", "-t", required=True, help="Expected document type",
                              choices=list(DOCUMENT_TYPES.keys()))
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate a signature string")
    gen_parser.add_argument("--aadhaar", "-a", required=True, help="Owner's Aadhaar number")
    gen_parser.add_argument("--type", "-t", required=True, help="Document type",
                           choices=list(DOCUMENT_TYPES.keys()))
    gen_parser.add_argument("--issuer", "-i", default="Blockchain Notary Authority", help="Issuing authority")
    
    args = parser.parse_args()
    
    if not args.command:
        # No command specified, run interactive mode
        interactive_mode()
        return
    
    signer = DocumentSigner()
    
    if args.command == "sign":
        if not os.path.exists(args.file):
            print(f"❌ Error: File not found: {args.file}")
            sys.exit(1)
        
        with open(args.file, 'rb') as f:
            content = f.read()
        
        signed_content = signer.sign_document(
            file_content=content,
            filename=args.file,
            aadhaar=args.aadhaar,
            document_type=args.type,
            issuer=args.issuer
        )
        
        if args.output:
            output_path = args.output
        else:
            base, ext = os.path.splitext(args.file)
            output_path = f"{base}_signed{ext}"
        
        with open(output_path, 'wb') as f:
            f.write(signed_content)
        
        print(f"✅ Document signed successfully!")
        print(f"   Output: {output_path}")
        print(f"   Owner Aadhaar: ****{args.aadhaar[-4:]}")
        print(f"   Document Type: {DOCUMENT_TYPES[args.type]}")
        print(f"   Issuer: {args.issuer}")
    
    elif args.command == "verify":
        if not os.path.exists(args.file):
            print(f"❌ Error: File not found: {args.file}")
            sys.exit(1)
        
        with open(args.file, 'rb') as f:
            content = f.read()
        
        result = signer.verify_signature(content, args.aadhaar, args.type)
        
        if result["valid"]:
            print("✅ Document verification PASSED!")
            print(f"   Owner Match: ✓")
            print(f"   Type Match: ✓")
            if result["signature_data"]:
                print(f"   Issued At: {result['signature_data'].get('issued_at', 'Unknown')}")
                print(f"   Issuer: {result['signature_data'].get('issuer', 'Unknown')}")
        else:
            print("❌ Document verification FAILED!")
            print(f"   Error: {result['error']}")
            sys.exit(1)
    
    elif args.command == "generate":
        signature = signer.create_signature_payload(
            aadhaar=args.aadhaar,
            document_type=args.type,
            issuer=args.issuer
        )
        
        print("Generated Signature:")
        print("-" * 60)
        print(signature)
        print("-" * 60)


if __name__ == "__main__":
    cli_mode()
