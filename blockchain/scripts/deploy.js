const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("\n🚀 Deploying Notary Smart Contract...\n");

  // Get deployer account
  const [deployer] = await hre.ethers.getSigners();
  console.log("📝 Deploying with account:", deployer.address);

  // Get account balance
  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("💰 Account balance:", hre.ethers.formatEther(balance), "ETH\n");

  // Deploy contract
  console.log("⏳ Deploying contract...");
  const Notary = await hre.ethers.getContractFactory("Notary");
  const notary = await Notary.deploy();

  await notary.waitForDeployment();
  const contractAddress = await notary.getAddress();

  console.log("\n✅ Contract deployed successfully!");
  console.log("📍 Contract Address:", contractAddress);
  console.log("🌐 Network:", hre.network.name);

  // Save deployment info
  const deploymentInfo = {
    network: hre.network.name,
    contractAddress: contractAddress,
    deployer: deployer.address,
    deploymentTime: new Date().toISOString(),
    blockNumber: await hre.ethers.provider.getBlockNumber()
  };

  const deploymentPath = path.join(__dirname, "../deployments.json");
  
  let deployments = {};
  if (fs.existsSync(deploymentPath)) {
    deployments = JSON.parse(fs.readFileSync(deploymentPath, "utf8"));
  }
  
  deployments[hre.network.name] = deploymentInfo;
  fs.writeFileSync(deploymentPath, JSON.stringify(deployments, null, 2));

  console.log("\n💾 Deployment info saved to deployments.json");

  // Update .env file reminder
  console.log("\n⚠️  IMPORTANT: Update your backend/.env file with:");
  console.log(`CONTRACT_ADDRESS=${contractAddress}`);

  // Verify contract on Etherscan (if not local network)
  if (hre.network.name !== "hardhat" && hre.network.name !== "localhost") {
    console.log("\n⏳ Waiting for block confirmations...");
    await notary.deploymentTransaction().wait(6);
    
    console.log("📝 Verifying contract on Etherscan...");
    try {
      await hre.run("verify:verify", {
        address: contractAddress,
        constructorArguments: [],
      });
      console.log("✅ Contract verified on Etherscan!");
    } catch (error) {
      console.log("⚠️  Verification failed:", error.message);
    }
  }

  console.log("\n🎉 Deployment complete!\n");
}

// Execute deployment
main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  });
