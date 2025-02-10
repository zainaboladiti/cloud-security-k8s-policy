# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import os
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
            balance REAL DEFAULT 1000.0
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']  # Storing plaintext password (CWE-256)
        
        # SQL Injection vulnerability (CWE-89)
        conn = sqlite3.connect('bank.db')
        c = conn.cursor()
        c.execute(f"INSERT INTO users (username, password) VALUES ('{username}', '{password}')")
        conn.commit()
        conn.close()
        
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # SQL Injection vulnerability (CWE-89)
        conn = sqlite3.connect('bank.db')
        c = conn.cursor()
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        c.execute(query)
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('dashboard'))
        
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute(f"SELECT balance FROM users WHERE id={session['user_id']}")
    balance = c.fetchone()[0]
    conn.close()
    
    return render_template('dashboard.html', username=session['username'], balance=balance)

@app.route('/transfer', methods=['POST'])
def transfer():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    # Missing CSRF protection
    amount = float(request.form['amount'])
    to_user = request.form['to_user']
    
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    
    # Race condition vulnerability (CWE-362)
    c.execute(f"SELECT balance FROM users WHERE id={session['user_id']}")
    balance = c.fetchone()[0]
    
    if balance >= amount:
        # SQL Injection vulnerability (CWE-89)
        c.execute(f"UPDATE users SET balance = balance - {amount} WHERE id={session['user_id']}")
        c.execute(f"UPDATE users SET balance = balance + {amount} WHERE username='{to_user}'")
        conn.commit()
        
    conn.close()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)  # Debug mode enabled in production (CWE-489)