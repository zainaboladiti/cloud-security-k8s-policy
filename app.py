# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
import sqlite3
import random
import string
import html

app = Flask(__name__)
app.secret_key = "super_secret_key_123"  # Hardcoded secret key (CWE-798)

def init_db():
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            account_number TEXT NOT NULL,
            balance REAL DEFAULT 1000.0,
            is_admin BOOLEAN DEFAULT 0
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users (id)
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
                'error': str(e),
                'query': query,
                'values': values
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
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = user[5]
            return redirect(url_for('dashboard'))
        
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM users WHERE id={session['user_id']}")
    user = c.fetchone()
    
    c.execute(f"SELECT * FROM loans WHERE user_id={session['user_id']}")
    loans = c.fetchall()
    conn.close()
    
    return render_template('dashboard.html', 
                         username=user[1], 
                         balance=user[4], 
                         account_number=user[3],
                         loans=loans,
                         is_admin=session.get('is_admin', False))

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

@app.route('/transfer', methods=['POST'])
def transfer():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    amount = float(request.form['amount'])
    to_account = request.form['to_account']
    
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    
    # Race condition vulnerability
    c.execute(f"SELECT balance FROM users WHERE id={session['user_id']}")
    balance = c.fetchone()[0]
    
    if balance >= amount:
        c.execute(f"UPDATE users SET balance = balance - {amount} WHERE id={session['user_id']}")
        c.execute(f"UPDATE users SET balance = balance + {amount} WHERE account_number='{to_account}'")
        conn.commit()
        
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/request_loan', methods=['POST'])
def request_loan():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    amount = float(request.form['amount'])
    
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute("INSERT INTO loans (user_id, amount) VALUES (?, ?)", 
             (session['user_id'], amount))
    conn.commit()
    conn.close()
    
    return redirect(url_for('dashboard'))

# Hidden admin endpoint (security through obscurity)
@app.route('/sup3r_s3cr3t_admin', methods=['GET'])
def admin_panel():
    if not session.get('is_admin'):
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
def approve_loan(loan_id):
    if not session.get('is_admin'):
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
def delete_account(user_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Access Denied'}), 403
    
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute(f"DELETE FROM users WHERE id={user_id}")
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/create_admin', methods=['POST'])
def create_admin():
    if not session.get('is_admin'):
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

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)