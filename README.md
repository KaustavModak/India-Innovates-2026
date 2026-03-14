# Post-Count Cryptographic Audit Layer for Election Integrity

A tamper-proof verification layer that allows anyone to verify that official election result files have never been altered.

## What This System Does

- Election officials upload official digital result files
- The system generates a SHA-256 cryptographic fingerprint
- The fingerprint is stored immutably on a Hyperledger Fabric blockchain
- Citizens can verify any result file against the blockchain record
- Any tampering is instantly detected

## What This System Does NOT Do

- Replace voting machines
- Store votes or voter identities
- Enable online voting

## Architecture

```
Citizen Browser → Next.js Dashboard → FastAPI Backend → Hyperledger Fabric → Immutable Ledger
```

## Tech Stack

| Layer          | Technology                          |
|----------------|-------------------------------------|
| Frontend       | Next.js, TypeScript, TailwindCSS    |
| Backend        | Python, FastAPI                     |
| Blockchain     | Hyperledger Fabric                  |
| Database       | PostgreSQL, Redis                   |
| Security       | SHA-256, PKI, TLS, RBAC, MFA       |
| Infrastructure | Docker, Kubernetes, NGINX, GH Actions |

## Project Structure

```
├── frontend/          # Next.js dashboard
├── backend/           # FastAPI services
├── blockchain/        # Hyperledger Fabric network + chaincode
├── database/          # SQL migrations
├── infrastructure/    # Docker, K8s, CI/CD, monitoring
└── docs/              # Architecture documentation
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+

### Development

```bash
# Start all services
docker-compose -f infrastructure/docker/docker-compose.yml up -d

# Backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## License

MIT
