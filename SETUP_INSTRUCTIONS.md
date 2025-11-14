# 🚀 Complete Setup Instructions

## Step 1: Install Dependencies

### Backend

cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

### Blockchain

cd ../blockchain
npm install

## Step 2: Get Alchemy API Key

1. Go to https://www.alchemy.com/
2. Sign up for free account
3. Create new app → Select Ethereum Sepolia
4. Copy API key

## Step 3: Get Sepolia Test ETH

1. Visit https://sepoliafaucet.com/
2. Enter your MetaMask address
3. Get free test ETH (0.5 ETH)

## Step 4: Configure .env

cd backend
nano .env

# Add:

RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
PRIVATE_KEY=your_metamask_private_key_here
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')

## Step 5: Compile & Deploy Contract

cd ../blockchain
npx hardhat compile
npx hardhat run scripts/deploy.js --network sepolia

# Note the contract address - it auto-saves to .env

## Step 6: Run Application

cd ../backend
source venv/bin/activate
python app.py

# Open browser: http://localhost:5000

## Step 7: Test the Application

1. Connect MetaMask
2. Upload a test file
3. Notarize it (confirm in MetaMask)
4. Verify the same file
5. Should show notarization details!
