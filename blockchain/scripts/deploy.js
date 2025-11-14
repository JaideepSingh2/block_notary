const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("🚀 Starting deployment...\n");

  // Get deployer account
  const [deployer] = await hre.ethers.getSigners();
  console.log("📍 Deploying contracts with account:", deployer.address);

  // Get account balance
  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("💰 Account balance:", hre.ethers.formatEther(balance), "ETH\n");

  // Deploy contract
  console.log("📝 Deploying Notary contract...");
  const Notary = await hre.ethers.getContractFactory("Notary");
  const notary = await Notary.deploy();

  await notary.waitForDeployment();
  const contractAddress = await notary.getAddress();

  console.log("✅ Notary contract deployed to:", contractAddress);
  console.log("🔗 Network:", hre.network.name);
  console.log(
    "⛽ Gas used:",
    (await notary.deploymentTransaction().wait()).gasUsed.toString()
  );

  // Save contract address to .env
  const envPath = path.join(__dirname, "../../backend/.env");
  let envContent = "";

  if (fs.existsSync(envPath)) {
    envContent = fs.readFileSync(envPath, "utf8");

    // Update CONTRACT_ADDRESS
    if (envContent.includes("CONTRACT_ADDRESS=")) {
      envContent = envContent.replace(
        /CONTRACT_ADDRESS=.*/,
        `CONTRACT_ADDRESS=${contractAddress}`
      );
    } else {
      envContent += `\nCONTRACT_ADDRESS=${contractAddress}\n`;
    }
  } else {
    envContent = `CONTRACT_ADDRESS=${contractAddress}\n`;
  }

  fs.writeFileSync(envPath, envContent);
  console.log("\n💾 Contract address saved to backend/.env");

  // Verify contract (if on public network)
  if (hre.network.name !== "hardhat" && hre.network.name !== "localhost") {
    console.log("\n⏳ Waiting for block confirmations...");
    await notary.deploymentTransaction().wait(6);

    console.log("🔍 Verifying contract on Etherscan...");
    try {
      await hre.run("verify:verify", {
        address: contractAddress,
        constructorArguments: [],
      });
      console.log("✅ Contract verified!");
    } catch (error) {
      console.log("⚠️ Verification failed:", error.message);
    }
  }

  console.log("\n" + "=".repeat(50));
  console.log("🎉 DEPLOYMENT COMPLETE!");
  console.log("=".repeat(50));
  console.log("📋 Contract Address:", contractAddress);
  console.log("🌐 Network:", hre.network.name);
  console.log("=".repeat(50) + "\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  });
