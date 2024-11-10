import json
from typing import Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect,Response, status

import random
import datetime

from app import constants
from app.blockchain import Blockchain
from contextlib import asynccontextmanager
from typing import Dict
from fastapi.middleware.cors import CORSMiddleware

from app.connectionManager import ConnectionManager
from app.schemas import BalanceRequest, TransactionRequest

class MyFastAPI(FastAPI):
    blockchain: Optional[Blockchain] = None
    manager: Optional[ConnectionManager] = None


@asynccontextmanager
async def lifespan(app:  MyFastAPI):
    try:
         constants.print_with_style()

         app.blockchain = Blockchain()
         app.manager = ConnectionManager()

         print("Visit: http://127.0.0.1:3080 for API")
         print("Visit: http://127.0.0.1:3080/docs for API documentation.")
         print()  
         yield 
    finally:
             print("\n🛑 Shutting down FastChain server...")


app = MyFastAPI(
    title="FastChain",
    description="A lightweight blockchain implementation with WebSocket-based miner network",
    version="1.0.0",
    lifespan=lifespan,
    root_path="/chain"
)   
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
async def root():

    return {
        "endpoints": {
            "view_blockchain": {
                "description": "See all confirmed transactions",
                "endpoint": "GET /chain"
            },
            "send_coins": {
                "description": "Transfer coins to another address",
                "endpoint": "POST /transaction",
                "note": "Requires sender address, receiver address, and amount"
            },
            "check_balance": {
                "description": "View your current balance",
                "endpoint": "GET /balance/{address}",
                "note": "Replace {address} with your blockchain address"
            },
            "pending_transactions": {
                "description": "View transactions waiting to be processed",
                "endpoint": "GET /pending"
            },
            "mine": {
                "description": "Connect as a miner to process transactions",
                "endpoint": "WS /ws/miner"
            }
        },
    }

@app.get("/dev")
async def get_dev():

    chain_length = len(app.blockchain.chain)
    last_block = app.blockchain.get_previous_block()
    pending_count = len(app.blockchain.get_pending_transactions())

    return {
        "status": {
            "blockchain": {
                "blocks": chain_length,
                "latest_block_index": last_block['index'],
                "latest_block_hash": last_block['hash'][:10] + "...",  
                "mining_difficulty": app.blockchain.difficulty,
                "pending_transactions": pending_count
            },
            "network": {
                "active_miners": len(app.manager.active_connections),
                "mining_reward": app.blockchain.mining_reward
            }
        },
        "api": {
            "name": "FastChain",
            "version": "1.0.0",
            "description": "Lightweight blockchain with WebSocket-based miner network"
        },
        "endpoints": {
            "GET /": {
                "description": "Get system status and API information",
                "requires_auth": False
            },
            "GET /chain": {
                "description": "Get full blockchain data and validation status",
                "returns": "Chain data with length and validity status",
                "requires_auth": False
            },
            "GET /mine": {
                "description": "Mine a new block with pending transactions",
                "requires_pending": True,
                "returns": "Newly mined block data",
                "requires_auth": False
            },
            "POST /txn": {
                "description": "Add new transaction to pending pool",
                "required_fields": ["sender", "receiver", "amount"],
                "validation": "Checks sender balance and transaction validity",
                "requires_auth": False
            },
            "GET /pending": {
                "description": "Get list of pending transactions",
                "returns": "Array of pending transactions with count",
                "requires_auth": False
            },
            "GET /balance/{address}": {
                "description": "Get current balance for an address",
                "parameter": "address: string",
                "returns": "Current balance for the address",
                "requires_auth": False
            },
            "WS /ws/miner": {
                "description": "WebSocket connection for miners",
                "protocol": "WebSocket",
                "events": {
                    "chain_update": "Receive full chain updates",
                    "new_block": "Receive/broadcast new blocks"
                },
                "requires_auth": False
            }
        }
    }





