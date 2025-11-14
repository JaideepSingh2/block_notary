// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title Notary
 * @dev Store and verify document hashes on blockchain
 */
contract Notary {
    
    // Mapping: hash => timestamp
    mapping(bytes32 => uint256) public timestamps;
    
    // Mapping: hash => notarizer address
    mapping(bytes32 => address) public notarizers;
    
    // Events
    event DocumentNotarized(
        bytes32 indexed documentHash,
        address indexed notarizer,
        uint256 timestamp
    );
    
    event DocumentVerified(
        bytes32 indexed documentHash,
        uint256 timestamp,
        address notarizer
    );
    
    /**
     * @dev Store a document hash
     * @param documentHash SHA-256 hash of the document
     */
    function storeHash(bytes32 documentHash) public {
        require(documentHash != bytes32(0), "Invalid hash");
        require(timestamps[documentHash] == 0, "Document already notarized");
        
        timestamps[documentHash] = block.timestamp;
        notarizers[documentHash] = msg.sender;
        
        emit DocumentNotarized(documentHash, msg.sender, block.timestamp);
    }
    
    /**
     * @dev Verify if a document hash exists
     * @param documentHash SHA-256 hash to verify
     * @return timestamp When the document was notarized (0 if not found)
     * @return notarizer Address that notarized the document
     */
    function verifyHash(bytes32 documentHash) 
        public 
        view 
        returns (uint256 timestamp, address notarizer) 
    {
        return (timestamps[documentHash], notarizers[documentHash]);
    }
    
    /**
     * @dev Check if a document is notarized
     * @param documentHash SHA-256 hash to check
     * @return bool True if notarized, false otherwise
     */
    function isNotarized(bytes32 documentHash) public view returns (bool) {
        return timestamps[documentHash] != 0;
    }
    
    /**
     * @dev Get notarization details
     * @param documentHash SHA-256 hash of the document
     * @return timestamp When notarized
     * @return notarizer Who notarized it
     * @return exists Whether it exists
     */
    function getNotarizationDetails(bytes32 documentHash) 
        public 
        view 
        returns (
            uint256 timestamp,
            address notarizer,
            bool exists
        ) 
    {
        timestamp = timestamps[documentHash];
        notarizer = notarizers[documentHash];
        exists = timestamp != 0;
    }
}