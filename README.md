# 🔐 Blockchain Document Notarization System

A decentralized application (DApp) for notarizing and verifying documents using blockchain technology.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![Solidity](https://img.shields.io/badge/Solidity-0.8.19-orange)
![Web3.js](https://img.shields.io/badge/Web3.js-1.10-yellow)

## 🌟 Features

- ✅ **Document Notarization**: Store cryptographic proof of document existence on blockchain
- ✅ **Document Verification**: Verify document authenticity anytime
- ✅ **Immutable Records**: Blockchain ensures data cannot be tampered with
- ✅ **Timestamped Proof**: Exact time of notarization is recorded
- ✅ **MetaMask Integration**: Secure wallet connection for transactions
- ✅ **Multi-Network Support**: Works on Ethereum, Polygon, and testnets

## 🏗️ Architecture

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Frontend   │───────▶│   Backend    │───────▶│  Blockchain  │
│  (HTML/JS)   │         │   (Flask)    │         │  (Solidity)  │
└──────────────┘         └──────────────┘         └──────────────┘
     │                         │                         │
     │                         │                         │
  MetaMask               Web3.py/RPC            Smart Contract
```

## 📋 Prerequisites

- Python 3.9+
- Node.js 16+
- MetaMask browser extension
- Alchemy/Infura account (for RPC endpoint)

## 🚀 Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/notary-dapp.git
cd notary-dapp
```

### 2. Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment

Create `backend/.env`:

```env
RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY
PRIVATE_KEY=your_metamask_private_key
CONTRACT_ADDRESS=  # Leave empty, will be filled after deployment
SECRET_KEY=your-random-secret-key
```

### 4. Smart Contract Setup

```bash
cd blockchain
npm install
npx hardhat compile
```

### 5. Deploy Contract

```bash
# Deploy to Sepolia testnet
npx hardhat run scripts/deploy.js --network sepolia

# Or deploy locally for testing
npx hardhat node  # In one terminal
npx hardhat run scripts/deploy.js --network localhost  # In another
```

The deployment script automatically saves the contract address to `backend/.env`.

### 6. Run Application

```bash
cd backend
source venv/bin/activate
python app.py
```

Visit: `http://localhost:5000`

## 📖 Usage

### Notarize a Document

1. Click "Notarize Document"
2. Upload your file
3. System computes SHA-256 hash
4. Click "Confirm & Send to Blockchain"
5. MetaMask opens - confirm transaction
6. Document hash is stored permanently

### Verify a Document

1. Click "Verify Document"
2. Upload the same file OR enter hash manually
3. System checks blockchain
4. Shows notarization details if found

## 🧪 Testing

Run smart contract tests:

```bash
cd blockchain
npx hardhat test
```

## 🛠️ Technology Stack

- **Backend**: Python, Flask, Web3.py
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Blockchain**: Solidity, Hardhat, Ethers.js
- **Wallet**: MetaMask
- **Networks**: Ethereum Sepolia, Polygon Mumbai

## 📁 Project Structure

```
notary-dapp/
├── backend/
│   ├── app.py              # Flask application
│   ├── contract.py         # Blockchain interface
│   ├── config.py           # Configuration
│   └── utils.py            # Helper functions
├── frontend/
│   ├── templates/          # HTML templates
│   └── static/
│       ├── css/            # Stylesheets
│       └── js/             # JavaScript
├── blockchain/
│   ├── contracts/          # Solidity contracts
│   ├── scripts/            # Deployment scripts
│   └── test/               # Contract tests
└── docs/                   # Documentation
```

## 🔒 Security

- Document files never leave your device
- Only cryptographic hashes are stored on blockchain
- Private keys stored in `.env` (never committed)
- MetaMask handles transaction signing

## 📄 License

MIT License

## 👥 Contributors

- Jaideep Singh - [GitHub](https://github.com/JaideepSingh2)
- Akshit Baliyan - [GitHub](https://github.com/AkshitBaliyan)

## 🙏 Acknowledgments

- OpenZeppelin for smart contract libraries
- MetaMask for wallet integration
- Alchemy for RPC infrastructure
