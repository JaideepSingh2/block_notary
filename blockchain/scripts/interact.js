const hre = require("hardhat");
require("dotenv").config({ path: "../backend/.env" });

async function main() {
  const contractAddress = process.env.CONTRACT_ADDRESS;

  if (!contractAddress) {
    console.error("❌ CONTRACT_ADDRESS not found in .env file");
    process.exit(1);
  }

  console.log("🔗 Connecting to contract at:", contractAddress);

  const Notary = await hre.ethers.getContractFactory("Notary");
  const notary = Notary.attach(contractAddress);

  // Example: Store a hash
  const testHash = hre.ethers.keccak256(
    hre.ethers.toUtf8Bytes("Test Document")
  );
  console.log("\n📝 Test hash:", testHash);

  console.log("\n⏳ Storing hash...");
  const tx = await notary.storeHash(testHash);
  await tx.wait();
  console.log("✅ Hash stored! Transaction:", tx.hash);

  // Verify the hash
  console.log("\n🔍 Verifying hash...");
  const [timestamp, notarizer] = await notary.verifyHash(testHash);

  console.log("✅ Verification result:");
  console.log("   📅 Timestamp:", timestamp.toString());
  console.log("   👤 Notarizer:", notarizer);
  console.log("   ✓ Exists:", timestamp > 0);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
