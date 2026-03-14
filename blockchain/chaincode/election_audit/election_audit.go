// =============================================================
// Hyperledger Fabric Chaincode: Election Audit
//
// Stores and queries election result file hashes on the
// distributed ledger. Once a hash is committed, it becomes
// immutable — enabling tamper-proof verification.
// =============================================================

package main

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// ElectionAuditContract provides chaincode functions
type ElectionAuditContract struct {
	contractapi.Contract
}

// ResultHash represents a stored election result hash on the ledger
type ResultHash struct {
	DocType          string `json:"docType"`
	FileHash         string `json:"fileHash"`
	FileID           string `json:"fileId"`
	ConstituencyCode string `json:"constituencyCode"`
	ElectionDate     string `json:"electionDate"`
	ElectionType     string `json:"electionType"`
	UploaderID       string `json:"uploaderId"`
	StoredAt         string `json:"storedAt"`
	TxID             string `json:"txId"`
}

// StoreResultHash stores a new election result hash on the ledger.
// This is an immutable write — once stored, the hash cannot be modified or deleted.
func (c *ElectionAuditContract) StoreResultHash(
	ctx contractapi.TransactionContextInterface,
	fileHash string,
	fileID string,
	constituencyCode string,
	electionDate string,
	electionType string,
	uploaderID string,
) error {
	// Check if hash already exists (prevent duplicates)
	existing, err := ctx.GetStub().GetState(fileHash)
	if err != nil {
		return fmt.Errorf("failed to read from ledger: %v", err)
	}
	if existing != nil {
		return fmt.Errorf("hash already exists on the ledger: %s", fileHash)
	}

	// Create the result hash record
	record := ResultHash{
		DocType:          "resultHash",
		FileHash:         fileHash,
		FileID:           fileID,
		ConstituencyCode: constituencyCode,
		ElectionDate:     electionDate,
		ElectionType:     electionType,
		UploaderID:       uploaderID,
		StoredAt:         time.Now().UTC().Format(time.RFC3339),
		TxID:             ctx.GetStub().GetTxID(),
	}

	recordJSON, err := json.Marshal(record)
	if err != nil {
		return fmt.Errorf("failed to marshal record: %v", err)
	}

	// Store on the ledger using the hash as the key
	err = ctx.GetStub().PutState(fileHash, recordJSON)
	if err != nil {
		return fmt.Errorf("failed to store hash on ledger: %v", err)
	}

	// Emit event for off-chain listeners
	err = ctx.GetStub().SetEvent("HashStored", recordJSON)
	if err != nil {
		return fmt.Errorf("failed to emit event: %v", err)
	}

	return nil
}

// QueryResultHash queries a stored hash from the ledger.
// Returns the full record if found, empty if not.
func (c *ElectionAuditContract) QueryResultHash(
	ctx contractapi.TransactionContextInterface,
	fileHash string,
) (*ResultHash, error) {
	recordJSON, err := ctx.GetStub().GetState(fileHash)
	if err != nil {
		return nil, fmt.Errorf("failed to read from ledger: %v", err)
	}
	if recordJSON == nil {
		return nil, nil // Not found
	}

	var record ResultHash
	err = json.Unmarshal(recordJSON, &record)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal record: %v", err)
	}

	return &record, nil
}

// GetHashHistory returns the full modification history of a hash record.
// Since hashes are immutable, this typically shows a single creation entry.
func (c *ElectionAuditContract) GetHashHistory(
	ctx contractapi.TransactionContextInterface,
	fileHash string,
) ([]*ResultHash, error) {
	historyIterator, err := ctx.GetStub().GetHistoryForKey(fileHash)
	if err != nil {
		return nil, fmt.Errorf("failed to get history: %v", err)
	}
	defer historyIterator.Close()

	var records []*ResultHash
	for historyIterator.HasNext() {
		modification, err := historyIterator.Next()
		if err != nil {
			return nil, fmt.Errorf("failed to iterate history: %v", err)
		}

		if modification.Value == nil {
			continue
		}

		var record ResultHash
		err = json.Unmarshal(modification.Value, &record)
		if err != nil {
			continue
		}

		record.TxID = modification.TxId
		records = append(records, &record)
	}

	return records, nil
}

// GetAllHashes returns all stored hashes (for admin/audit purposes).
// Uses a rich query against CouchDB (if configured as state database).
func (c *ElectionAuditContract) GetAllHashes(
	ctx contractapi.TransactionContextInterface,
) ([]*ResultHash, error) {
	queryString := `{"selector":{"docType":"resultHash"}}`
	
	iterator, err := ctx.GetStub().GetQueryResult(queryString)
	if err != nil {
		return nil, fmt.Errorf("failed to execute query: %v", err)
	}
	defer iterator.Close()

	var records []*ResultHash
	for iterator.HasNext() {
		result, err := iterator.Next()
		if err != nil {
			return nil, fmt.Errorf("failed to iterate results: %v", err)
		}

		var record ResultHash
		err = json.Unmarshal(result.Value, &record)
		if err != nil {
			continue
		}
		records = append(records, &record)
	}

	return records, nil
}

// VerifyHash checks if a given hash exists on the ledger.
// Returns true if the hash is found, false otherwise.
func (c *ElectionAuditContract) VerifyHash(
	ctx contractapi.TransactionContextInterface,
	fileHash string,
) (bool, error) {
	recordJSON, err := ctx.GetStub().GetState(fileHash)
	if err != nil {
		return false, fmt.Errorf("failed to read from ledger: %v", err)
	}
	return recordJSON != nil, nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(&ElectionAuditContract{})
	if err != nil {
		fmt.Printf("Error creating election audit chaincode: %v\n", err)
		return
	}

	if err := chaincode.Start(); err != nil {
		fmt.Printf("Error starting chaincode: %v\n", err)
	}
}
