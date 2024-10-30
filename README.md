# FastChain-A-Lightweight-Python-Blockchain-with-WebSocket-based-Miner-Network

Createating a simple Bitcoin like server that has the following components -

Central server - A central websocket server that all miners connect to to exchange messages
Miner server -
Code that miners can run to be able to create blocks, do proof of work, broadcast the block via the central server.
Code that verifies the signature, balances and creates / adds a block
Code should reject smaller blockchains/erronours blocks
Should be able to catch up to the blockchain when the server starts