@app.websocket("/ws/miner")
async def websocket_endpoint(websocket: WebSocket):
    await app.manager.connect(websocket)
    try:
        await websocket.send_json({
            "type": "chain_update",
            "chain": app.blockchain.chain
        })
        
        while True:
            try:
                data = await websocket.receive_json()
                print("Ws message: ",data)
                
                if data["type"] == "new_block":
                    async with app.manager.mining_lock:
                        print("Handling new block first removing pending and broadcasting")
                        block = data["block"]
                        if not block:
                            await websocket.send_json({
                                "status": "error",
                                "message": "Invalid block data received"
                            })
                            continue
                            
                        if app.blockchain.is_valid_block(block):
                            app.blockchain.chain.append(block)
                            for tx in block['transactions']:
                                app.blockchain.remove_pending_transaction(tx)
                            await app.manager.broadcast({
                                "type": "new_block",
                                "block": block
                            })
                        else:
                            await websocket.send_json({
                                "status": "error",
                                "message": "Invalid block structure"
                            })
                            
                elif data["type"] == "chain_update":
                    new_chain = data["chain"]
                    if not new_chain:
                        await websocket.send_json({
                            "status": "error",
                            "message": "Invalid chain data received"
                        })
                        continue
                        
                    if app.blockchain.resolve_conflicts(new_chain):
                        await app.manager.broadcast({
                            "type": "chain_update",
                            "chain": app.blockchain.chain
                        })
                    else:
                        await websocket.send_json({
                            "status": "error",
                            "message": "Chain resolution failed"
                        })

                elif data["type"] == "mine":
                    async with app.manager.mining_lock:
                        if not app.blockchain.is_chain_valid():
                            await websocket.send_json({
                                "status": "error",
                                "message": "Blockchain Not Valid"
                            })
                            continue
                         
                        transactions = app.blockchain.get_pending_transactions()
                        print(transactions)

                        if not transactions:
                            await websocket.send_json({
                                "status": "error",
                                "message": "No pending transactions"
                            })
                            continue
                         
                        print("Creating New Block")
                        if "miner" not in data:
                            await websocket.send_json({
                                "status": "error",
                                "message": "Miner address not provided"
                            })
                            continue

                        block = app.blockchain.create_block_with_transactions(transactions, miner=data["miner"])
            
                        if not app.blockchain.is_valid_block(block):
                            await websocket.send_json({
                                "status": "error",
                                "message": "Invalid block created"
                            })
                            continue
            
                        app.blockchain.chain.append(block)
                        app.blockchain.clear_pending_transactions()
            
                        await app.manager.broadcast({
                            "type": "new_block",
                            "block": block
                        })
                        
            except json.JSONDecodeError:
                await websocket.send_json({
                    "status": "error",
                    "message": "Invalid JSON data received"
                })
            except KeyError as e:
                await websocket.send_json({
                    "status": "error",
                    "message": f"Missing required field: {str(e)}"
                })
            except Exception as e:
                await websocket.send_json({
                    "status": "error",
                    "message": f"Operation failed: {str(e)}"
                })
                
    except WebSocketDisconnect:
        app.manager.disconnect(websocket=websocket)
    finally:
        print("Socket Closed")

@app.get("/mine")
async def mine_api(miner: str, response: Response):
    if not miner:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "status": "error",
            "message": "Miner address not provided"
        }

    if not app.blockchain.is_chain_valid():
        response.status_code = status.HTTP_406_NOT_ACCEPTABLE
        return {
            "status": "error",
            "message": "Blockchain not valid"
        }

    transactions = app.blockchain.get_pending_transactions()
    if not transactions:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "status": "error",
            "message": "No pending transactions"
        }

    try:
        print("Creating New Block")
        block = app.blockchain.create_block_with_transactions(transactions, miner=miner)

        if not app.blockchain.is_valid_block(block):
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {
                "status": "error",
                "message": "Invalid block created"
            }

        app.blockchain.chain.append(block)
        app.blockchain.clear_pending_transactions()

        app.manager.broadcast({
            "type": "new_block",
            "block": block
        })

        return {
            "status": "success",
            "message": "Block mined successfully",
            "miner": miner,
            "block": block
        }
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {
            "status": "error",
            "message": f"Mining operation failed: {str(e)}"
        }

