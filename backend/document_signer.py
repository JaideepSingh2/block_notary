"""
Document Signing Tool for Blockchain Notary System

This module provides functionality to:
1. Sign documents by embedding a cryptographic signature
2. Verify document signatures match owner and document type

Signature Format:
-----------------
The signature is embedded as a text marker in the document:
    NOTARY_SIG_START:{base64_encoded_payload}:NOTARY_SIG_END

The payload contains:
- aadhaar_hash: SHA256 hash of Aadhaar number (for privacy)
- document_type: Type of document (e.g., birth_certificate, degree_certificate)
- issued_at: ISO timestamp when signature was created
- issuer: Name of issuing authority
- hmac: HMAC-SHA256 signature for verification

Supported Formats:
- PDF files (signature embedded in metadata/content)
- Text files (.txt) - signature appended
- Images (.png, .jpg) - signature in EXIF metadata (future)

Usage:
------
    from document_signer import DocumentSigner
    
    signer = DocumentSigner()
    
    # Sign a document
    signed_doc = signer.sign_document(
        file_path="certificate.pdf",
        aadhaar="123412341234",
        document_type="birth_certificate",
        issuer="Government Authority"
    )
    
    # Verify a document
    result = signer.verify_signature(
        file_path="certificate.pdf",
        expected_aadhaar="123412341234",
        expected_doc_type="birth_certificate"
    )
"""

import os
import json
import hmac
import hashlib
import base64
import re
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, BinaryIO
from io import BytesIO

# Try to import PDF libraries (optional, for PDF support)
try:
    from PyPDF2 import PdfReader, PdfWriter
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("[DocumentSigner] PyPDF2 not installed. PDF signing limited.")


