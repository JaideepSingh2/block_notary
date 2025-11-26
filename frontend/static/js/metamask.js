// MetaMask integration for notarizing documents

let userAccount = null;
let web3 = null;
let contractAddress = null;

// Initialize on page load
document.addEventListener("DOMContentLoaded", async () => {
  // Get contract info from backend
  await fetchContractInfo();

  // Set up event listeners
  document
    .getElementById("connectWallet")
    .addEventListener("click", connectWallet);
  document
    .getElementById("fileInput")
    .addEventListener("change", handleFileSelect);
  document
    .getElementById("notarizeForm")
    .addEventListener("submit", handleNotarize);
});

// Fetch contract address from backend
async function fetchContractInfo() {
  try {
    const response = await fetch("/api/contract-info");
    const data = await response.json();
    contractAddress = data.contractAddress;
  } catch (error) {
    console.error("Error fetching contract info:", error);
  }
}

// Connect to MetaMask wallet
async function connectWallet() {
  if (typeof window.ethereum === "undefined") {
    alert("Please install MetaMask to use this feature!");
    window.open("https://metamask.io/download/", "_blank");
    return;
  }

  try {
    // Request account access
    const accounts = await window.ethereum.request({
      method: "eth_requestAccounts",
    });

    userAccount = accounts[0];
    web3 = new Web3(window.ethereum);

    // Update UI
    document.getElementById("walletAddress").textContent = `${userAccount.slice(
      0,
      6
    )}...${userAccount.slice(-4)}`;
    document.getElementById("walletInfo").classList.remove("hidden");
    document.getElementById("uploadSection").classList.remove("hidden");
    document.getElementById("connectWallet").disabled = true;
    document.getElementById("connectWallet").textContent = "✓ Wallet Connected";

    // Listen for account changes
    window.ethereum.on("accountsChanged", (accounts) => {
      if (accounts.length === 0) {
        // User disconnected wallet
        location.reload();
      } else {
        userAccount = accounts[0];
        document.getElementById(
          "walletAddress"
        ).textContent = `${userAccount.slice(0, 6)}...${userAccount.slice(-4)}`;
      }
    });
  } catch (error) {
    console.error("Error connecting wallet:", error);
    alert("Failed to connect wallet. Please try again.");
  }
}

// Handle file selection
function handleFileSelect(event) {
  const file = event.target.files[0];
  if (file) {
    document.getElementById("fileLabel").textContent = file.name;
  }
}

// Handle document notarization
async function handleNotarize(event) {
  event.preventDefault();

  if (!userAccount) {
    alert("Please connect your wallet first!");
    return;
  }

  const fileInput = document.getElementById("fileInput");
  const file = fileInput.files[0];
  const documentType = document.getElementById("documentType").value;

  if (!file) {
    alert("Please select a file!");
    return;
  }

  if (!documentType) {
    alert("Please select a document type!");
    return;
  }

  // Show processing
  document.getElementById("uploadSection").classList.add("hidden");
  document.getElementById("verificationSection")?.classList.add("hidden");
  document.getElementById("processingSection").classList.remove("hidden");
  document.getElementById("processingMessage").textContent =
    "Verifying document signature...";

  try {
    // Step 1: Send file to backend to verify and compute hash
    const formData = new FormData();
    formData.append("file", file);
    formData.append("document_type", documentType);

    const response = await fetch("/api/notarize", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      // Handle verification failure
      if (data.verification_failed) {
        document.getElementById("processingSection").classList.add("hidden");
        showVerificationError(data, file.name, documentType);
        return;
      }
      throw new Error(data.error || "Failed to process document");
    }

    const docHash = data.hash;
    const docTypeLabel = data.document_type_label;

    document.getElementById("processingMessage").textContent =
      "✅ Signature verified! Waiting for MetaMask confirmation...";

    // Step 2: Send transaction via MetaMask
    await sendTransactionToBlockchain(
      docHash,
      file.name,
      documentType,
      docTypeLabel
    );
  } catch (error) {
    console.error("Error notarizing document:", error);
    showResult("error", "Failed to notarize document", error.message);
  }
}

