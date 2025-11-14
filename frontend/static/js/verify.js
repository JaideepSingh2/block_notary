/**
 * Verification Page Logic
 * Handles document verification through file upload or hash input
 */

// File upload verification
document
  .getElementById("verifyFileForm")
  ?.addEventListener("submit", async (e) => {
    e.preventDefault();

    const fileInput = document.getElementById("verifyFileInput");
    const file = fileInput.files[0];

    if (!file) {
      showAlert("Please select a file", "warning");
      return;
    }

    showLoading("Computing hash and verifying...");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/api/verify", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      hideLoading();

      if (data.success) {
        displayVerificationResult(data);
      } else {
        showAlert(data.error, "danger");
      }
    } catch (error) {
      hideLoading();
      showAlert("Error: " + error.message, "danger");
    }
  });

// Hash input verification
document
  .getElementById("verifyHashForm")
  ?.addEventListener("submit", async (e) => {
    e.preventDefault();

    const hashInput = document.getElementById("hashInput");
    const hash = hashInput.value.trim();

    if (!hash) {
      showAlert("Please enter a hash", "warning");
      return;
    }

    // Validate hash format
    if (!/^[a-fA-F0-9]{64}$/.test(hash)) {
      showAlert(
        "Invalid hash format. Must be 64 hexadecimal characters.",
        "danger"
      );
      return;
    }

    showLoading("Verifying hash on blockchain...");

    try {
      const response = await fetch("/api/verify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ hash: hash }),
      });

      const data = await response.json();

      hideLoading();

      if (data.success) {
        displayVerificationResult(data);
      } else {
        showAlert(data.error, "danger");
      }
    } catch (error) {
      hideLoading();
      showAlert("Error: " + error.message, "danger");
    }
  });

/**
 * Display verification results
 */
function displayVerificationResult(data) {
  const resultDiv = document.getElementById("verificationResult");
  const successDiv = document.getElementById("successResult");
  const failureDiv = document.getElementById("failureResult");

  resultDiv.style.display = "block";

  if (data.exists) {
    // Document verified
    successDiv.style.display = "block";
    failureDiv.style.display = "none";

    document.getElementById("verifiedHash").textContent = data.hash;
    document.getElementById("notarizedDate").textContent =
      data.formatted_timestamp;
    document.getElementById("notarizerAddress").textContent = data.notarizer;
    document.getElementById("timestamp").textContent = new Date(
      data.timestamp * 1000
    ).toLocaleString();

    if (data.filename) {
      document.getElementById("filenameRow").style.display = "flex";
      document.getElementById("verifiedFilename").textContent = data.filename;
    }

    document.getElementById("blockExplorerLink").href = data.block_explorer_url;

    showAlert("✅ Document verified successfully!", "success");
  } else {
    // Document not found
    successDiv.style.display = "none";
    failureDiv.style.display = "block";

    document.getElementById("failedHash").textContent = data.hash;

    showAlert("⚠️ Document not found on blockchain", "warning");
  }

  // Scroll to result
  resultDiv.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

/**
 * Reset verification form
 */
function resetVerification() {
  document.getElementById("verifyFileForm")?.reset();
  document.getElementById("verifyHashForm")?.reset();
  document.getElementById("verificationResult").style.display = "none";
  document.getElementById("alertContainer").innerHTML = "";
}

/**
 * Show alert message
 */
function showAlert(message, type) {
  const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
  document.getElementById("alertContainer").innerHTML = alertHtml;
}

/**
 * Show loading indicator
 */
function showLoading(message) {
  const loadingHtml = `
        <div class="alert alert-info">
            <span class="spinner-border spinner-border-sm me-2"></span> ${message}
        </div>
    `;
  document.getElementById("alertContainer").innerHTML = loadingHtml;
}

/**
 * Hide loading indicator
 */
function hideLoading() {
  const alertContainer = document.getElementById("alertContainer");
  const loadingAlert = alertContainer.querySelector(".alert-info");
  if (loadingAlert && loadingAlert.querySelector(".spinner-border")) {
    alertContainer.innerHTML = "";
  }
}
