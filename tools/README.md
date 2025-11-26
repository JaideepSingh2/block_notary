# Document Signing Tool

This standalone tool prepares documents for notarization in the Blockchain Notary system.

## Overview

Before a document can be notarized on the blockchain, it must be **digitally signed** to prove:

1. **Ownership** - The document belongs to you (verified via Aadhaar)
2. **Document Type** - The document is what it claims to be

This tool embeds a cryptographic signature into your documents that the main notarization app will verify.

## Requirements

- Python 3.8+
- PyPDF2 (optional, for better PDF support)

```bash
pip install PyPDF2 python-dotenv
```

## Usage

### Interactive Mode (Recommended)

```bash
cd tools
python sign_document.py
```

This opens an interactive menu where you can:

1. Sign documents
2. Verify signed documents
3. Generate signature strings

### Command-Line Mode

**Sign a document:**

```bash
python sign_document.py sign --file certificate.pdf --aadhaar 123412341234 --type birth_certificate
```

**Verify a signed document:**

```bash
python sign_document.py verify --file certificate_signed.pdf --aadhaar 123412341234 --type birth_certificate
```

**Generate signature string only:**

```bash
python sign_document.py generate --aadhaar 123412341234 --type degree_certificate
```

## Document Types

| Key                  | Description                  |
| -------------------- | ---------------------------- |
| `birth_certificate`  | Birth Certificate            |
| `degree_certificate` | Degree/Education Certificate |
| `property_deed`      | Property Deed                |
| `employment_letter`  | Employment Letter            |
| `legal_contract`     | Legal Contract/Agreement     |
| `identity_document`  | Identity Document            |
| `other`              | Other Document               |

## How It Works

1. **Signature Creation**: The tool creates a payload containing:

   - SHA256 hash of your Aadhaar (for privacy)
   - Document type
   - Timestamp
   - Issuing authority
   - HMAC signature (tamper-proof)

2. **Signature Embedding**: The payload is embedded in the document:

   - **PDF files**: Added to PDF metadata
   - **Text files**: Appended to the end of the file
   - **Other files**: Appended as text

3. **Verification**: When you notarize, the main app:
   - Extracts the signature
   - Verifies HMAC integrity
   - Checks Aadhaar hash matches logged-in user
   - Confirms document type matches selection

## Example Workflow

```bash
# 1. Sign your document
python sign_document.py sign \
  --file my_degree.pdf \
  --aadhaar 123412341234 \
  --type degree_certificate \
  --issuer "ABC University"

# Output: my_degree_signed.pdf

# 2. Verify it's signed correctly
python sign_document.py verify \
  --file my_degree_signed.pdf \
  --aadhaar 123412341234 \
  --type degree_certificate

# 3. Use my_degree_signed.pdf in the notarization app
```

## Security Notes

- Your **Aadhaar number is never stored** - only a SHA256 hash
- The **HMAC signature** prevents tampering with the embedded data
- The signing key is derived from the same `SECRET_KEY` used by the main app
- Anyone modifying the document after signing will invalidate the signature

## Troubleshooting

**"No valid signature found"**

- Make sure you're using the signed version of the document (usually `*_signed.pdf`)
- Check that the file wasn't modified after signing

**"Document does not belong to you"**

- You're trying to notarize a document signed with a different Aadhaar
- Re-sign the document with your own Aadhaar

**"Document type mismatch"**

- Select the same document type you used when signing
- Or re-sign the document with the correct type

## File Support

| Format   | Support Level              |
| -------- | -------------------------- |
| PDF      | Full (with PyPDF2)         |
| TXT      | Full                       |
| DOC/DOCX | Basic (signature appended) |
| Other    | Basic (signature appended) |

For best results with PDFs, install PyPDF2:

```bash
pip install PyPDF2
```
