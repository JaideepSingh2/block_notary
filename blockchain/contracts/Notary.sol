// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title Notary
 * @dev Smart contract for document notarization
 * Stores document hashes with timestamps on blockchain
 */
contract Notary {
    
    // Mapping: document hash => timestamp
    mapping(bytes32 => uint256) public timestamps;
    
    // Event emitted when a document is notarized
    event DocumentNotarized(
        bytes32 indexed hash,
        uint256 timestamp,
        address indexed notarizedBy
    );
    
    /**
     * @dev Store a document hash on the blockchain
     * @param hash The SHA-256 hash of the document (bytes32)
     */
    function storeHash(bytes32 hash) public {
        require(timestamps[hash] == 0, "Document already notarized");
        
        timestamps[hash] = block.timestamp;
        
        emit DocumentNotarized(hash, block.timestamp, msg.sender);
    }
    
    /**
     * @dev Verify if a document hash exists and get its timestamp
     * @param hash The SHA-256 hash to verify
     * @return timestamp The timestamp when document was notarized (0 if not found)
     */
    function verifyHash(bytes32 hash) public view returns (uint256) {
        return timestamps[hash];
    }
    
    /**
     * @dev Check if a document has been notarized
     * @param hash The SHA-256 hash to check
     * @return bool True if document exists, false otherwise
     */
    function isNotarized(bytes32 hash) public view returns (bool) {
        return timestamps[hash] > 0;
    }
}
