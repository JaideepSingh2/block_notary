const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("Notary Contract", function () {
  let notary;
  let owner;
  let addr1;

  beforeEach(async function () {
    [owner, addr1] = await ethers.getSigners();
    const Notary = await ethers.getContractFactory("Notary");
    notary = await Notary.deploy();
    await notary.waitForDeployment();
  });

  describe("Deployment", function () {
    it("Should deploy successfully", async function () {
      expect(await notary.getAddress()).to.be.properAddress;
    });
  });

  describe("Store Hash", function () {
    it("Should store a document hash", async function () {
      const hash = ethers.keccak256(ethers.toUtf8Bytes("Test Document"));

      await expect(notary.storeHash(hash))
        .to.emit(notary, "DocumentNotarized")
        .withArgs(
          hash,
          owner.address,
          await ethers.provider.getBlock("latest").then((b) => b.timestamp + 1)
        );

      const [timestamp, notarizer] = await notary.verifyHash(hash);
      expect(timestamp).to.be.gt(0);
      expect(notarizer).to.equal(owner.address);
    });

    it("Should reject duplicate hash", async function () {
      const hash = ethers.keccak256(ethers.toUtf8Bytes("Test Document"));

      await notary.storeHash(hash);
      await expect(notary.storeHash(hash)).to.be.revertedWith(
        "Document already notarized"
      );
    });

    it("Should reject zero hash", async function () {
      const zeroHash = ethers.ZeroHash;
      await expect(notary.storeHash(zeroHash)).to.be.revertedWith(
        "Invalid hash"
      );
    });
  });

  describe("Verify Hash", function () {
    it("Should return zero for non-existent hash", async function () {
      const hash = ethers.keccak256(ethers.toUtf8Bytes("Non-existent"));
      const [timestamp, notarizer] = await notary.verifyHash(hash);

      expect(timestamp).to.equal(0);
      expect(notarizer).to.equal(ethers.ZeroAddress);
    });

    it("Should return correct details for existing hash", async function () {
      const hash = ethers.keccak256(ethers.toUtf8Bytes("Test Document"));
      await notary.storeHash(hash);

      const [timestamp, notarizer] = await notary.verifyHash(hash);
      expect(timestamp).to.be.gt(0);
      expect(notarizer).to.equal(owner.address);
    });
  });
});
