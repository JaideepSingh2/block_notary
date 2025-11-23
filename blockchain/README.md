# Blockchain Smart Contracts

This directory contains the Solidity smart contracts for the document notarization system.

## 📁 Structure

- `contracts/` - Solidity smart contracts
- `scripts/` - Deployment and interaction scripts
- `test/` - Contract tests (optional)
- `artifacts/` - Compiled contract artifacts (generated)
- `cache/` - Hardhat cache (generated)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd blockchain
npm install
```

### 2. Compile Contracts

```bash
npm run compile
```

### 3. Deploy to Testnet

**Sepolia:**
```bash
npm run deploy:sepolia
```

**Mumbai:**
```bash
npm run deploy:mumbai
```

**Local Network:**
```bash
# Terminal 1: Start local node
npm run node

# Terminal 2: Deploy
npm run deploy:local
```

## 📝 Contract Functions

### `storeHash(bytes32 hash)`
Store a document hash on the blockchain. Reverts if hash already exists.

### `verifyHash(bytes32 hash)`
Get the timestamp when a document was notarized. Returns 0 if not found.

### `isNotarized(bytes32 hash)`
Check if a document has been notarized. Returns boolean.

## 🔧 Configuration

Update `hardhat.config.js` with your:
- RPC URL (from Alchemy/Infura)
- Private key (in `.env` file)
- Etherscan API key (for verification)

## 🧪 Testing

Create tests in `test/` directory and run:

```bash
npm test
```

## 📊 Gas Estimates

- `storeHash`: ~45,000 gas
- `verifyHash`: ~24,000 gas (view function, no gas cost)

## 🌐 Networks

- **Sepolia**: Ethereum testnet
- **Mumbai**: Polygon testnet  
- **Hardhat**: Local development network

## ⚠️ Security Notes

- Never commit private keys
- Use `.env` file for sensitive data
- Test thoroughly before mainnet deployment
- Consider adding access control for production

## 🔗 Useful Links

- [Hardhat Documentation](https://hardhat.org/docs)
- [Solidity Documentation](https://docs.soliditylang.org/)
- [Sepolia Faucet](https://sepoliafaucet.com/)
- [Mumbai Faucet](https://faucet.polygon.technology/)
