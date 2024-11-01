# FastChain-A-Lightweight-Python-Blockchain-with-WebSocket-based-Miner-Network


```
███████╗ █████╗ ███████╗████████╗ ██████╗██╗  ██╗ █████╗ ██╗███╗   ██╗
██╔════╝██╔══██╗██╔════╝╚══██╔══╝██╔════╝██║  ██║██╔══██╗██║████╗  ██║
█████╗  ███████║███████╗   ██║   ██║     ███████║███████║██║██╔██╗ ██║
██╔══╝  ██╔══██║╚════██║   ██║   ██║     ██╔══██║██╔══██║██║██║╚██╗██║
██║     ██║  ██║███████║   ██║   ╚██████╗██║  ██║██║  ██║██║██║ ╚████║
╚═╝     ╚═╝  ╚═╝╚══════╝   ╚═╝    ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
```


This project implements a blockchain API with WebSocket support, allowing users to interact with a blockchain network for adding transactions, mining blocks, and checking balances in real-time. Built using FastAPI, the API provides HTTP-based REST endpoints and WebSocket connections for miners.

## Features

- **Blockchain Operations**: Add transactions, mine blocks, validate blockchain integrity.

### API Endpoints:

- `GET /` - Returns API info and available endpoints.
- `GET /chain` - Retrieves the blockchain with chain length and validity status.
- `POST /txn` - Adds a new transaction to the blockchain.
- `POST /add` - Adds coninbase to a specified user.
- `GET /balance/{address}` - Retrieves balance for a given address.
- `GET /pending` - Shows pending transactions.
- `GET /dev` - System status information.

### WebSocket:

- `ws://localhost:8000/ws/miner` - Allows miners to connect and receive live blockchain updates. Connected miners can mine new blocks, with broadcasts of new blocks in real-time.

## Setup & Usage

### Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- httpx

### Installation

Install dependencies:

## Setup & Usage
### Requirements
Python 3.8+
FastAPI, Uvicorn, httpx
Install dependencies:

### Start the server:

```python
fastapi dev app/main.py
```

### Project Structure

- main.py: FastAPI app configuration with blockchain and WebSocket support.
- blockchain.py: Core blockchain functionality.
- connectionManager.py: Manages WebSocket connections for miners.