// Show verification error with helpful message
function showVerificationError(data, filename, documentType) {
  const verificationSection = document.getElementById("verificationSection");
  const verificationContent = document.getElementById("verificationContent");

  if (!verificationSection || !verificationContent) {
    showResult("error", "Verification Failed", data.error);
    return;
  }

  verificationSection.classList.remove("hidden");

  let helpText = "";
  if (!data.owner_match) {
    helpText = `
      <p><strong>What this means:</strong> The document you uploaded was signed by a different person (different Aadhaar).</p>
      <p><strong>How to fix:</strong></p>
      <ul>
        <li>Make sure you're uploading a document that YOU signed</li>
        <li>Use the signing tool: <code>python tools/sign_document.py</code></li>
      </ul>
    `;
  } else if (!data.type_match) {
    helpText = `
      <p><strong>What this means:</strong> The document type you selected doesn't match the type embedded in the document's signature.</p>
      <p><strong>How to fix:</strong></p>
      <ul>
        <li>Select the correct document type from the dropdown</li>
        <li>Or re-sign the document with the correct type using the signing tool</li>
      </ul>
    `;
  } else {
    helpText = `
      <p>This document doesn't have a valid signature.</p>
      <p>Sign your document first using: <code>python tools/sign_document.py</code></p>
    `;
  }

  verificationContent.innerHTML = `
    <div class="error-message">
      <h3>❌ Document Verification Failed</h3>
      <p style="margin-bottom: 1rem;"><strong>Error:</strong> ${data.error}</p>
      ${helpText}
      <div style="margin-top: 1.5rem;">
        <button onclick="location.reload()" class="btn btn-primary">
          Try Again
        </button>
      </div>
    </div>
  `;
}

// Send transaction to blockchain via MetaMask
async function sendTransactionToBlockchain(
  docHash,
  filename,
  documentType,
  docTypeLabel
) {
  try {
    // Contract ABI for storeHash function
    const contractABI = [
      {
        inputs: [{ internalType: "bytes32", name: "hash", type: "bytes32" }],
        name: "storeHash",
        outputs: [],
        stateMutability: "nonpayable",
        type: "function",
      },
    ];

    // Create contract instance
    const contract = new web3.eth.Contract(contractABI, contractAddress);

    // Convert hash to bytes32
    const hashBytes = "0x" + docHash;

    // Estimate gas
    const gasEstimate = await contract.methods
      .storeHash(hashBytes)
      .estimateGas({ from: userAccount });

    // Send transaction
    const tx = await contract.methods.storeHash(hashBytes).send({
      from: userAccount,
      gas: gasEstimate + 10000, // Add buffer
    });

    // Step 3: Confirm notarization with backend to store metadata
    document.getElementById("processingMessage").textContent =
      "Storing document metadata...";

    await fetch("/api/notarize/confirm", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        hash: docHash,
        document_type: documentType,
        filename: filename,
        tx_hash: tx.transactionHash,
      }),
    });

    // Show success
    showResult(
      "success",
      "Document Notarized Successfully!",
      `<p><strong>File:</strong> ${filename}</p>
             <p><strong>Document Type:</strong> ${docTypeLabel}</p>
             <p><strong>Hash:</strong></p>
             <div class="hash-display">${docHash}</div>
             <p><strong>Transaction:</strong> <a href="https://sepolia.etherscan.io/tx/${tx.transactionHash}" target="_blank">View on Etherscan</a></p>
             <p>Your document has been permanently recorded on the blockchain!</p>`
    );
  } catch (error) {
    console.error("Transaction error:", error);

    let errorMessage = "Transaction failed";
    if (error.code === 4001) {
      errorMessage = "Transaction rejected by user";
    } else if (error.message) {
      errorMessage = error.message;
    }

    showResult("error", "Transaction Failed", errorMessage);
  }
}

// Show result message
function showResult(type, title, message) {
  document.getElementById("processingSection").classList.add("hidden");
  document.getElementById("resultSection").classList.remove("hidden");

  const resultContent = document.getElementById("resultContent");
  const className = type === "success" ? "success-message" : "error-message";

  resultContent.innerHTML = `
        <div class="${className}">
            <h3>${title}</h3>
            ${typeof message === "string" ? `<p>${message}</p>` : message}
            <button onclick="location.reload()" class="btn btn-primary" style="margin-top: 1rem;">
                Notarize Another Document
            </button>
        </div>
    `;
}

// Load Web3 library
(function () {
  const script = document.createElement("script");
  script.src = "https://cdn.jsdelivr.net/npm/web3@1.8.0/dist/web3.min.js";
  script.async = true;
  document.head.appendChild(script);
})();
