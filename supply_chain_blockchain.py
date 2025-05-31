import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid
import requests
from urllib.parse import urlparse
from auth import AuthenticationSystem
from supply_chain_model import validate_transaction, transaction_factory


class SupplyChainBlockchain:
    def __init__(self):
        # Initialize blockchain attributes
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        self.auth_system = AuthenticationSystem()
        
        # Create a dictionary to track products
        self.products = {}  # product_id -> details
        
        # Create the genesis block
        self.new_block(previous_hash=1, proof=100)

    def register_node(self, address: str) -> None:
        """
        Add a new node to the list of nodes
        
        :param address: Address of the node. Eg. 'http://192.168.0.5:5000'
        :return: None
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain: List[Dict[str, Any]]) -> bool:
        """
        Determine if a given blockchain is valid
        
        :param chain: A blockchain
        :return: True if valid, False if not
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self) -> bool:
        """
        This is our Consensus Algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        
        :return: True if our chain was replaced, False if not
        """
        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, proof: int, previous_hash=None) -> Dict[str, Any]:
        """
        Create a new Block in the Blockchain
        
        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': datetime.now().isoformat(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender: str, transaction_type: str, data: Dict[str, Any], signature: str) -> int:
        """
        Creates a new transaction to go into the next mined Block
        
        :param sender: Identity of the sender (username or public key)
        :param transaction_type: Type of transaction (e.g., "product_registration", "processing", "transfer")
        :param data: Transaction-specific data
        :param signature: Cryptographic signature of the data
        :return: The index of the Block that will hold this transaction
        """
        # Get sender's public key from our auth system
        sender_info = self.auth_system.get_user_info(sender)
        if not sender_info:
            raise ValueError(f"Unknown sender: {sender}")
        
        # Verify the signature
        if not self.auth_system.verify_signature(sender_info['public_key'], data, signature):
            raise ValueError("Invalid signature")
        
        # Validate transaction data based on its type
        if not validate_transaction(transaction_type, data):
            raise ValueError(f"Invalid {transaction_type} transaction data")
        
        # Process specific transaction types
        if transaction_type == "product_registration":
            product_id = data.get('product_id')
            if product_id in self.products:
                raise ValueError(f"Product ID {product_id} already exists")
            self.products[product_id] = {
                'registered_by': sender,
                'registration_time': datetime.now().isoformat(),
                'current_owner': sender,
                'history': []
            }
        
        elif transaction_type == "transfer":
            product_id = data.get('product_id')
            if product_id not in self.products:
                raise ValueError(f"Unknown product ID: {product_id}")
            
            if self.products[product_id]['current_owner'] != sender:
                raise ValueError(f"Sender {sender} does not own product {product_id}")
            
            # Update ownership
            self.products[product_id]['current_owner'] = data.get('recipient_id')
            self.products[product_id]['history'].append({
                'transaction_type': 'transfer',
                'timestamp': datetime.now().isoformat(),
                'from': sender,
                'to': data.get('recipient_id')
            })
        
        # Create the transaction
        transaction = {
            'sender': sender,
            'transaction_type': transaction_type,
            'data': transaction_factory(transaction_type, data),
            'timestamp': datetime.now().isoformat(),
            'signature': signature,
            'transaction_id': str(uuid.uuid4()).replace('-', '')
        }
        
        self.current_transactions.append(transaction)

        return self.last_block['index'] + 1

    def get_product_history(self, product_id: str) -> List[Dict[str, Any]]:
        """
        Get the complete history of a product from the blockchain
        
        :param product_id: ID of the product
        :return: List of transactions related to this product
        """
        if product_id not in self.products:
            raise ValueError(f"Unknown product ID: {product_id}")
        
        history = []
        
        # Scan the entire blockchain for transactions related to this product
        for block in self.chain:
            for tx in block['transactions']:
                if tx.get('transaction_type') in ['product_registration', 'processing', 'transfer', 'quality_check', 'retail']:
                    if tx.get('data', {}).get('product_id') == product_id:
                        history.append({
                            'block_index': block['index'],
                            'timestamp': tx['timestamp'],
                            'transaction_type': tx['transaction_type'],
                            'transaction_id': tx['transaction_id'],
                            'data': tx['data']
                        })
        
        return sorted(history, key=lambda x: x['timestamp'])

    def verify_product_authenticity(self, product_id: str) -> Dict[str, Any]:
        """
        Verify that a product is authentic and its history is valid
        
        :param product_id: ID of the product
        :return: Verification result
        """
        try:
            history = self.get_product_history(product_id)
            
            # Check if the product exists and has a registration event
            if not history or history[0]['transaction_type'] != 'product_registration':
                return {
                    'authentic': False,
                    'reason': 'Product not properly registered'
                }
            
            # Check if the chain of custody is continuous
            current_owner = history[0]['data']['producer_id']
            for event in history[1:]:
                if event['transaction_type'] == 'transfer':
                    # Check if the sender in this transfer matches the current owner
                    if event['data']['sender_id'] != current_owner:
                        return {
                            'authentic': False,
                            'reason': 'Chain of custody broken'
                        }
                    current_owner = event['data']['recipient_id']
            
            # All checks passed
            return {
                'authentic': True,
                'product_id': product_id,
                'history_length': len(history),
                'registration_date': history[0]['timestamp'],
                'current_owner': self.products[product_id]['current_owner']
            }
            
        except Exception as e:
            return {
                'authentic': False,
                'reason': str(e)
            }

    @property
    def last_block(self) -> Dict[str, Any]:
        """
        Returns the last Block in the chain
        
        :return: Last block
        """
        return self.chain[-1]

    @staticmethod
    def hash(block: Dict[str, Any]) -> str:
        """
        Creates a SHA-256 hash of a Block
        
        :param block: Block
        :return: Hash string
        """
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof: int) -> int:
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
         - p is the previous proof, and p' is the new proof
         
        :param last_proof: <int>
        :return: <int>
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof: int, proof: int) -> bool:
        """
        Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?
        
        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :return: <bool> True if correct, False if not.
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"
