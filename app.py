from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
from datetime import datetime
import sqlite3
import random
import string
import html
import os
from auth import generate_token, token_required, verify_token, init_auth_routes
from werkzeug.utils import secure_filename 
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

SWAGGER_URL = '/api/docs'
API_URL = '/static/openapi.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Vulnerable Bank API Documentation",
        'validatorUrl': None
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

app.secret_key = "secret123"  # Hardcoded secret key (CWE-798)

UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def init_db():
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            account_number TEXT NOT NULL,
            balance REAL DEFAULT 1000.0,
            is_admin BOOLEAN DEFAULT 0,
            profile_picture TEXT,
            reset_pin TEXT
        )
    ''')
    
    # Create loans table
    c.execute('''
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create transactions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_account TEXT NOT NULL,
            to_account TEXT NOT NULL,
            amount REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            transaction_type TEXT NOT NULL,
            description TEXT
        )
    ''')
    
    # Create default admin account
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, account_number, balance, is_admin) VALUES (?, ?, ?, ?, ?)",
                 ('admin', 'admin123', 'ADMIN001', 1000000.0, 1))
    
    conn.commit()
    conn.close()

def generate_account_number():
    return ''.join(random.choices(string.digits, k=10))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Mass Assignment Vulnerability - Client can send additional parameters
        user_data = request.form.to_dict()
        account_number = generate_account_number()
        
        # Check if username already exists
        conn = sqlite3.connect('bank.db')
        c = conn.cursor()
        c.execute(f"SELECT username FROM users WHERE username='{user_data.get('username')}'")
        existing_user = c.fetchone()
        
        if existing_user:
            conn.close()
            return jsonify({
                'status': 'error',
                'message': 'Username already exists',
                'username': user_data.get('username'),
                'tried_at': str(datetime.now())  # Information disclosure
            }), 400
        
        
        # Build the SQL query with all parameters
        fields = ['username', 'password', 'account_number']
        values = [user_data.get('username'), user_data.get('password'), account_number]
        
        # Include any additional parameters (Mass Assignment Vulnerability)
        for key, value in user_data.items():
            if key not in ['username', 'password']:
                fields.append(key)
                values.append(value)
        
        # Create the SQL query
        query = f"INSERT INTO users ({', '.join(fields)}) VALUES ({', '.join(['?'] * len(fields))})"
        
        try:
            c.execute(query, values)
            user_id = c.lastrowid
            conn.commit()

             # Generate JWT token for new user
            token = generate_token(user_id, user_data.get('username'), False)
            
            # Excessive Data Exposure in Response
            c.execute(f"SELECT * FROM users WHERE id={user_id}")
            user = c.fetchone()
            conn.close()
            
            # Create response with sensitive data
            sensitive_data = {
                'status': 'success',
                'message': 'Registration successful! Proceed to login',
                'debug_data': {  # Sensitive data exposed
                    'user_id': user[0],
                    'username': user[1],
                    'password': user[2],  # Exposing password
                    'account_number': user[3],
                    'balance': user[4],
                    'is_admin': user[5],
                    'registration_time': str(datetime.now()),
                    'server_info': request.headers.get('User-Agent'),
                    'raw_form_data': dict(request.form)  # Exposing raw form data
                }
            }
            
            response = jsonify(sensitive_data)
            
            # Add sensitive data in custom headers
            response.headers['X-Debug-Info'] = str(sensitive_data['debug_data'])
            response.headers['X-User-Info'] = f"id={user[0]};admin={user[5]};balance={user[4]}"
            response.headers['X-Registration-Query'] = f"{query} -- values: {values}"
            
            return response
            
        except Exception as e:
            conn.close()
            return jsonify({
                'status': 'error',
                'message': 'Registration failed',
                'error': str(e)
            }), 500
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # SQL Injection vulnerability
        conn = sqlite3.connect('bank.db')
        c = conn.cursor()
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        c.execute(query)
        user = c.fetchone()
        conn.close()
        
        
        if user:
            # Generate JWT token instead of using session
            token = generate_token(user[0], user[1], user[5])
            
            # Set token in cookie and also return in response
            response = make_response(jsonify({
                'status': 'success',
                'message': 'Login successful',
                'token': token
            }))
            response.set_cookie('token', token, httponly=True)
            return response
            
        return jsonify({
            'status': 'error',
            'message': 'Invalid credentials'
        }), 401
        
    return render_template('login.html')

#Dashboard code
@app.route('/dashboard')
@token_required
def dashboard(current_user):
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM users WHERE id={current_user['user_id']}")
    user = c.fetchone()
    
    c.execute(f"SELECT * FROM loans WHERE user_id={current_user['user_id']}")
    loans = c.fetchall()
    conn.close()
    
    # Create a user dictionary with all fields
    user_data = {
        'id': user[0],
        'username': user[1],
        'account_number': user[3],
        'balance': user[4],
        'is_admin': user[5],
        'profile_picture': user[6] if len(user) > 6 else None
    }
    
    return render_template('dashboard.html', 
                         user=user_data,
                         username=user[1], 
                         balance=user[4], 
                         account_number=user[3],
                         loans=loans,
                         is_admin=current_user.get('is_admin', False))


@app.route('/check_balance/<account_number>')
def check_balance(account_number):
    # Broken Object Level Authorization (BOLA) vulnerability
    # No authentication check, anyone can check any account balance
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute(f"SELECT username, balance FROM users WHERE account_number='{account_number}'")
    user = c.fetchone()
    conn.close()
    
    if user:
        return jsonify({'username': user[0], 'balance': user[1]})
    return jsonify({'error': 'Account not found'}), 404

#Transfer funds
@app.route('/transfer', methods=['POST'])
@token_required
def transfer(current_user):
    amount = float(request.form['amount'])
    to_account = request.form['to_account']
    
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    
    # Get sender's account number
    # Race condition vulnerability
    c.execute(f"SELECT account_number, balance FROM users WHERE id={current_user['user_id']}")
    sender_data = c.fetchone()
    from_account = sender_data[0]
    balance = sender_data[1]
    
    if balance >= amount:
        try:
            # Perform transfer
            c.execute(f"UPDATE users SET balance = balance - {amount} WHERE id={current_user['user_id']}")
            c.execute(f"UPDATE users SET balance = balance + {amount} WHERE account_number='{to_account}'")
            
            # Record transaction
            # Vulnerability: SQL injection possible in description
            description = request.form.get('description', 'Transfer')
            c.execute(f"""
                INSERT INTO transactions 
                (from_account, to_account, amount, transaction_type, description)
                VALUES ('{from_account}', '{to_account}', {amount}, 'transfer', '{description}')
            """)
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
    
    conn.close()
    return redirect(url_for('dashboard'))


@app.route('/request_loan', methods=['POST'])
@token_required
def request_loan(current_user):
    amount = float(request.form['amount'])
    
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute("INSERT INTO loans (user_id, amount) VALUES (?, ?)", 
             (current_user['user_id'], amount))
    conn.commit()
    conn.close()
    
    return redirect(url_for('dashboard'))

# Hidden admin endpoint (security through obscurity)
@app.route('/sup3r_s3cr3t_admin')
@token_required
def admin_panel(current_user):
    if not current_user['is_admin']:
        return "Access Denied", 403
        
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    c.execute("SELECT * FROM loans WHERE status='pending'")
    pending_loans = c.fetchall()
    conn.close()
    
    return render_template('admin.html', users=users, pending_loans=pending_loans)


@app.route('/admin/approve_loan/<int:loan_id>', methods=['POST'])
@token_required
def approve_loan(current_user, loan_id):
    if not current_user.get('is_admin'):
        return jsonify({'error': 'Access Denied'}), 403
    
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM loans WHERE id={loan_id}")
    loan = c.fetchone()
    
    if loan:
        c.execute(f"UPDATE loans SET status='approved' WHERE id={loan_id}")
        c.execute(f"UPDATE users SET balance = balance + {loan[2]} WHERE id={loan[1]}")
        conn.commit()
    
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_account/<int:user_id>', methods=['POST'])
@token_required
def delete_account(current_user, user_id):
    if not current_user.get('is_admin'):
        return jsonify({'error': 'Access Denied'}), 403
    
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute(f"DELETE FROM users WHERE id={user_id}")
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/create_admin', methods=['POST'])
@token_required
def create_admin(current_user):
    if not current_user.get('is_admin'):
        return jsonify({'error': 'Access Denied'}), 403
    
    username = request.form['username']
    password = request.form['password']
    account_number = generate_account_number()
    
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute(f"INSERT INTO users (username, password, account_number, is_admin) VALUES ('{username}', '{password}', '{account_number}', 1)")
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_panel'))


@app.route('/upload_profile_picture', methods=['POST'])
@token_required
def upload_profile_picture(current_user):
    if 'profile_picture' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['profile_picture']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    # Vulnerability: No file type validation
    # Vulnerability: Using user-controlled filename
    # Vulnerability: No file size check
    # Vulnerability: No content-type validation
    filename = secure_filename(file.filename)
    
    # Add random prefix to prevent filename collisions
    filename = f"{random.randint(1, 1000000)}_{filename}"
    
    # Vulnerability: Path traversal possible if filename contains ../
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    try:
        file.save(file_path)
        
        # Update database with just the filename
        conn = sqlite3.connect('bank.db')
        c = conn.cursor()
        
        # Vulnerability: SQL Injection possible
        c.execute(f"UPDATE users SET profile_picture='{filename}' WHERE id={current_user['user_id']}")
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Profile picture uploaded successfully',
            'file_path': os.path.join('static/uploads', filename)  # Return path relative to static folder
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'file_path': file_path  # Vulnerability: Information disclosure
        }), 500

@app.route('/transactions/<account_number>')
def get_transaction_history(account_number):
    # Vulnerability: No authentication required (BOLA)
    # Vulnerability: SQL Injection possible
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    
    # Vulnerability: Showing all transaction details
    query = f"""
        SELECT 
            id,
            from_account,
            to_account,
            amount,
            timestamp,
            transaction_type,
            description
        FROM transactions 
        WHERE from_account='{account_number}' OR to_account='{account_number}'
        ORDER BY timestamp DESC
    """
    
    try:
        c.execute(query)
        transactions = c.fetchall()
        
        # Vulnerability: Information disclosure
        transaction_list = [{
            'id': t[0],
            'from_account': t[1],
            'to_account': t[2],
            'amount': t[3],
            'timestamp': t[4],
            'type': t[5],
            'description': t[6],
            'query_used': query  # Vulnerability: Exposing SQL query
        } for t in transactions]
        
        return jsonify({
            'status': 'success',
            'account_number': account_number,
            'transactions': transaction_list,
            'server_time': str(datetime.now())  # Vulnerability: Server information disclosure
        })
        
    except Exception as e:
        # Vulnerability: Detailed error exposure
        return jsonify({
            'status': 'error',
            'error': str(e),
            'query': query,
            'account_number': account_number
        }), 500
    finally:
        conn.close()

@app.route('/api/transactions', methods=['GET'])
@token_required
def api_transactions(current_user):
    # Vulnerability: No validation of account_number parameter
    account_number = request.args.get('account_number')
    
    if not account_number:
        return jsonify({'error': 'Account number required'}), 400
        
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    
    # Vulnerability: SQL Injection
    query = f"""
        SELECT * FROM transactions 
        WHERE from_account='{account_number}' OR to_account='{account_number}'
        ORDER BY timestamp DESC
    """
    
    try:
        c.execute(query)
        transactions = c.fetchall()
        conn.close()
        
        return jsonify({
            'transactions': transactions,
            'account_number': account_number
        })
        
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        
        conn = sqlite3.connect('bank.db')
        c = conn.cursor()
        
        # Vulnerability: SQL Injection possible
        c.execute(f"SELECT id FROM users WHERE username='{username}'")
        user = c.fetchone()
        
        if user:
            # Weak reset pin logic (CWE-330)
            # Using only 3 digits makes it easily guessable
            reset_pin = str(random.randint(100, 999))
            
            # Store the reset PIN in database (in plaintext - CWE-319)
            c.execute(f"UPDATE users SET reset_pin='{reset_pin}' WHERE username='{username}'")
            conn.commit()
            
            # Vulnerability: Information disclosure
            # We would normally send this via email, but we're storing it for demonstration
            # The attacker can brute force this 3-digit PIN
            return jsonify({
                'status': 'success',
                'message': 'Reset PIN has been sent to your email.',
                'debug_info': {  # Vulnerability: Information disclosure
                    'timestamp': str(datetime.now()),
                    'username': username,
                    'pin_length': len(reset_pin)
                }
            })
        else:
            # Vulnerability: Username enumeration
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
            
        conn.close()
        
    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form['username']
        reset_pin = request.form['reset_pin']
        new_password = request.form['new_password']
        
        conn = sqlite3.connect('bank.db')
        c = conn.cursor()
        
        # Vulnerability: No rate limiting on PIN attempts
        # Vulnerability: SQL Injection possible
        c.execute(f"SELECT id FROM users WHERE username='{username}' AND reset_pin='{reset_pin}'")
        user = c.fetchone()
        
        if user:
            # Vulnerability: No password complexity requirements
            # Vulnerability: SQL Injection possible
            c.execute(f"UPDATE users SET password='{new_password}', reset_pin=NULL WHERE username='{username}'")
            conn.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Password has been reset successfully'
            })
        else:
            # Vulnerability: Timing attack possible
            return jsonify({
                'status': 'error',
                'message': 'Invalid reset PIN'
            }), 400
            
        conn.close()
        
    return render_template('reset_password.html')

if __name__ == '__main__':
    init_db()
    init_auth_routes(app) #auth.py
    app.run(host='0.0.0.0', port=5000, debug=True)