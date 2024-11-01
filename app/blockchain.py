import datetime
import hashlib
import json
import copy
from typing import Dict, List



class Blockchain:
    def __init__(self):
        self.chain: List[Dict] = []
        self.difficulty = '00000'
        self.transactions: List[Dict] = []
        self.pending_transactions: List[Dict] = []
        self.balances: Dict[str, float] = dict()
        self.genesis_block()
        self.peer_b = copy.deepcopy(self.chain)
        self.mining_reward = 50  

    def genesis_block(self) -> None:
        print("Creating a Genisis Block")
        block = self.create_block(balances=dict(), previous_hash='0'*64)
        self.chain.append(block)

    def create_block(self, balances: Dict[str, float], previous_hash: str) -> Dict:
        print("Creating New Block with Previous Hash")

        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'transactions': copy.deepcopy(self.transactions),
            'balances': copy.deepcopy(balances),
            'previous_hash': previous_hash,
            'merkle_root': self.calculate_merkle_root(),  
            'version': '1.0',  
        }

        nonce, hash = self.hash(block)
        block['nonce'] = nonce
        block['hash'] = hash
        
       
        self.transactions = []
        self.balances = dict()
        return block
    
    def clear_pending_transactions(self):
        self.transactions: List[Dict] = []
        self.pending_transactions: List[Dict] = []


    def get_current_balances(self) -> Dict[str, float]:
        if not self.chain:
            return {}
        return copy.deepcopy(self.chain[-1].get('balances', {}))
    
    def create_block_with_transactions(self, transactions: List[Dict],miner) -> Dict:
 
        print("Creating New Block with Transactions")
        
      
        previous_hash = self.chain[-1]['hash'] if self.chain else '0'*64
        
        print(previous_hash
              )
        
        tx=copy.deepcopy(transactions)
  
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'transactions': copy.deepcopy(transactions),
            # 'balances': new_balances,
            'balances':{
                miner: self.mining_reward
                },
            'previous_hash': previous_hash,
            'merkle_root': self.calculate_merkle_root_for_block(tx),
            'version': '1.0',
        }
        
        nonce, hash = self.hash(block)
        block['nonce'] = nonce
        block['hash'] = hash
        
        return block
    
    def hash(self, block: Dict) -> tuple:
        print("Hashing and Finding Nanunce")
        encoded_block = json.dumps(block, sort_keys=True).encode()
        nonce = 0
        while True:
            hash_operation = hashlib.sha256(encoded_block + str(nonce).encode()).hexdigest()
            if hash_operation[:len(self.difficulty)] == self.difficulty:
                break
            nonce += 1
        return nonce, hash_operation

    def calculate_merkle_root(self) -> str:
    
        if not self.transactions:
            print("txn not found so creating from exmpty")
            return hashlib.sha256(''.encode()).hexdigest()
        
        hash_list = [hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest() 
                    for tx in self.transactions]
        
        while len(hash_list) > 1:
            if len(hash_list) % 2 != 0:
                hash_list.append(hash_list[-1])
            hash_list = [hashlib.sha256((hash_list[i] + hash_list[i+1]).encode()).hexdigest()   
                        for i in range(0, len(hash_list), 2)]
        print("Final Mekkal ROot Hash",hash_list)
        return hash_list[0]

    def get_previous_block(self) -> Dict:
        print("Getting Previous Hash")
        return self.chain[-1]
    
    
    def add_transaction(self, sender: str, receiver: str, amount: float) -> int:
        print("Adding Txn in Pending ")
        transaction = {
            'sender': sender,
            'receiver': receiver,
            'amount': amount,
            'timestamp': str(datetime.datetime.now()),
            'signature': ''  #TODO Adding Sign
        }
        print(transaction)
        
        if self.validate_transaction(transaction):
            self.transactions.append(transaction)
            self.pending_transactions.append(transaction)
            previous_block = self.get_previous_block()
            return previous_block['index'] + 1
        return -1

    def validate_transaction(self, transaction: Dict) -> bool:
        print("Validating the txn")
      
        sender_balance = self.get_balance(transaction['sender'])
        sender_pending = self.get_pending_outgoing_amount(transaction['sender'])

        available_balance = sender_balance - sender_pending

        if transaction['amount'] > available_balance:
            return False
        
        if transaction['amount'] <= 0:
            return False
            
        return True

    def get_balance(self, address: str) -> (float):
        print("Find the Balance of user")
        balance = 0
     
        for block in self.chain:
      
            if address in block['balances']:
                balance += block['balances'][address]
                
            for tx in block['transactions']:
                if tx['sender'] == address:
                    balance -= tx['amount']
                if tx['receiver'] == address:
                    balance += tx['amount']
        
        return balance
    
    def get_pending_outgoing_amount(self, address: str) -> float:

        try:
             pending_amount = sum(
                 tx['amount'] for tx in self.pending_transactions 
                 if tx['sender'] == address
              )
             return pending_amount
        except Exception as e:
               print(f"Error calculating pending amount: {str(e)}")
               return 0.0

    def add_balance(self, receiver: str, amount: float) -> int:
         print("Adding balance to an address")
    
         previous_block = self.get_previous_block()
         print(previous_block)

         if 'balances' not in previous_block:
             previous_block['balances'] = {}
    
         if receiver not in previous_block['balances']:

              previous_block['balances'][receiver] = 0
    
         previous_block['balances'][receiver] += amount
         return (previous_block['balances'])
    

    def is_chain_valid(self) -> bool:
        print("Checking Chain Validation")
        previous_block = self.chain[0]
        block_index = 1
       
        print("Start Peer")
        print(self.peer_b)
        print("End Peer") 
        
    
        while block_index < len(self.chain):
            block = self.chain[block_index]
            print("Block =",block)

            if block['previous_hash'] != previous_block['hash']:
                return False
            
            #print("Comparing With Peer Copy ! like multiples chain maintners")
                    # if block['hash'] != self.peer_b[block_index]['hash']:   
            #     return False

          
            if block['hash'][:len(self.difficulty)] != self.difficulty:
                return False

            calculated_merkle = self.calculate_merkle_root_for_block(block['transactions'])
            
            if block['merkle_root'] != calculated_merkle:
                     print(f"Invalid merkle root at block {block_index}")
                     print(f"Stored: {block['merkle_root']}")
                     print(f"Calculated: {calculated_merkle}")
                     return False
            

            if block['merkle_root'] != calculated_merkle:
                return False

            previous_block = block
            block_index += 1
            
        return True
    
    def calculate_merkle_root_for_block(self, transactions: List[Dict]) -> str:
 
        if not transactions:
            return hashlib.sha256(''.encode()).hexdigest()
    
        hash_list = [
            hashlib.sha256(
                json.dumps(tx, sort_keys=True).encode()
            ).hexdigest() 
            for tx in transactions
        ]
    
        print("Initial transaction hashes:")
        for i, h in enumerate(hash_list):
            print(f"Tx {i}: {h}")
        while len(hash_list) > 1:
            print(f"Current hash list length: {len(hash_list)}")
            if len(hash_list) % 2 != 0:
                hash_list.append(hash_list[-1])
                print("Added duplicate of last hash for even number")
        
            new_hash_list = []
            for i in range(0, len(hash_list), 2):
                combined = hash_list[i] + hash_list[i+1]
                new_hash = hashlib.sha256(combined.encode()).hexdigest()
                new_hash_list.append(new_hash)
                print(f"Combined {hash_list[i][:8]}... + {hash_list[i+1][:8]}... = {new_hash[:8]}...")
        
            hash_list = new_hash_list
    
        print(f"Final merkle root: {hash_list[0]}")
        return hash_list[0]


    def is_valid_block(self, block: Dict) -> bool:
     print("Validating Block Before adding to Chain")
 
     prev_block = self.get_previous_block()
     if block['previous_hash'] != prev_block['hash']:
        return False
        
     print("Verfying Proof Of work i.e 00000")
     if block['hash'][:len(self.difficulty)] != self.difficulty:
            return False
        
   
     for tx in block['transactions']:
            if not self.validate_transaction(tx):
                return False
            
     return True

    def get_pending_transactions(self) -> List[Dict]:
        print("Getting Pending Txn")
        print(self.pending_transactions)
        return self.pending_transactions
    

    def remove_pending_transaction(self, transaction: Dict) -> None:
        print("Adding txn in Block rempving from Prnding")
        if transaction in self.pending_transactions:
            self.pending_transactions.remove(transaction)


    def resolve_conflicts(self, new_chain: List[Dict]) -> bool:
        print("Resolve Longer chain")
        if len(new_chain) <= len(self.chain):
           return False
        

        for i in range(1, len(new_chain)):
          if not self.is_valid_block(new_chain[i]):
              print("Chain not valid")
              return False

        print("Accepting New Chain")
        self.chain = new_chain
        return True
    
