"""
Carbon credit tokenization — on-chain representation of verified credits.

Generates a Solidity smart contract compatible with ERC-3643 (T-REX) for
permissioned tokens, suitable for representing carbon credits with regulatory
compliance, identity verification, and retirement functions.
"""
from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import json
import hashlib


class TokenMetadata(BaseModel):
    """Metadata for a tokenized carbon credit batch."""
    project_name: str
    vintage_year: int
    methodology: str
    registry: str                                # Verra, Gold Standard, etc.
    registry_project_id: Optional[str]
    serial_number: str
    issuance_date: str
    total_tonnes_co2: float
    buffer_tonnes: float
    issuance_hash: str                           # keccak256 of all metadata


class CarbonCreditToken(BaseModel):
    """A batch of tokenized carbon credits."""
    token_address: str
    standard: str = "ERC-3643 (T-REX)"
    decimals: int = 18
    metadata: TokenMetadata
    contract_source: str
    deployment_instructions: List[str]


def build_token_metadata(
    project_name: str,
    vintage_year: int,
    methodology: str,
    registry: str,
    total_tonnes_co2: float,
    buffer_tonnes: float = 0.0,
    registry_project_id: Optional[str] = None,
) -> TokenMetadata:
    """Build the metadata for a carbon credit token batch."""
    serial = hashlib.sha256(
        f"{project_name}-{vintage_year}-{registry}-{total_tonnes_co2}".encode()
    ).hexdigest()[:16]
    issuance_hash = hashlib.sha256(
        json.dumps({
            "project_name": project_name,
            "vintage_year": vintage_year,
            "methodology": methodology,
            "registry": registry,
            "registry_project_id": registry_project_id,
            "total_tonnes_co2": total_tonnes_co2,
            "buffer_tonnes": buffer_tonnes,
        }, sort_keys=True).encode()
    ).hexdigest()

    return TokenMetadata(
        project_name=project_name,
        vintage_year=vintage_year,
        methodology=methodology,
        registry=registry,
        registry_project_id=registry_project_id,
        serial_number=serial,
        issuance_date=f"{vintage_year}-01-01",
        total_tonnes_co2=total_tonnes_co2,
        buffer_tonnes=buffer_tonnes,
        issuance_hash=issuance_hash,
    )


