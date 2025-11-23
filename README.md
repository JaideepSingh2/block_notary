# 🔐 Blockchain Document Notarization System

A decentralized application (DApp) for notarizing and verifying documents using blockchain technology. Built with **Python Flask**, **Web3.py**, **Solidity**, and **MetaMask**.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![Solidity](https://img.shields.io/badge/Solidity-0.8.19-orange.svg)
![Web3](https://img.shields.io/badge/Web3.py-6.11-purple.svg)

---

## 🌟 Features

- **📝 Document Notarization**: Upload any file and create a tamper-proof timestamp on blockchain
- **✅ Document Verification**: Verify authenticity and timestamp of previously notarized documents
- **🔒 Immutable Records**: Blockchain ensures records cannot be altered or deleted
- **🌐 Decentralized**: No central authority controls the data
- **🔐 Secure**: Uses SHA-256 hashing and blockchain cryptography
- **💼 MetaMask Integration**: Easy wallet connection for transaction signing

---

## 🏗️ Architecture

```
User Interface (HTML/CSS/JS)
        ↓
Flask Backend (Python)
        ↓
Web3.py ←→ Smart Contract (Solidity)
        ↓
Ethereum Blockchain (Sepolia/Mumbai)
```

### How It Works

1. **Notarization**:

   - User uploads document → System computes SHA-256 hash
   - MetaMask signs transaction → Hash stored on blockchain
   - Timestamp recorded permanently

2. **Verification**:
   - User uploads document → System computes hash
   - Blockchain queried for hash → Returns timestamp if found
   - Instant verification without wallet needed

---

## 📂 Project Structure

```
block_notary/
├── backend/                    # Flask application
│   ├── app.py                 # Main Flask routes
│   ├── config.py              # Configuration
│   ├── contract.py            # Blockchain interaction
│   ├── utils.py               # Helper functions
│   ├── requirements.txt       # Python dependencies
│   └── .env.example          # Environment variables template
│
├── frontend/                  # User interface
│   ├── templates/            # HTML pages
│   │   ├── index.html       # Homepage
│   │   ├── notarize.html    # Notarization page
│   │   └── verify.html      # Verification page
│   └── static/
│       ├── css/style.css    # Styling
│       └── js/
│           ├── metamask.js  # MetaMask integration
│           └── verify.js    # Verification logic
│
├── blockchain/               # Smart contracts
│   ├── contracts/
│   │   └── Notary.sol       # Main contract
│   ├── scripts/
│   │   ├── deploy.js        # Deployment script
│   │   └── interact.js      # Interaction examples
│   ├── hardhat.config.js    # Hardhat configuration
│   └── README.md            # Blockchain docs
│
├── docs/                     # Documentation
└── README.md                # This file
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Node.js 16+** and npm
- **MetaMask** browser extension
- **Git**
- Test ETH from faucet (Sepolia or Mumbai)

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/block_notary.git
cd block_notary
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your credentials:
# - RPC_URL (from Alchemy/Infura)
# - PRIVATE_KEY (from MetaMask)
# - CONTRACT_ADDRESS (after deployment)
```

### 3. Deploy Smart Contract

```bash
cd ../blockchain

# Install dependencies
npm install

# Compile contract
npm run compile

# Deploy to Sepolia testnet
npm run deploy:sepolia

# Copy the contract address from output
# Update backend/.env with CONTRACT_ADDRESS
```

### 4. Run Application

```bash
cd ../backend

# Start Flask server
python app.py

# Visit: http://localhost:5000
```

---

## 🔧 Configuration

### Get RPC URL

1. Create account on [Alchemy](https://www.alchemy.com/) or [Infura](https://infura.io/)
2. Create new app for Sepolia testnet
3. Copy HTTP URL to `.env` as `RPC_URL`

### Get Test ETH

**Sepolia Faucet:**

- https://sepoliafaucet.com/
- https://www.alchemy.com/faucets/ethereum-sepolia

**Mumbai Faucet:**

- https://faucet.polygon.technology/

### MetaMask Setup

1. Install [MetaMask](https://metamask.io/)
2. Switch to Sepolia testnet
3. Import account with test ETH

---

## 📖 Usage Guide

### Notarizing a Document

1. Visit http://localhost:5000/notarize
2. Click "Connect MetaMask"
3. Upload your document (PDF, image, text, etc.)
4. Click "Notarize Document"
5. Confirm transaction in MetaMask
6. Save the transaction hash for your records

### Verifying a Document

1. Visit http://localhost:5000/verify
2. Upload the document
3. System checks blockchain automatically
4. View notarization timestamp if found

---

## 🧪 Testing

### Test Smart Contract

```bash
cd blockchain
npm test
```

### Test Backend API

```bash
cd backend
python -m pytest
```

### Manual Testing

Use `blockchain/scripts/interact.js` to test contract functions:

```bash
cd blockchain
node scripts/interact.js
```

---

## 🛠️ Development

### File Upload Limits

Default: 16MB (configured in `backend/config.py`)

```python
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
```

### Allowed File Types

```python
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx', 'png', 'jpg', 'jpeg'}
```

### Adding New Networks

Edit `blockchain/hardhat.config.js`:

```javascript
networks: {
  yourNetwork: {
    url: "RPC_URL",
    accounts: [PRIVATE_KEY],
    chainId: CHAIN_ID
  }
}
```

---

## 🔒 Security Considerations

- ✅ **Never commit** `.env` files or private keys
- ✅ Use environment variables for sensitive data
- ✅ Only document **hashes** are stored (not actual files)
- ✅ Verify contract on Etherscan after deployment
- ✅ Test thoroughly on testnet before mainnet
- ✅ Consider rate limiting for production
- ✅ Implement proper error handling

---

## 📊 Gas Costs

Approximate gas costs on Ethereum:

| Operation   | Gas Used | Cost (at 30 Gwei) |
| ----------- | -------- | ----------------- |
| Store Hash  | ~45,000  | ~$0.05            |
| Verify Hash | Free     | View function     |

_Actual costs vary based on network congestion_

---

## 🐛 Troubleshooting

### MetaMask Not Connecting

- Ensure MetaMask is installed and unlocked
- Check you're on the correct network (Sepolia)
- Clear browser cache and reload

### Transaction Failed

- Check you have enough test ETH for gas
- Verify contract address in `.env`
- Check RPC endpoint is responding

### Backend Errors

- Verify all dependencies installed: `pip install -r requirements.txt`
- Check `.env` file exists and has correct values
- Ensure Flask is running on port 5000

### Contract Not Found

- Verify `CONTRACT_ADDRESS` in `.env` matches deployment
- Check you're connected to correct network
- Ensure contract is deployed: `npm run deploy:sepolia`

---

## 🚀 Deployment

### Deploy to Production

**Backend (Flask):**

```bash
# Use gunicorn for production
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**Smart Contract to Mainnet:**

```bash
# Deploy to Ethereum mainnet (requires real ETH)
npm run deploy:mainnet
```

**Hosting Options:**

- Backend: Heroku, AWS, DigitalOcean, Render
- Frontend: Netlify, Vercel, GitHub Pages

---

## 📚 Technologies Used

- **Backend**: Python, Flask, Web3.py
- **Blockchain**: Solidity, Hardhat, Ethers.js
- **Frontend**: HTML, CSS, JavaScript
- **Tools**: MetaMask, Alchemy/Infura
- **Network**: Ethereum (Sepolia testnet)
