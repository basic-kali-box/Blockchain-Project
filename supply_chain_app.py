from flask import Flask, jsonify, request, render_template, redirect, url_for, session
import uuid
import json
from supply_chain_blockchain import SupplyChainBlockchain
from auth import AuthenticationSystem

# Instantiate our Node
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = str(uuid.uuid4())  # For session management

# Generate a globally unique address for this node
node_identifier = str(uuid.uuid4()).replace('-', '')

# Instantiate the Blockchain and Authentication System
blockchain = SupplyChainBlockchain()
auth_system = blockchain.auth_system  # Use the one from blockchain to ensure consistency

# In-memory storage for demo purposes - in a real app, use a database
demo_users = {}

# Routes for the blockchain API

@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new block.
    # Since regular transactions require a valid signature, we handle mining specially
    blockchain.current_transactions.append({
        'sender': "0",
        'transaction_type': "mining",
        'data': {"message": "Mining reward"},
        'timestamp': blockchain.chain[-1]['timestamp'],
        'signature': "MINING_TRANSACTION",
        'transaction_id': str(uuid.uuid4()).replace('-', '')
    })

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'transaction_type', 'data', 'signature']
    if not all(k in values for k in required):
        return jsonify({'error': 'Missing values'}), 400

    try:
        # Create a new Transaction
        index = blockchain.new_transaction(
            values['sender'], 
            values['transaction_type'], 
            values['data'], 
            values['signature']
        )

        response = {'message': f'Transaction will be added to Block {index}'}
        return jsonify(response), 201
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


# Routes for supply chain functionality

