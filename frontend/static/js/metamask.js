/**
 * MetaMask Integration for Notary DApp
 * Handles wallet connection and blockchain transactions
 */

// Global variables
let web3;
let userAccount;
let notaryContract;
const CONTRACT_ABI = [
  {
    inputs: [
      { internalType: "bytes32", name: "documentHash", type: "bytes32" },
    ],
    name: "storeHash",
    outputs: [],
    stateMutability: "nonpayable",
    type: "function",
  },
  {
    inputs: [
      { internalType: "bytes32", name: "documentHash", type: "bytes32" },
    ],
    name: "verifyHash",
    outputs: [
      { internalType: "uint256", name: "timestamp", type: "uint256" },
      { internalType: "address", name: "notarizer", type: "address" },
    ],
    stateMutability: "view",
    type: "function",
  },
  {
    inputs: [
      { internalType: "bytes32", name: "documentHash", type: "bytes32" },
    ],
    name: "isNotarized",
    outputs: [{ internalType: "bool", name: "", type: "bool" }],
    stateMutability: "view",
    type: "function",
  },
  {
    anonymous: false,
    inputs: [
      {
        indexed: true,
        internalType: "bytes32",
        name: "documentHash",
        type: "bytes32",
      },
      {
        indexed: true,
        internalType: "address",
        name: "notarizer",
        type: "address",
      },
      {
        indexed: false,
        internalType: "uint256",
        name: "timestamp",
        type: "uint256",
      },
    ],
    name: "DocumentNotarized",
    type: "event",
  },
];

/**
 * Initialize Web3 and check MetaMask
 */
async function initWeb3() {
  if (typeof window.ethereum !== "undefined") {
    console.log("✅ MetaMask detected");
    web3 = new Web3(window.ethereum);

    // Get contract info from backend
    await loadContractInfo();

    // Check if already connected
    const accounts = await web3.eth.getAccounts();
    if (accounts.length > 0) {
      userAccount = accounts[0];
      updateWalletUI(userAccount);
    }

    // Listen for account changes
    window.ethereum.on("accountsChanged", handleAccountsChanged);
    window.ethereum.on("chainChanged", handleChainChanged);

    return true;
  } else {
    console.log("⚠️ MetaMask not detected");
    return false;
  }
}

/**
 * Load contract address from backend
 */
async function loadContractInfo() {
  try {
    const response = await fetch("/api/contract-info");
    const data = await response.json();

    if (data.success) {
      const contractAddress = data.contract_address;
      notaryContract = new web3.eth.Contract(CONTRACT_ABI, contractAddress);
      console.log("📜 Contract loaded at:", contractAddress);
    }
  } catch (error) {
    console.error("❌ Error loading contract info:", error);
  }
}

/**
 * Connect wallet button handler
 */
async function connectWallet() {
  if (typeof window.ethereum === "undefined") {
    alert(
      "⚠️ MetaMask not installed! Please install MetaMask to use this DApp."
    );
    window.open("https://metamask.io/download/", "_blank");
    return;
  }

  try {
    // Request account access
    const accounts = await window.ethereum.request({
      method: "eth_requestAccounts",
    });

    userAccount = accounts[0];
    updateWalletUI(userAccount);

    console.log("✅ Wallet connected:", userAccount);

    // Check network
    const chainId = await web3.eth.getChainId();
    console.log("🌐 Connected to chain ID:", chainId);

    return userAccount;
  } catch (error) {
    console.error("❌ Error connecting wallet:", error);
    alert("Failed to connect wallet: " + error.message);
    return null;
  }
}

/**
 * Update wallet UI
 */
function updateWalletUI(address) {
  const connectBtn = document.getElementById("connectWallet");
  const walletAddr = document.getElementById("walletAddress");

  if (address) {
    const shortAddr = `${address.substring(0, 6)}...${address.substring(38)}`;
    connectBtn.innerHTML = '<i class="fas fa-check-circle"></i> Connected';
    connectBtn.classList.remove("btn-outline-light");
    connectBtn.classList.add("btn-success");
    walletAddr.textContent = shortAddr;
    walletAddr.style.display = "inline";
  } else {
    connectBtn.innerHTML = '<i class="fas fa-wallet"></i> Connect Wallet';
    connectBtn.classList.remove("btn-success");
    connectBtn.classList.add("btn-outline-light");
    walletAddr.style.display = "none";
  }
}

