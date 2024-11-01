from fastapi.testclient import TestClient
import pytest
from httpx import AsyncClient
from fastapi import WebSocket
from main import app  
from schemas import TransactionRequest, BalanceRequest
import asyncio

client = TestClient(app)



@pytest.mark.asyncio
async def test_add_balance():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        data = {
       "receiver":"a1",
        "amount":1000
        }
        
        response = await client.post("/add", json=data)
        assert response.status_code == 200
        assert response.json() == {
            "a1":1000.0
        }

@pytest.mark.asyncio
async def test_add_transaction_invalid():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        # Test sender and receiver same
        data = {
            "sender": "address1",
            "receiver": "address1",
            "amount": 10.0
        }
        response = await client.post("/txn", json=data)
        assert response.status_code == 400
        assert response.json()["detail"] == "Sender cannot be same as receiver"

        # Test negative amount
        data = {
            "sender": "address1",
            "receiver": "address2",
            "amount": -5.0
        }
        response = await client.post("/txn", json=data)
        assert response.status_code == 400
        assert response.json()["detail"] == "Amount must be positive"

@pytest.mark.asyncio
async def test_mine_block():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/mine")
        if response.status_code == 400:  # In case of "No pending transactions to mine"
            assert response.json()["detail"] == "No pending transactions to mine"
        else:
            assert response.status_code == 200
            assert "Block successfully mined" in response.json()["message"]

@pytest.mark.asyncio
async def test_get_balance():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        address = "address1"
        response = await client.get(f"/balance/{address}")
        assert response.status_code == 200
        assert "balance" in response.json()

@pytest.mark.asyncio
async def test_get_pending_transactions():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/pending")
        assert response.status_code == 200
        assert "pending_transactions" in response.json()
        assert "count" in response.json()



@pytest.mark.asyncio
async def test_websocket_miner():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        async with client.websocket_connect("/ws/miner") as websocket:
            # Check initial chain update
            message = await websocket.receive_json()
            assert message["type"] == "chain_update"
            assert "chain" in message

            # Send chain_update message
            await websocket.send_json({"type": "chain_update", "chain": message["chain"]})
            response = await websocket.receive_json()
            assert response["type"] == "chain_update"
            assert "chain" in response

            # Send mine messageG
            await websocket.send_json({"type": "mine"})
            response = await websocket.receive_json()
            if "message" in response and response["message"] == "No pending txn":
                assert response["message"] == "No pending txn"
            elif "block" in response:
                assert response["type"] == "new_block"
                assert "block" in response

@pytest.mark.asyncio
async def test_get_chain():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/chain")
        assert response.status_code == 200
        assert "chain" in response.json()
        assert "length" in response.json()
        assert "is_valid" in response.json()