class DocumentSigner:
    """
    Handles document signing and verification for the notarization system.
    """
    
    # Signature markers
    SIG_START = "NOTARY_SIG_START:"
    SIG_END = ":NOTARY_SIG_END"
    SIG_PATTERN = r"NOTARY_SIG_START:([A-Za-z0-9+/=]+):NOTARY_SIG_END"
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize the document signer.
        
        Args:
            secret_key: HMAC secret key. If not provided, reads from environment.
        """
        self.secret_key = secret_key or os.getenv("DOCUMENT_SIGNING_KEY", "")
        
        if not self.secret_key:
            # Generate a default key for demo (in production, always use env variable)
            self.secret_key = os.getenv("SECRET_KEY", "default-signing-key-change-me")
        
        self.secret_key = self.secret_key.encode('utf-8')
    
    def _hash_aadhaar(self, aadhaar: str) -> str:
        """Create a SHA256 hash of Aadhaar number for privacy."""
        return hashlib.sha256(aadhaar.encode('utf-8')).hexdigest()
    
    def _create_hmac(self, data: dict) -> str:
        """Create HMAC signature for the payload data."""
        # Create a deterministic string from the data (excluding hmac field)
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
        """
        Create a signature payload for embedding in documents.
        
        Args:
            aadhaar: Owner's Aadhaar number
            document_type: Type of document
            issuer: Name of issuing authority
            
        Returns:
            Base64 encoded signature string
        """
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
        """
        Extract signature payload from file content.
        
        Args:
            file_content: Raw bytes of the file
            
        Returns:
            Decoded signature dict or None if not found
        """
        try:
            # Try to decode as text first
            try:
                text_content = file_content.decode('utf-8', errors='ignore')
            except:
                text_content = file_content.decode('latin-1', errors='ignore')
            
            # Search for signature pattern
            match = re.search(self.SIG_PATTERN, text_content)
            
            if not match:
                # For PDFs, also check in raw bytes
                raw_match = re.search(self.SIG_PATTERN.encode(), file_content)
                if raw_match:
                    payload_b64 = raw_match.group(1).decode('utf-8')
                else:
                    return None
            else:
                payload_b64 = match.group(1)
            
            # Decode base64
            payload_json = base64.b64decode(payload_b64).decode('utf-8')
            return json.loads(payload_json)
            
        except Exception as e:
            print(f"[DocumentSigner] Error extracting signature: {e}")
            return None
    
    def verify_signature(
        self,
        file_content: bytes,
        expected_aadhaar: str,
        expected_doc_type: str
    ) -> Dict[str, Any]:
        """
        Verify that a document's signature matches expected owner and type.
        
        Args:
            file_content: Raw bytes of the file
            expected_aadhaar: Aadhaar of the user trying to notarize
            expected_doc_type: Document type selected by user
            
        Returns:
            Dictionary with verification result:
            {
                "valid": bool,
                "error": str (if invalid),
                "signature_data": dict (if valid),
                "owner_match": bool,
                "type_match": bool
            }
        """
        result = {
            "valid": False,
            "error": None,
            "signature_data": None,
            "owner_match": False,
            "type_match": False
        }
        
        # Extract signature
        sig_data = self.extract_signature(file_content)
        
        if not sig_data:
            result["error"] = "No valid signature found in document. Please use a properly signed document."
            return result
        
        result["signature_data"] = sig_data
        
        # Verify HMAC integrity
        provided_hmac = sig_data.get("hmac", "")
        if not self._verify_hmac(sig_data, provided_hmac):
            result["error"] = "Document signature is invalid or has been tampered with."
            return result
        
        # Check owner (Aadhaar hash match)
        expected_hash = self._hash_aadhaar(expected_aadhaar)
        if sig_data.get("aadhaar_hash") == expected_hash:
            result["owner_match"] = True
        else:
            result["error"] = "This document does not belong to you. The owner's Aadhaar does not match."
            return result
        
        # Check document type
        if sig_data.get("document_type") == expected_doc_type:
            result["type_match"] = True
        else:
            actual_type = sig_data.get("document_type", "unknown")
            result["error"] = f"Document type mismatch. Document is signed as '{actual_type}', but you selected '{expected_doc_type}'."
            return result
        
        # All checks passed
        result["valid"] = True
        return result
    
    def sign_text_file(self, content: bytes, signature: str) -> bytes:
        """
        Sign a text file by appending signature.
        
        Args:
            content: Original file content
            signature: Signature string to append
            
        Returns:
            Signed file content
        """
        # Append signature at the end with newlines
        signed_content = content + b"\n\n" + signature.encode('utf-8') + b"\n"
        return signed_content
    
    def sign_pdf_file(self, content: bytes, signature: str) -> bytes:
        """
        Sign a PDF file by adding signature to metadata/content.
        
        Args:
            content: Original PDF content
            signature: Signature string to embed
            
        Returns:
            Signed PDF content
        """
        if not PDF_SUPPORT:
            # Fallback: append as comment (may not work for all PDFs)
            # This embeds signature in a way that can be extracted
            sig_comment = f"\n% {signature}\n".encode('utf-8')
            return content + sig_comment
        
        try:
            # Use PyPDF2 to embed in metadata
            reader = PdfReader(BytesIO(content))
            writer = PdfWriter()
            
            # Copy all pages
            for page in reader.pages:
                writer.add_page(page)
            
            # Add signature to metadata
            metadata = reader.metadata or {}
            writer.add_metadata({
                **metadata,
                "/NotarySignature": signature,
                "/SignedAt": datetime.now().isoformat()
            })
            
            # Write to bytes
            output = BytesIO()
            writer.write(output)
            signed = output.getvalue()
            # Always append a visible comment with the signature marker so
            # extraction via simple text search is reliable across viewers.
            sig_comment = f"\n% {signature}\n".encode('utf-8')
            return signed + sig_comment
            
        except Exception as e:
            print(f"[DocumentSigner] PDF signing error: {e}")
            # Fallback to comment method
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
        """
        Sign a document by embedding cryptographic signature.
        
        Args:
            file_content: Original file content as bytes
            filename: Name of the file (to determine type)
            aadhaar: Owner's Aadhaar number
            document_type: Type of document
            issuer: Issuing authority name
            
        Returns:
            Signed file content as bytes
        """
        # Create signature
        signature = self.create_signature_payload(aadhaar, document_type, issuer)
        
        # Get file extension
        ext = os.path.splitext(filename)[1].lower()
        
        if ext == '.pdf':
            return self.sign_pdf_file(file_content, signature)
        elif ext in ['.txt', '.doc', '.docx', '.rtf']:
            return self.sign_text_file(file_content, signature)
        else:
            # For other files, append signature
            return self.sign_text_file(file_content, signature)


# Create global instance
document_signer = DocumentSigner()


# ===== CLI Tool for Signing Documents =====

def main():
    """Command-line interface for signing documents."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Sign documents for Blockchain Notary System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Sign a document:
    python document_signer.py sign --file certificate.pdf --aadhaar 123412341234 --type birth_certificate
  
  Verify a document:
    python document_signer.py verify --file certificate.pdf --aadhaar 123412341234 --type birth_certificate
  
  Generate signature only:
    python document_signer.py generate --aadhaar 123412341234 --type degree_certificate
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Sign command
    sign_parser = subparsers.add_parser("sign", help="Sign a document")
    sign_parser.add_argument("--file", "-f", required=True, help="Path to document file")
    sign_parser.add_argument("--aadhaar", "-a", required=True, help="Owner's Aadhaar number")
    sign_parser.add_argument("--type", "-t", required=True, help="Document type",
                            choices=["birth_certificate", "degree_certificate", "property_deed",
                                    "employment_letter", "legal_contract", "identity_document", "other"])
    sign_parser.add_argument("--issuer", "-i", default="Blockchain Notary Authority", help="Issuing authority")
    sign_parser.add_argument("--output", "-o", help="Output file path (default: adds _signed suffix)")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a document signature")
    verify_parser.add_argument("--file", "-f", required=True, help="Path to signed document")
    verify_parser.add_argument("--aadhaar", "-a", required=True, help="Expected owner's Aadhaar")
    verify_parser.add_argument("--type", "-t", required=True, help="Expected document type")
    
    # Generate command (just outputs signature string)
    gen_parser = subparsers.add_parser("generate", help="Generate a signature string")
    gen_parser.add_argument("--aadhaar", "-a", required=True, help="Owner's Aadhaar number")
    gen_parser.add_argument("--type", "-t", required=True, help="Document type")
    gen_parser.add_argument("--issuer", "-i", default="Blockchain Notary Authority", help="Issuing authority")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    signer = DocumentSigner()
    
    if args.command == "sign":
        # Read input file
        with open(args.file, 'rb') as f:
            content = f.read()
        
        # Sign document
        signed_content = signer.sign_document(
            file_content=content,
            filename=args.file,
            aadhaar=args.aadhaar,
            document_type=args.type,
            issuer=args.issuer
        )
        
        # Determine output path
        if args.output:
            output_path = args.output
        else:
            base, ext = os.path.splitext(args.file)
            output_path = f"{base}_signed{ext}"
        
        # Write signed file
        with open(output_path, 'wb') as f:
            f.write(signed_content)
        
        print(f"✅ Document signed successfully!")
        print(f"   Output: {output_path}")
        print(f"   Owner Aadhaar: ****{args.aadhaar[-4:]}")
        print(f"   Document Type: {args.type}")
        print(f"   Issuer: {args.issuer}")
    
    elif args.command == "verify":
        # Read file
        with open(args.file, 'rb') as f:
            content = f.read()
        
        # Verify
        result = signer.verify_signature(
            file_content=content,
            expected_aadhaar=args.aadhaar,
            expected_doc_type=args.type
        )
        
        if result["valid"]:
            print("✅ Document verification PASSED!")
            print(f"   Owner Match: ✓")
            print(f"   Type Match: ✓")
            print(f"   Issued At: {result['signature_data'].get('issued_at', 'Unknown')}")
            print(f"   Issuer: {result['signature_data'].get('issuer', 'Unknown')}")
        else:
            print("❌ Document verification FAILED!")
            print(f"   Error: {result['error']}")
    
    elif args.command == "generate":
        # Just generate and print signature
        signature = signer.create_signature_payload(
            aadhaar=args.aadhaar,
            document_type=args.type,
            issuer=args.issuer
        )
        
        print("Generated Signature:")
        print("-" * 60)
        print(signature)
        print("-" * 60)
        print("\nYou can manually add this signature to your document.")


if __name__ == "__main__":
    main()