/**
 * Handle account changes
 */
function handleAccountsChanged(accounts) {
  if (accounts.length === 0) {
    console.log("🔌 Wallet disconnected");
    userAccount = null;
    updateWalletUI(null);
  } else if (accounts[0] !== userAccount) {
    userAccount = accounts[0];
    updateWalletUI(userAccount);
    console.log("🔄 Account changed to:", userAccount);
    location.reload();
  }
}

/**
 * Handle chain changes
 */
function handleChainChanged(chainId) {
  console.log("🔄 Network changed to:", chainId);
  location.reload();
}

/**
 * Notarize document with MetaMask
 */
async function notarizeWithMetaMask(documentHash) {
  try {
    // Ensure wallet is connected
    if (!userAccount) {
      await connectWallet();
    }

    if (!userAccount) {
      throw new Error("Wallet not connected");
    }

    // Convert hex string to bytes32
    const hashBytes = "0x" + documentHash;

    // Check if already notarized
    const isNotarized = await notaryContract.methods
      .isNotarized(hashBytes)
      .call();
    if (isNotarized) {
      throw new Error("Document already notarized");
    }

    console.log("📝 Sending transaction...");

    // Estimate gas
    const gasEstimate = await notaryContract.methods
      .storeHash(hashBytes)
      .estimateGas({
        from: userAccount,
      });

    // Send transaction
    const receipt = await notaryContract.methods.storeHash(hashBytes).send({
      from: userAccount,
      gas: Math.floor(gasEstimate * 1.2), // Add 20% buffer
    });

    console.log("✅ Transaction successful:", receipt);

    // Get explorer URL
    const chainId = await web3.eth.getChainId();
    const explorerUrl = getExplorerUrl(chainId, receipt.transactionHash);

    return {
      success: true,
      transactionHash: receipt.transactionHash,
      blockNumber: receipt.blockNumber,
      gasUsed: receipt.gasUsed,
      explorerUrl: explorerUrl,
    };
  } catch (error) {
    console.error("❌ Transaction error:", error);

    let errorMessage = error.message;

    // Handle common errors
    if (error.code === 4001) {
      errorMessage = "Transaction rejected by user";
    } else if (error.message.includes("insufficient funds")) {
      errorMessage = "Insufficient funds for gas";
    }

    return {
      success: false,
      error: errorMessage,
    };
  }
}

/**
 * Verify document with MetaMask (read-only)
 */
async function verifyWithMetaMask(documentHash) {
  try {
    const hashBytes = "0x" + documentHash;

    // Call smart contract (no gas needed for view functions)
    const result = await notaryContract.methods.verifyHash(hashBytes).call();

    const timestamp = parseInt(result[0]);
    const notarizer = result[1];

    return {
      success: true,
      exists: timestamp > 0,
      timestamp: timestamp,
      notarizer: notarizer,
      hash: documentHash,
    };
  } catch (error) {
    console.error("❌ Verification error:", error);
    return {
      success: false,
      error: error.message,
    };
  }
}

/**
 * Get block explorer URL based on chain ID
 */
function getExplorerUrl(chainId, txHash) {
  const explorers = {
    1: "https://etherscan.io",
    11155111: "https://sepolia.etherscan.io",
    137: "https://polygonscan.com",
    80001: "https://mumbai.polygonscan.com",
    5: "https://goerli.etherscan.io",
  };

  const baseUrl = explorers[chainId] || "https://etherscan.io";
  return `${baseUrl}/tx/${txHash}`;
}

/**
 * Get current network name
 */
async function getNetworkName() {
  const chainId = await web3.eth.getChainId();

  const networks = {
    1: "Ethereum Mainnet",
    11155111: "Sepolia Testnet",
    137: "Polygon Mainnet",
    80001: "Mumbai Testnet",
    5: "Goerli Testnet",
    31337: "Localhost",
  };

  return networks[chainId] || `Unknown Network (${chainId})`;
}

/**
 * Initialize on page load
 */
document.addEventListener("DOMContentLoaded", async () => {
  await initWeb3();

  // Attach connect wallet handler
  const connectBtn = document.getElementById("connectWallet");
  if (connectBtn) {
    connectBtn.addEventListener("click", connectWallet);
  }
});