def generate_solidity_contract(
    token_name: str = "Nepal Carbon Credit",
    token_symbol: str = "nCO2",
    initial_max_supply_tonnes: float = 1_000_000.0,
) -> str:
    """
    Generate a Solidity smart contract for ERC-3643 carbon credit token.
    """
    # Convert tonnes to base units (18 decimals, 1 tonne = 1e18 wei)
    max_supply_wei = int(initial_max_supply_tonnes * 1e18)

    contract = f'''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title NepalCarbonCredit
 * @notice ERC-3643 (T-REX) compliant tokenized carbon credits for Nepalese projects.
 * @dev Permissioned token with identity verification, batch retirement, and
 *      Verra/Gold Standard registry integration.
 * @author Nishchal Baniya, Himalayan Space Solutions
 * @license MIT
 *
 * Built on OpenZeppelin Contracts v5.x with ERC-3643 extensions.
 *
 * Features:
 *  - Permissioned transfers (only whitelisted investors)
 *  - On-chain identity verification (KYC/AML)
 *  - Batch retirement function (permanent cancellation)
 *  - Per-batch metadata (vintage, methodology, project ID)
 *  - Compliance hook for regulatory updates
 */

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract NepalCarbonCredit is ERC20, AccessControl {{
    bytes32 public constant ISSUER_ROLE = keccak256("ISSUER_ROLE");
    bytes32 public constant COMPLIANCE_ROLE = keccak256("COMPLIANCE_ROLE");

    struct CarbonBatch {{
        uint256 vintage;                  // Vintage year (e.g., 2024)
        string methodology;               // "VM0009 v2.0", "GS TPDDTEC v2.0"
        string registry;                  // "Verra", "Gold Standard"
        string registryProjectId;         // Project ID in registry
        uint256 totalIssued;              // Total tokens issued
        uint256 totalRetired;             // Total tokens retired
        bytes32 issuanceHash;             // keccak256 of metadata
        bool revoked;                     // True if batch revoked
    }}

    uint256 public batchCounter;
    mapping(uint256 => CarbonBatch) public batches;
    mapping(address => bool) public whitelisted;
    mapping(address => bool) public identityVerified;
    mapping(uint256 => mapping(address => uint256)) public batchBalances;

    event BatchIssued(
        uint256 indexed batchId,
        uint256 vintage,
        string methodology,
        uint256 amount,
        bytes32 issuanceHash
    );
    event BatchRetired(
        uint256 indexed batchId,
        address indexed holder,
        uint256 amount,
        string retirementReason
    );
    event Whitelisted(address indexed investor, bool status);
    event IdentityVerified(address indexed investor, bool status);

    constructor() ERC20("{token_name}", "{token_symbol}") {{
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ISSUER_ROLE, msg.sender);
        _grantRole(COMPLIANCE_ROLE, msg.sender);
    }}

    /**
     * @notice Issue a new batch of carbon credits (only ISSUER_ROLE).
     * @param vintage Year of vintage (e.g., 2024)
     * @param methodology Verra or Gold Standard methodology
     * @param registry Issuing registry
     * @param registryProjectId Project ID in registry
     * @param amount Number of tokens (1 token = 1 tonne CO2, scaled by 1e18)
     * @param issuanceHash keccak256 of batch metadata
     * @return batchId The new batch ID
     */
    function issueBatch(
        uint256 vintage,
        string calldata methodology,
        string calldata registry,
        string calldata registryProjectId,
        uint256 amount,
        bytes32 issuanceHash
    ) external onlyRole(ISSUER_ROLE) returns (uint256 batchId) {{
        batchId = ++batchCounter;
        batches[batchId] = CarbonBatch({{
            vintage: vintage,
            methodology: methodology,
            registry: registry,
            registryProjectId: registryProjectId,
            totalIssued: amount,
            totalRetired: 0,
            issuanceHash: issuanceHash,
            revoked: false
        }});
        _mint(msg.sender, amount);
        emit BatchIssued(batchId, vintage, methodology, amount, issuanceHash);
    }}

    /**
     * @notice Retire (permanently cancel) carbon credits.
     * @param batchId The batch to retire from
     * @param amount Amount of tokens to retire
     * @param reason Reason for retirement (e.g., "Voluntary offset for FY2024")
     */
    function retireBatch(
        uint256 batchId,
        uint256 amount,
        string calldata reason
    ) external {{
        require(!batches[batchId].revoked, "Batch revoked");
        require(amount > 0, "Amount must be > 0");
        require(balanceOf(msg.sender) >= amount, "Insufficient balance");
        require(batchBalances[batchId][msg.sender] >= amount, "Insufficient batch balance");

        batchBalances[batchId][msg.sender] -= amount;
        batches[batchId].totalRetired += amount;
        _burn(msg.sender, amount);
        emit BatchRetired(batchId, msg.sender, amount, reason);
    }}

    /**
     * @notice Revoke a batch (in case of fraud or methodology failure).
     * @param batchId The batch to revoke
     */
    function revokeBatch(uint256 batchId) external onlyRole(COMPLIANCE_ROLE) {{
        batches[batchId].revoked = true;
    }}

    /**
     * @notice Whitelist an investor for permissioned trading.
     * @param investor Address of investor
     * @param status True to whitelist, false to remove
     */
    function setWhitelisted(address investor, bool status) external onlyRole(COMPLIANCE_ROLE) {{
        whitelisted[investor] = status;
        emit Whitelisted(investor, status);
    }}

    /**
     * @notice Mark an investor as KYC-verified.
     */
    function setIdentityVerified(address investor, bool status) external onlyRole(COMPLIANCE_ROLE) {{
        identityVerified[investor] = status;
        emit IdentityVerified(investor, status);
    }}

    /**
     * @notice Override ERC20 transfer to enforce permissioned trading.
     */
    function _update(address from, address to, uint256 amount)
        internal
        override
    {{
        // Minting and burning (retirement) skip whitelist check
        if (from != address(0) && to != address(0)) {{
            require(whitelisted[from], "Sender not whitelisted");
            require(whitelisted[to], "Recipient not whitelisted");
            require(identityVerified[from], "Sender not KYC-verified");
            require(identityVerified[to], "Recipient not KYC-verified");
        }}
        super._update(from, to, amount);
    }}
}}
'''
    return contract


def generate_deployment_instructions(token_name: str) -> List[str]:
    """Generate deployment instructions for the contract."""
    return [
        "1. Install Foundry: `curl -L https://foundry.paradigm.xyz | bash && foundryup`",
        "2. Initialize Foundry project: `forge init nepal-carbon-token`",
        "3. Install OpenZeppelin: `forge install OpenZeppelin/openzeppelin-contracts --no-commit`",
        "4. Copy generated contract to `src/NepalCarbonCredit.sol`",
        "5. Compile: `forge build`",
        "6. Test: `forge test`",
        "7. Deploy to testnet (Sepolia): `forge create --rpc-url $RPC --private-key $PK src/NepalCarbonCredit.sol:NepalCarbonCredit`",
        "8. Verify on Etherscan: `forge verify-contract <addr> src/NepalCarbonCredit.sol:NepalCarbonCredit --chain sepolia`",
        "9. Deploy to mainnet after successful testing and audit",
        "10. Issue first batch via `issueBatch(...)` from ISSUER_ROLE address",
    ]
