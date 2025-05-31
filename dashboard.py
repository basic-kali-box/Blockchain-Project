from flask import Blueprint, render_template, session, redirect, url_for
from .auth import AuthenticationSystem

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    # Get user info from session
    username = session.get('username')
    if not username:
        return redirect(url_for('auth.login'))

    # Get user info from authentication system
    auth_system = AuthenticationSystem()
    user_info = auth_system.registered_users.get(username)
    
    if not user_info:
        return redirect(url_for('auth.login'))

    # Get blockchain length (you'll need to implement this function in your blockchain module)
    blockchain_length = get_blockchain_length()
    
    # Get demo info (you'll need to implement this function in your auth module)
    demo_info = get_demo_info(username)
    
    # Define role-specific dashboard content
    role = user_info['role']
    
    # Role-specific actions
    actions = []
    
    if role == 'producer':
        actions = [
            {'title': 'Enregistrer un produit', 'url': '/ui/register_product', 
             'description': 'Ajouter un nouveau produit à la blockchain'},
            {'title': 'Voir mes produits', 'url': '/ui/my_products',
             'description': 'Consulter les produits que vous avez produits'},
            {'title': 'Vérifier la qualité', 'url': '/ui/quality_check',
             'description': 'Vérifier la qualité des matières premières'}
        ]
    elif role == 'processor':
        actions = [
            {'title': 'Recevoir des produits', 'url': '/ui/receive_products',
             'description': 'Recevoir et valider les produits entrants'},
            {'title': 'Traiter des produits', 'url': '/ui/process_products',
             'description': 'Traiter et transformer les produits'},
            {'title': 'Vérifier la qualité', 'url': '/ui/quality_check',
             'description': 'Vérifier la qualité des produits traités'}
        ]
    elif role == 'distributor':
        actions = [
            {'title': 'Recevoir des produits', 'url': '/ui/receive_products',
             'description': 'Recevoir et valider les produits entrants'},
            {'title': 'Transférer des produits', 'url': '/ui/transfer_product',
             'description': 'Transférer des produits aux détaillants'},
            {'title': 'Suivi des stocks', 'url': '/ui/inventory',
             'description': 'Gérer vos stocks de produits'}
        ]
    elif role == 'retailer':
        actions = [
            {'title': 'Recevoir des produits', 'url': '/ui/receive_products',
             'description': 'Recevoir et valider les produits entrants'},
            {'title': 'Vendre des produits', 'url': '/ui/sell_products',
             'description': 'Vendre des produits aux consommateurs'},
            {'title': 'Gérer les stocks', 'url': '/ui/inventory',
             'description': 'Gérer vos stocks de produits'}
        ]
    elif role == 'regulator':
        actions = [
            {'title': 'Auditer les produits', 'url': '/ui/audit_products',
             'description': 'Vérifier la conformité des produits'},
            {'title': 'Consulter l\'historique', 'url': '/ui/view_history',
             'description': 'Consulter l\'historique complet des produits'},
            {'title': 'Générer des rapports', 'url': '/ui/generate_reports',
             'description': 'Créer des rapports de conformité'}
        ]
    
    # Role-specific statistics
    stats = []
    if role == 'producer':
        stats = [
            {'title': 'Produits produits', 'value': get_produced_products_count(username)},
            {'title': 'Produits en cours', 'value': get_active_products_count(username)}
        ]
    elif role == 'processor':
        stats = [
            {'title': 'Produits reçus', 'value': get_received_products_count(username)},
            {'title': 'Produits traités', 'value': get_processed_products_count(username)}
        ]
    elif role == 'distributor':
        stats = [
            {'title': 'Produits reçus', 'value': get_received_products_count(username)},
            {'title': 'Produits distribués', 'value': get_distributed_products_count(username)}
        ]
    elif role == 'retailer':
        stats = [
            {'title': 'Produits en stock', 'value': get_inventory_count(username)},
            {'title': 'Produits vendus', 'value': get_sold_products_count(username)}
        ]
    elif role == 'regulator':
        stats = [
            {'title': 'Audits effectués', 'value': get_audit_count(username)},
            {'title': 'Infractions détectées', 'value': get_violations_count()}
        ]
    
    return render_template('dashboard.html', 
                         user_info=user_info,
                         blockchain_length=blockchain_length,
                         demo_info=demo_info,
                         actions=actions,
                         stats=stats,
                         role=role)

# Helper functions (you'll need to implement these based on your blockchain data)
def get_blockchain_length():
    return 0  # Replace with actual implementation

def get_demo_info(username):
    return {}  # Replace with actual implementation

def get_produced_products_count(username):
    return 0  # Replace with actual implementation

def get_active_products_count(username):
    return 0  # Replace with actual implementation

def get_received_products_count(username):
    return 0  # Replace with actual implementation

def get_processed_products_count(username):
    return 0  # Replace with actual implementation

def get_distributed_products_count(username):
    return 0  # Replace with actual implementation

def get_inventory_count(username):
    return 0  # Replace with actual implementation

def get_sold_products_count(username):
    return 0  # Replace with actual implementation

def get_audit_count(username):
    return 0  # Replace with actual implementation

def get_violations_count():
    return 0  # Replace with actual implementation
