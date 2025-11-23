const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("\n🔧 Interacting with Notary Contract...\n");

  // Load deployment info
  const deploymentPath = path.join(__dirname, "../deployments.json");
  
  if (!fs.existsSync(deploymentPath)) {
    console.error("❌ No deployment found. Please deploy the contract first.");
    process.exit(1);
  }

  const deployments = JSON.parse(fs.readFileSync(deploymentPath, "utf8"));
  const deployment = deployments[hre.network.name];

  if (!deployment) {
    console.error(`❌ No deployment found for network: ${hre.network.name}`);
    process.exit(1);
  }

  console.log("📍 Contract Address:", deployment.contractAddress);
  console.log("🌐 Network:", hre.network.name, "\n");

  // Get contract instance
  const Notary = await hre.ethers.getContractFactory("Notary");
  const notary = Notary.attach(deployment.contractAddress);

  // Example: Store a test hash
  const testHash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef";
  
  console.log("📝 Storing test hash:", testHash);
  const tx = await notary.storeHash(testHash);
  await tx.wait();
  console.log("✅ Hash stored! Transaction:", tx.hash, "\n");

  // Verify the hash
  console.log("🔍 Verifying hash...");
  const timestamp = await notary.verifyHash(testHash);
  console.log("✅ Timestamp:", timestamp.toString());
  console.log("📅 Date:", new Date(Number(timestamp) * 1000).toISOString(), "\n");

  // Check if notarized
  const isNotarized = await notary.isNotarized(testHash);
  console.log("✓ Is Notarized:", isNotarized, "\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Error:", error);
    process.exit(1);
  });