@app.get('/chain')
async def get_chain():
    try:
        return {
            'status': 'success',
            'chain': app.blockchain.chain,
            'length': len(app.blockchain.chain),
            'is_valid': app.blockchain.is_chain_valid()
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f"Failed to retrieve chain: {str(e)}"
        }

@app.get('/peer')
async def get_peer():
    try:
        return {
            'status': 'success',
            'chain': app.blockchain.peer_b,
            'length': len(app.blockchain.peer_b)
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f"Failed to retrieve peer data: {str(e)}"
        }

@app.post('/txn')
async def add_transaction(transaction: TransactionRequest, response: Response):
    try:
        data = transaction.model_dump()
        print("Adding txn", data)
    
        if data['sender'] == data['receiver']:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {
                'status': 'error',
                'message': 'Sender cannot be same as receiver'
            }
    
        if data['amount'] <= 0:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {
                'status': 'error',
                'message': 'Amount must be positive'
            }
    
        sender_balance = app.blockchain.get_balance(data['sender'])
        
        if sender_balance < data['amount']:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {
                'status': 'error',
                'message': 'Insufficient balance'
            }
    
        app.blockchain.add_transaction(data["sender"], data["receiver"], data["amount"])
    
        return {
            'status': 'success',
            'message': 'Transaction added to pending pool',
            'transaction': data
        }
  
    except Exception as e:
        print("Error", e)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {
            'status': 'error',
            'message': f'Failed to add transaction: {str(e)}'
        }

@app.get('/pending')
async def get_pending_transactions():
    try:
        pending_txns = app.blockchain.get_pending_transactions()
        return {
            'status': 'success',
            'pending_transactions': pending_txns,
            'count': len(pending_txns)
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Failed to retrieve pending transactions: {str(e)}'
        }

@app.get('/balance/{address}')
async def get_balance(address: str, response: Response):
    try:
        if not address:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {
                'status': 'error',
                'message': 'Address not provided'
            }

        balance = app.blockchain.get_balance(address)
        if balance == 0:
            return {
                'status': 'success',
                'message': 'User does not exist or has zero balance',
                'address': address,
                'balance': 0
            }

        return {
            'status': 'success',
            'address': address,
            'balance': balance
        }
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {
            'status': 'error',
            'message': f'Failed to retrieve balance: {str(e)}'
        }

@app.get('/hack')
async def hack_block(passwd:str):
    try:
        if  passwd != "hackit":
            return {
                'status': 'error',
                'message': 'Wrong   provided ?passwd="....'
            }
        chain_length = len(app.blockchain.chain)
        
        if(chain_length <= 1):
            return {
                'message': 'Starting Chain cant be hacked'
            }
            
            
        block_id = random.randint(1, len(app.blockchain.chain)-1)
        block = app.blockchain.chain[block_id]
        
        block['timestamp'] = str(datetime.datetime.now())
        block['hash'] = app.blockchain.hash(block)
        app.blockchain.chain[block_id] = block
        
        return {
            'status': 'success',
            'message': 'Block hacked for testing',
            'block': block
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Failed to hack block: {str(e)}'
        }

@app.post("/add")
async def add_money(data: BalanceRequest, response: Response):
    try:
        req = data.model_dump()

        if not req["receiver"]:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {
                'status': 'error',
                'message': 'Receiver address not provided'
            }
            
        if not req["amount"]:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {
                'status': 'error',
                'message': 'Amount not provided'
            }
        
        res = app.blockchain.add_balance(req["receiver"], amount=req["amount"])
        
        return {
            'status': 'success',
            'message': 'Balance added successfully',
            'data': res
        }
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {
            'status': 'error',
            'message': f'Failed to add balance: {str(e)}'
        }
