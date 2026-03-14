#!/bin/bash
# =============================================================
# Hyperledger Fabric Channel Setup Script
# Creates channel, joins peers, installs & commits chaincode
# =============================================================

set -e

CHANNEL_NAME="electionchannel"
CHAINCODE_NAME="election_audit"
CHAINCODE_VERSION="1.0"
CHAINCODE_PATH="../chaincode/election_audit"
ORDERER_ADDRESS="localhost:7050"

echo "============================================================="
echo "  Election Audit - Hyperledger Fabric Channel Setup"
echo "============================================================="

# 1. Generate crypto materials
echo ""
echo "[1/6] Generating crypto materials..."
cryptogen generate --config=./crypto-config.yaml --output=./crypto-config

# 2. Generate genesis block
echo ""
echo "[2/6] Generating genesis block..."
mkdir -p channel-artifacts
configtxgen -profile ElectionAuditOrdererGenesis -channelID system-channel -outputBlock ./channel-artifacts/genesis.block

# 3. Generate channel configuration transaction
echo ""
echo "[3/6] Generating channel configuration..."
configtxgen -profile ElectionChannel -outputCreateChannelTx ./channel-artifacts/${CHANNEL_NAME}.tx -channelID ${CHANNEL_NAME}

# 4. Generate anchor peer transactions
echo ""
echo "[4/6] Generating anchor peer transactions..."
configtxgen -profile ElectionChannel \
  -outputAnchorPeersUpdate ./channel-artifacts/ElectionOrg1MSPanchors.tx \
  -channelID ${CHANNEL_NAME} \
  -asOrg ElectionOrg1MSP

configtxgen -profile ElectionChannel \
  -outputAnchorPeersUpdate ./channel-artifacts/ElectionOrg2MSPanchors.tx \
  -channelID ${CHANNEL_NAME} \
  -asOrg ElectionOrg2MSP

# 5. Start the network
echo ""
echo "[5/6] Starting Fabric network..."
docker-compose up -d

echo ""
echo "Waiting for containers to start..."
sleep 10

# 6. Create and join channel
echo ""
echo "[6/6] Creating channel and joining peers..."

# Set environment for Org1
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="ElectionOrg1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=./crypto-config/peerOrganizations/org1.election-audit.com/peers/peer0.org1.election-audit.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=./crypto-config/peerOrganizations/org1.election-audit.com/users/Admin@org1.election-audit.com/msp
export CORE_PEER_ADDRESS=localhost:7051

# Create channel
peer channel create -o ${ORDERER_ADDRESS} -c ${CHANNEL_NAME} \
  -f ./channel-artifacts/${CHANNEL_NAME}.tx \
  --outputBlock ./channel-artifacts/${CHANNEL_NAME}.block \
  --tls --cafile ./crypto-config/ordererOrganizations/election-audit.com/orderers/orderer.election-audit.com/msp/tlscacerts/tlsca.election-audit.com-cert.pem

# Join Org1 peer
peer channel join -b ./channel-artifacts/${CHANNEL_NAME}.block

# Set environment for Org2
export CORE_PEER_LOCALMSPID="ElectionOrg2MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=./crypto-config/peerOrganizations/org2.election-audit.com/peers/peer0.org2.election-audit.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=./crypto-config/peerOrganizations/org2.election-audit.com/users/Admin@org2.election-audit.com/msp
export CORE_PEER_ADDRESS=localhost:9051

# Join Org2 peer
peer channel join -b ./channel-artifacts/${CHANNEL_NAME}.block

echo ""
echo "============================================================="
echo "  Channel '${CHANNEL_NAME}' created successfully!"
echo "  Peers from both organizations have joined."
echo ""
echo "  Next steps:"
echo "  1. Package chaincode:  peer lifecycle chaincode package"
echo "  2. Install chaincode:  peer lifecycle chaincode install"
echo "  3. Approve & commit:   peer lifecycle chaincode approveformyorg"
echo "============================================================="
