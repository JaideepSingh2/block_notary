require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config({ path: "../backend/.env" });

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.19",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    // Ethereum Sepolia Testnet
    sepolia: {
      url: process.env.RPC_URL || "https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 11155111
    },
    // Polygon Mumbai Testnet
    mumbai: {
      url: process.env.RPC_URL || "https://polygon-mumbai.g.alchemy.com/v2/YOUR_API_KEY",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 80001
    },
    // Local Hardhat Network
    hardhat: {
      chainId: 31337
    }
  },
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts"
  },
  etherscan: {
    apiKey: {
      sepolia: process.env.ETHERSCAN_API_KEY || "",
      polygonMumbai: process.env.POLYGONSCAN_API_KEY || ""
    }
  }
};
