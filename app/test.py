import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket, WebSocketState
from typing import Generator
import pytest_asyncio
import asyncio
from blockchain import Blockchain
from connectionManager import ConnectionManager
import json
from httpx import AsyncClient
from typing import List, Dict, Generator
import uvicorn
from main import app, MyFastAPI
from blockchain import Blockchain
from connectionManager import ConnectionManager



@pytest.fixture
def test_app() -> Generator:
    """Fixture for creating a test application instance."""
    app.blockchain = Blockchain()
    app.manager = ConnectionManager()
    return app

@pytest.fixture
def client(test_app) -> Generator:
    """Fixture for creating a TestClient instance."""
    with TestClient(test_app) as client:
        yield client

class TestBlockchainAPI:
    def test_root_endpoint(self, client):
        """Test the root endpoint returns correct API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        
        # Check if all expected endpoints are present
        endpoints = data["endpoints"]
        assert "view_blockchain" in endpoints
        assert "send_coins" in endpoints
        assert "check_balance" in endpoints
        assert "pending_transactions" in endpoints
        assert "mine" in endpoints

    def test_get_chain(self, client):
        """Test getting the blockchain."""
        response = client.get("/chain")
        assert response.status_code == 200
        data = response.json()
        
        assert "chain" in data
        assert "length" in data
        assert "is_valid" in data
        assert isinstance(data["chain"], list)
        assert isinstance(data["length"], int)
        assert isinstance(data["is_valid"], bool)

    def test_add_transaction(self, client):
        """Test adding a new transaction."""
        # First add some initial balance
        init_balance = client.post("/add", json={
            "receiver": "user1",
            "amount": 100
        })
        assert init_balance.status_code == 200

        # Test valid transaction
        transaction = {
            "sender": "user1",
            "receiver": "user2",
            "amount": 50
        }
        response = client.post("/txn", json=transaction)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "transaction" in data
        assert data["transaction"]["amount"] == 50

        # Test invalid transaction (insufficient balance)
        invalid_transaction = {
            "sender": "user1",
            "receiver": "user2",
            "amount": 1000
        }
        response = client.post("/txn", json=invalid_transaction)
        assert "Insufficient balance" in str(response.content)

        # Test invalid transaction (negative amount)
        negative_transaction = {
            "sender": "user1",
            "receiver": "user2",
            "amount": -50
        }
        response = client.post("/txn", json=negative_transaction)
        assert "Amount must be positive" in str(response.content)

    def test_get_balance(self, client):
        """Test getting balance for an address."""
        # First add some balance
        init_balance = client.post("/add", json={
            "receiver": "test_user",
            "amount": 100
        })
        assert init_balance.status_code == 200

        # Check balance
        response = client.get("/balance/test_user")
        assert response.status_code == 200
        data = response.json()
        assert data["address"] == "test_user"
        assert data["balance"] == 100

        # Check non-existent user
        response = client.get("/balance/nonexistent_user")
        assert response.status_code == 200
        assert "Message USer Donest Exists" in str(response.content)

    def test_pending_transactions(self, client):
        """Test getting pending transactions."""
        # First add a transaction
        init_balance = client.post("/add", json={
            "receiver": "sender1",
            "amount": 100
        })
        assert init_balance.status_code == 200

        transaction = {
            "sender": "sender1",
            "receiver": "receiver1",
            "amount": 50
        }
        client.post("/txn", json=transaction)

        # Check pending transactions
        response = client.get("/pending")
        assert response.status_code == 200
        data = response.json()
        assert "pending_transactions" in data
        assert "count" in data
        assert data["count"] > 0
        assert isinstance(data["pending_transactions"], list)


    def test_add_balance(self, client):
        """Test adding balance to an address."""
        response = client.post("/add", json={
            "receiver": "new_user",
            "amount": 100
        })
        assert response.status_code == 200
        
        # Verify balance was added
        balance_response = client.get("/balance/new_user")
        balance_data = balance_response.json()
        assert balance_data["new_user"] == 100

    def test_dev_endpoint(self, client):
        """Test the dev endpoint returns correct system status."""
        response = client.get("/dev")
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "blockchain" in data["status"]
        assert "network" in data["status"]
        assert "api" in data
        assert "endpoints" in data
        
        

class MockWebSocket:
    def __init__(self):
        self.sent_messages = []
        self.closed = False
        self.accepted = False
        self.state = WebSocketState.CONNECTING

    async def accept(self):
        self.accepted = True
        self.state = WebSocketState.CONNECTED

    async def send_json(self, message: dict):
        if not self.closed:
            self.sent_messages.append(message)

    async def receive_json(self):
        return {"type": "test_message"}

    def is_connected(self):
        return not self.closed

    async def close(self):
        self.closed = True
        self.state = WebSocketState.DISCONNECTED

class TestConnectionManager:
    @pytest.mark.asyncio
    async def test_connect(self):
        """Test WebSocket connection."""
        manager = ConnectionManager()
        mock_ws = MockWebSocket()
        
        await manager.connect(mock_ws)
        
        assert mock_ws in manager.active_connections
        assert mock_ws.accepted
        assert len(manager.active_connections) == 1

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test WebSocket disconnection."""
        manager = ConnectionManager()
        mock_ws = MockWebSocket()
        
        await manager.connect(mock_ws)
        manager.disconnect(mock_ws)
        
        assert mock_ws not in manager.active_connections
        assert len(manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcasting messages to all connected clients."""
        manager = ConnectionManager()
        mock_ws1 = MockWebSocket()
        mock_ws2 = MockWebSocket()
        
        await manager.connect(mock_ws1)
        await manager.connect(mock_ws2)
        
        test_message = {"type": "test", "data": "Hello"}
        await manager.broadcast(test_message)
        
        assert test_message in mock_ws1.sent_messages
        assert test_message in mock_ws2.sent_messages

    @pytest.mark.asyncio
    async def test_broadcast_with_disconnected_client(self):
        """Test broadcasting when one client is disconnected."""
        manager = ConnectionManager()
        mock_ws1 = MockWebSocket()
        mock_ws2 = MockWebSocket()
        
        await manager.connect(mock_ws1)
        await manager.connect(mock_ws2)

     
        # Simulate ws2 disconnection

        manager.disconnect(mock_ws2)
        
        test_message = {"type": "test", "data": "Hello"}
        await manager.broadcast(test_message)
        
        print(mock_ws1.sent_messages)
        print(manager.active_connections)
        
        assert test_message in mock_ws1.sent_messages
        assert mock_ws2 not in manager.active_connections

    @pytest.mark.asyncio
    async def test_mining_lock(self):
        """Test the mining lock functionality."""
        manager = ConnectionManager()
        
        async with manager.mining_lock:
            # Verify we can acquire the lock
            assert True
            
        # Verify we can acquire it again
        async with manager.mining_lock:
            assert True
            
            


from fastapi.testclient import TestClient

from typing import List, Dict, Generator
import uvicorn
from main import app, MyFastAPI
from blockchain import Blockchain
from connectionManager import ConnectionManager

class MockWebSocket:
    def __init__(self):
        self.sent_messages = []
        self.closed = False
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def send_json(self, message: dict):
        if not self.closed:
            self.sent_messages.append(message)

    async def receive_json(self):
        return {"type": "test_message"}

    def is_connected(self):
        return not self.closed

    async def close(self):
        self.closed = True

@pytest.fixture(scope="module")
def event_loop():
    """Create an instance of the event loop for each test module."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def server():
    """Fixture to start and stop the FastAPI server."""
    # Initialize blockchain and manager
    app.blockchain = Blockchain()
    app.manager = ConnectionManager()
    
    # Start server
    config = uvicorn.Config(app, port=8000, log_level="error")
    server = uvicorn.Server(config)
    await server.serve()
    yield server
    # Cleanup
    await server.shutdown()

class TestConnectionManager:
    @pytest.mark.asyncio
    async def test_connect(self):
        """Test WebSocket connection."""
        manager = ConnectionManager()
        mock_ws = MockWebSocket()
        
        await manager.connect(mock_ws)
        
        assert mock_ws in manager.active_connections
        assert mock_ws.accepted
        assert len(manager.active_connections) == 1

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test WebSocket disconnection."""
        manager = ConnectionManager()
        mock_ws = MockWebSocket()
        
        await manager.connect(mock_ws)
        manager.disconnect(mock_ws)
        
        assert mock_ws not in manager.active_connections
        assert len(manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcasting messages to all connected clients."""
        manager = ConnectionManager()
        mock_ws1 = MockWebSocket()
        mock_ws2 = MockWebSocket()
        
        await manager.connect(mock_ws1)
        await manager.connect(mock_ws2)
        
        test_message = {"type": "test", "data": "Hello"}
        await manager.broadcast(test_message)
        
        assert test_message in mock_ws1.sent_messages
        assert test_message in mock_ws2.sent_messages

class TestWebSocketEndpoint:
    @pytest.mark.asyncio
    async def test_websocket_connection(self, server):
        """Test WebSocket connection and initial chain update."""
        async with websocket.connect('ws://localhost:8000/ws/miner') as websocket:
            data = await websocket.recv()
            data = json.loads(data)
            assert data["type"] == "chain_update"
            assert "chain" in data

    @pytest.mark.asyncio
    async def test_mining_request(self, server):
        """Test mining request handling."""
        # Add a test transaction to pending
        app.blockchain.add_transaction("sender", "receiver", 10)
        
        async with websocket.connect('ws://localhost:8000/ws/miner') as websocket:
            # Skip initial chain update
            await websocket.recv()
            
            # Send mining request
            await websocket.send(json.dumps({
                "type": "mine",
                "miner": "test_miner"
            }))
            
            # Receive mining response
            response = json.loads(await websocket.recv())
            assert response["type"] == "new_block"
            assert "block" in response

    @pytest.mark.asyncio
    async def test_new_block_broadcast(self, server):
        """Test broadcasting of new blocks."""
        async with WebSocket.connect('ws://localhost:8000/ws/miner') as ws1:
            async with WebSocket.connect('ws://localhost:8000/ws/miner') as ws2:
                # Skip initial chain updates
                await ws1.recv()
                await ws2.recv()
                
                # Create a test block
                test_block = {
                    "index": len(app.blockchain.chain),
                    "timestamp": "2024-01-01T00:00:00",
                    "transactions": [],
                    "proof": 100,
                    "previous_hash": app.blockchain.chain[-1]["hash"],
                    "hash": "test_hash"
                }
                
                # Send new block from ws1
                await ws1.send(json.dumps({
                    "type": "new_block",
                    "block": test_block
                }))
                
                # Both connections should receive the broadcast
                response1 = json.loads(await ws1.recv())
                response2 = json.loads(await ws2.recv())
                
                assert response1["type"] == "new_block"
                assert response2["type"] == "new_block"
                assert response1["block"] == test_block
                assert response2["block"] == test_block

    @pytest.mark.asyncio
    async def test_chain_update(self, server):
        """Test chain update functionality."""
        async with websocket.connect('ws://localhost:8000/ws/miner') as websocket:
            # Skip initial chain update
            await websocket.recv()
            
            # Send chain update
            new_chain = app.blockchain.chain
            await websocket.send(json.dumps({
                "type": "chain_update",
                "chain": new_chain
            }))
            
            # Should receive broadcast of chain update
            response = json.loads(await websocket.recv())
            assert response["type"] == "chain_update"
            assert response["chain"] == new_chain

    @pytest.mark.asyncio
    async def test_concurrent_mining(self, server):
        """Test concurrent mining requests."""
        async with WebSocket.connect('ws://localhost:8000/ws/miner') as ws1:
            async with WebSocket.connect('ws://localhost:8000/ws/miner') as ws2:
                # Skip initial chain updates
                await ws1.recv()
                await ws2.recv()
                
                # Add test transactions
                app.blockchain.add_transaction("sender1", "receiver1", 10)
                app.blockchain.add_transaction("sender2", "receiver2", 20)
                
                # Send concurrent mining requests
                await ws1.send(json.dumps({
                    "type": "mine",
                    "miner": "miner1"
                }))
                await ws2.send(json.dumps({
                    "type": "mine",
                    "miner": "miner2"
                }))
                
                # Both should receive the same block (first one to mine)
                response1 = json.loads(await ws1.recv())
                response2 = json.loads(await ws2.recv())
                
                assert response1 == response2
                assert response1["type"] == "new_block"

    @pytest.mark.asyncio
    async def test_invalid_message_handling(self, server):
        """Test handling of invalid messages."""
        async with websocket.connect('ws://localhost:8000/ws/miner') as websocket:
            # Skip initial chain update
            await websocket.recv()
            
            # Send invalid message
            await websocket.send(json.dumps({
                "type": "invalid_type",
                "data": "test"
            }))
            
            # Connection should still be open
            await websocket.send(json.dumps({
                "type": "mine",
                "miner": "test_miner"
            }))
            
            # Should still receive response
            response = json.loads(await websocket.recv())
            assert response["type"] == "new_block"