from typing import Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
import random
import datetime
import os
import constants
from connectionManager import ConnectionManager
from schemas import TransactionRequest,BalanceRequest
from contextlib import asynccontextmanager
from blockchain import Blockchain
from typing import Dict

class MyFastAPI(FastAPI):
    blockchain: Optional[Blockchain] = None
    manager: Optional[ConnectionManager] = None


@asynccontextmanager
async def lifespan(app: MyFastAPI):
    try:
         constants.print_with_style()

         app.blockchain = Blockchain()
         app.manager = ConnectionManager()

         print("Visit: http://127.0.0.1:8000 for API")
         print("Visit: http://127.0.0.1:8000/docs for API documentation.")
         print()  
         yield 
    finally:
             print("\n🛑 Shutting down FastChain server...")


app = MyFastAPI(
    title="FastChain",
    description="A lightweight blockchain implementation with WebSocket-based miner network",
    version="1.0.0",
    lifespan=lifespan
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
            "POST /transaction": {
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
            data = await websocket.receive_json()
            print("Ws message: ",data)
            
            if data["type"] == "new_block":
                async with app.manager.mining_lock:
                    print("Handelling new block first removing pending and broadcasting")
                    block = data["block"]
                    if app.blockchain.is_valid_block(block):
                        app.blockchain.chain.append(block)
                        for tx in block['transactions']:
                            app.blockchain.remove_pending_transaction(tx)
                        await app.manager.broadcast({
                            "type": "new_block",
                            "block": block
                        })
                        
            elif data["type"] == "chain_update":
                new_chain = data["chain"]
                if app.blockchain.resolve_conflicts(new_chain):
                    await app.manager.broadcast({
                        "type": "chain_update",
                        "chain": app.blockchain.chain
                    })

            elif data["type"] == "mine":
                async with app.manager.mining_lock:
                     if not app.blockchain.is_chain_valid():
                        await websocket.send_json({"message":"Blockchain Not Valid"})
                        return
                     
                     transactions = app.blockchain.get_pending_transactions()

                     print(transactions)

                     if not transactions:
                       await websocket.send_json({
                            "message":"No pending txn"
                        })
                       return
                     
                     print("Creating New BLock")
                     

                     block = app.blockchain.create_block_with_transactions(transactions,miner=data["miner"])
        
                     if not app.blockchain.is_valid_block(block):
                       await websocket.send_json({
                           "message":"invalid block"
                       })
                       return
        
                     app.blockchain.chain.append(block)

                     app.blockchain.clear_pending_transactions()
        
                     await app.manager.broadcast({
                         "type":"new_block",
                         "block":block
                     })

                    
    except Exception as e:
        return {
            "message":"Error",
            "Error":e
        }
    except WebSocketDisconnect:
        app.manager.disconnect(websocket=websocket)
    finally:
        print("Socket CLosed")


@app.get('/chain')
async def get_chain():
    return {
        'chain': app.blockchain.chain,
        'length': len(app.blockchain.chain),
        'is_valid': app.blockchain.is_chain_valid()
    }


@app.get('/peer')
async def get_peer():
    return {
        'chain': app.blockchain.peer_b,
        'length': len(app.blockchain.peer_b),
    }



@app.post('/txn')
async def add_transaction(transaction: TransactionRequest):
    try:
        data = transaction.model_dump()
        print("Adding txn",data)
    
        if data['sender'] == data['receiver']:
            raise HTTPException(status_code=400, detail="Sender cannot be same as receiver")
    
        if data['amount'] <= 0:
          raise HTTPException(status_code=400, detail="Amount must be positive")
    
        sender_balance = app.blockchain.get_balance(data['sender'])

        if sender_balance < data['amount']:
           raise HTTPException(status_code=400, detail="Insufficient balance")
    

        
        app.blockchain.add_transaction(data["sender"],data["receiver"],data["amount"])
    
        return {
            'message': 'Transaction added to pending pool',
           'transaction': data
        }
  
    except Exception as e:
        print("Error",e)
        return e


    


@app.get('/pending')
async def get_pending_transactions():
    return {
        'pending_transactions': app.blockchain.get_pending_transactions(),
        'count': len(app.blockchain.get_pending_transactions())
    }


@app.get('/balance/{address}')
async def get_balance(address: str):
    balance = app.blockchain.get_balance(address)

    if (balance == 0):
        return {
            "Message USer Donest Exists"
        }

    return {
        'address': address,
        'balance': balance
    }


@app.get('/hack')
async def hack_block():
    # if not app.debug:
    #     raise HTTPException(status_code=404)
        
    block_id = random.randint(1, len(app.blockchain.chain)-1)
    block = app.blockchain.chain[block_id]
    
    block['timestamp'] = str(datetime.datetime.now())
    block['hash'] = app.blockchain.hash(block)
    app.blockchain.chain[block_id] = block
    
    return {
        'message': 'Block hacked for testing',
        'block': block
    }

@app.post("/add")
async def add_money(data:BalanceRequest):
        req = data.model_dump()

        if(not req["receiver"]):
           return
        if (not req["amount"]):
            return
        
        res:Dict[str , float] =  app.blockchain.add_balance(req["receiver"], amount=req["amount"])

        return res
            
        
       
    