@app.route('/products/<product_id>/history', methods=['GET'])
def product_history(product_id):
    """Get the complete history of a product"""
    try:
        history = blockchain.get_product_history(product_id)
        return jsonify({'product_id': product_id, 'history': history}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@app.route('/products/<product_id>/verify', methods=['GET'])
def verify_product(product_id):
    """Verify the authenticity of a product"""
    result = blockchain.verify_product_authenticity(product_id)
    if result['authentic']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@app.route('/users/register', methods=['POST'])
def register_user():
    """Register a new user with the system"""
    values = request.get_json()
    
    required = ['username', 'role', 'organization']
    if not all(k in values for k in required):
        return jsonify({'error': 'Missing values'}), 400
    
    try:
        # Generate a key pair for the new user
        private_key, public_key = auth_system.generate_key_pair()
        
        # Register the user
        user_id = auth_system.register_user(
            values['username'],
            public_key,
            values['role'],
            values['organization']
        )
        
        # Store keys for demo purposes - in a real app, private key would be sent securely to the user
        demo_users[values['username']] = {
            'private_key': private_key,
            'public_key': public_key,
            'user_id': user_id
        }
        
        return jsonify({
            'message': 'User registered successfully',
            'username': values['username'],
            'user_id': user_id,
            'public_key': public_key,
            'private_key': private_key  # In a real app, NEVER return the private key!
        }), 201
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/users/<username>/info', methods=['GET'])
def user_info(username):
    """Get information about a registered user"""
    user_info = auth_system.get_user_info(username)
    if user_info:
        return jsonify(user_info), 200
    else:
        return jsonify({'error': f'User {username} not found'}), 404


@app.route('/sign', methods=['POST'])
def sign_data():
    """Sign data with a user's private key (demo only)"""
    values = request.get_json()
    
    required = ['username', 'data']
    if not all(k in values for k in required):
        return jsonify({'error': 'Missing values'}), 400
    
    username = values['username']
    data = values['data']
    
    if username not in demo_users:
        return jsonify({'error': f'User {username} not found'}), 404
    
    try:
        signature = auth_system.sign_data(demo_users[username]['private_key'], data)
        return jsonify({'signature': signature}), 200
    except Exception as e:
        return jsonify({'error': f'Signing error: {str(e)}'}), 500


# Web UI routes

@app.route('/')
def index():
    """Render the homepage"""
    return render_template('index.html')


@app.route('/ui/register', methods=['GET', 'POST'])
def ui_register():
    """User registration page"""
    if request.method == 'POST':
        username = request.form.get('username')
        role = request.form.get('role')
        organization = request.form.get('organization')
        
        if not all([username, role, organization]):
            return render_template('register.html', error="All fields are required")
        
        try:
            # Generate a key pair for the new user
            private_key, public_key = auth_system.generate_key_pair()
            
            # Register the user
            user_id = auth_system.register_user(
                username,
                public_key,
                role,
                organization
            )
            
            # Store keys for demo purposes
            demo_users[username] = {
                'private_key': private_key,
                'public_key': public_key,
                'user_id': user_id
            }
            
            session['username'] = username
            return redirect(url_for('ui_dashboard'))
        
        except ValueError as e:
            return render_template('register.html', error=str(e))
    
    return render_template('register.html')


@app.route('/ui/dashboard')
def ui_dashboard():
    """User dashboard"""
    username = session.get('username')
    if not username:
        return redirect(url_for('ui_login'))
    
    user_info = auth_system.get_user_info(username)
    demo_info = demo_users.get(username, {})
    
    return render_template('dashboard.html', 
                           user_info=user_info, 
                           demo_info=demo_info, 
                           blockchain_length=len(blockchain.chain))


@app.route('/ui/login', methods=['GET', 'POST'])
def ui_login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        
        if not username or username not in demo_users:
            return render_template('login.html', error="Invalid username")
        
        session['username'] = username
        return redirect(url_for('ui_dashboard'))
    
    return render_template('login.html')


@app.route('/ui/logout')
def ui_logout():
    """Logout"""
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/ui/register_product', methods=['GET', 'POST'])
def ui_register_product():
    """Register a new product"""
    username = session.get('username')
    if not username:
        return redirect(url_for('ui_login'))
    
    if request.method == 'POST':
        try:
            data = {
                'product_id': request.form.get('product_id'),
                'name': request.form.get('name'),
                'description': request.form.get('description'),
                'category': request.form.get('category'),
                'producer_id': username,
                'production_date': request.form.get('production_date'),
                'batch_number': request.form.get('batch_number'),
                'origin_location': {
                    'latitude': float(request.form.get('latitude')),
                    'longitude': float(request.form.get('longitude')),
                    'address': request.form.get('address'),
                    'country': request.form.get('country'),
                    'region': request.form.get('region')
                },
                'certifications': [],
                'additional_info': {}
            }
            
            # Add certifications if provided
            cert_type = request.form.get('certification_type')
            if cert_type:
                data['certifications'].append({
                    'certification_type': cert_type,
                    'issuer': request.form.get('certification_issuer', 'Self'),
                    'issue_date': request.form.get('certification_date', data['production_date']),
                    'expiry_date': request.form.get('certification_expiry', '2030-01-01'),
                    'certification_id': f"cert-{uuid.uuid4().hex[:8]}",
                    'additional_info': {}
                })
            
            # Sign the data
            signature = auth_system.sign_data(demo_users[username]['private_key'], data)
            
            # Create the transaction
            blockchain.new_transaction(
                username,
                'product_registration',
                data,
                signature
            )
            
            # Mine a block to include this transaction
            last_block = blockchain.last_block
            last_proof = last_block['proof']
            proof = blockchain.proof_of_work(last_proof)
            previous_hash = blockchain.hash(last_block)
            block = blockchain.new_block(proof, previous_hash)
            
            return render_template('product_registered.html', product_id=data['product_id'])
        
        except Exception as e:
            return render_template('register_product.html', error=str(e))
    
    return render_template('register_product.html')


@app.route('/ui/transfer_product', methods=['GET', 'POST'])
def ui_transfer_product():
    """Transfer a product to another user"""
    username = session.get('username')
    if not username:
        return redirect(url_for('ui_login'))
    
    if request.method == 'POST':
        try:
            data = {
                'transfer_id': f"tx-{uuid.uuid4().hex[:8]}",
                'product_id': request.form.get('product_id'),
                'sender_id': username,
                'sender_type': auth_system.get_user_info(username)['role'],
                'recipient_id': request.form.get('recipient'),
                'recipient_type': auth_system.get_user_info(request.form.get('recipient'))['role'],
                'timestamp': datetime.now().isoformat(),
                'departure_location': {
                    'latitude': float(request.form.get('latitude')),
                    'longitude': float(request.form.get('longitude')),
                    'address': request.form.get('address'),
                    'country': request.form.get('country'),
                    'region': request.form.get('region')
                },
                # Set arrival_location to None since the product is just starting its journey
                'arrival_location': None,
                'estimated_arrival_time': request.form.get('arrival_time'),
                'transport_conditions': {},
                'status': 'initiated',
                'additional_info': {}
            }
            
            # Sign the data
            signature = auth_system.sign_data(demo_users[username]['private_key'], data)
            
            # Create the transaction
            blockchain.new_transaction(
                username,
                'transfer',
                data,
                signature
            )
            
            # Mine a block to include this transaction
            last_block = blockchain.last_block
            last_proof = last_block['proof']
            proof = blockchain.proof_of_work(last_proof)
            previous_hash = blockchain.hash(last_block)
            block = blockchain.new_block(proof, previous_hash)
            
            return render_template('transfer_completed.html', 
                                product_id=data['product_id'], 
                                recipient=request.form.get('recipient'))
        
        except Exception as e:
            return render_template('transfer_product.html', error=str(e))
    
    # For GET requests, show the form with a list of products owned by the user
    owned_products = []
    for product_id, details in blockchain.products.items():
        if details['current_owner'] == username:
            owned_products.append(product_id)
    
    # Get a list of all users except the current one
    all_users = list(auth_system.registered_users.keys())
    other_users = [user for user in all_users if user != username]
    
    return render_template('transfer_product.html', 
                           owned_products=owned_products, 
                           other_users=other_users)


@app.route('/ui/product/<product_id>')
def ui_product_details(product_id):
    """View product details and history"""
    try:
        history = blockchain.get_product_history(product_id)
        verification = blockchain.verify_product_authenticity(product_id)
        product_info = history[0]['data'] if history else None
        
        return render_template('product_details.html', 
                               product_id=product_id,
                               product_info=product_info, 
                               history=history,
                               verification=verification)
    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/ui/search', methods=['GET', 'POST'])
def ui_search_product():
    """Search for a product by ID"""
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        try:
            blockchain.get_product_history(product_id)  # Check if product exists
            return redirect(url_for('ui_product_details', product_id=product_id))
        except ValueError:
            return render_template('search.html', error=f"Product ID {product_id} not found")
    
    return render_template('search.html')


if __name__ == '__main__':
    from datetime import datetime
    
    # For demo purposes, pre-register some users
    private_key1, public_key1 = auth_system.generate_key_pair()
    auth_system.register_user('farmer1', public_key1, 'producer', 'Organic Farm Co.')
    demo_users['farmer1'] = {'private_key': private_key1, 'public_key': public_key1, 'user_id': 'farmer1-id'}
    
    private_key2, public_key2 = auth_system.generate_key_pair()
    auth_system.register_user('processor1', public_key2, 'processor', 'GreenProcess Inc.')
    demo_users['processor1'] = {'private_key': private_key2, 'public_key': public_key2, 'user_id': 'processor1-id'}
    
    private_key3, public_key3 = auth_system.generate_key_pair()
    auth_system.register_user('distributor1', public_key3, 'distributor', 'EcoDistribution Ltd.')
    demo_users['distributor1'] = {'private_key': private_key3, 'public_key': public_key3, 'user_id': 'distributor1-id'}
    
    private_key4, public_key4 = auth_system.generate_key_pair()
    auth_system.register_user('retailer1', public_key4, 'retailer', 'GreenMart')
    demo_users['retailer1'] = {'private_key': private_key4, 'public_key': public_key4, 'user_id': 'retailer1-id'}
    
    app.run(host='0.0.0.0', port=5000)
