from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
from datetime import datetime
import random
import string
import html
import os
from dotenv import load_dotenv
from auth import generate_token, token_required, verify_token, init_auth_routes
from werkzeug.utils import secure_filename 
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from database import init_connection_pool, init_db, execute_query, execute_transaction

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize database connection pool
init_connection_pool()

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

# Hardcoded secret key (CWE-798)
app.secret_key = "secret123"

UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def generate_account_number():
    return ''.join(random.choices(string.digits, k=10))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Mass Assignment Vulnerability - Client can send additional parameters
            user_data = request.get_json()  # Changed to get_json()
            account_number = generate_account_number()
            
            # Check if username exists
            existing_user = execute_query(
                "SELECT username FROM users WHERE username = %s",
                (user_data.get('username'),)
            )
            
            if existing_user and existing_user[0]:
                return jsonify({
                    'status': 'error',
                    'message': 'Username already exists',
                    'username': user_data.get('username'),
                    'tried_at': str(datetime.now())  # Information disclosure
                }), 400
            
            # Build dynamic query based on user input fields
            # Vulnerability: Mass Assignment possible here
            fields = ['username', 'password', 'account_number']
            values = [user_data.get('username'), user_data.get('password'), account_number]
            
            # Include any additional parameters from user input
            for key, value in user_data.items():
                if key not in ['username', 'password']:
                    fields.append(key)
                    values.append(value)
            
            # Build the SQL query dynamically
            query = f"""
                INSERT INTO users ({', '.join(fields)})
                VALUES ({', '.join(['%s'] * len(fields))})
                RETURNING id, username, account_number, balance, is_admin
            """
            
            result = execute_query(query, values, fetch=True)
            
            if not result or not result[0]:
                raise Exception("Failed to create user")
                
            user = result[0]
            
            # Excessive Data Exposure in Response
            sensitive_data = {
                'status': 'success',
                'message': 'Registration successful! Proceed to login',
                'debug_data': {  # Sensitive data exposed
                    'user_id': user[0],
                    'username': user[1],
                    'account_number': user[2],
                    'balance': float(user[3]) if user[3] else 1000.0,
                    'is_admin': user[4],
                    'registration_time': str(datetime.now()),
                    'server_info': request.headers.get('User-Agent'),
                    'raw_data': user_data,  # Exposing raw input data
                    'fields_registered': fields  # Show what fields were registered
                }
            }
            
            response = jsonify(sensitive_data)
            response.headers['X-Debug-Info'] = str(sensitive_data['debug_data'])
            response.headers['X-User-Info'] = f"id={user[0]};admin={user[4]};balance={user[3]}"
            
            return response
                
        except Exception as e:
            print(f"Registration error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Registration failed',
                'error': str(e)
            }), 500
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            
            print(f"Login attempt - Username: {username}")  # Debug print
            
            # SQL Injection vulnerability (intentionally vulnerable)
            query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
            print(f"Debug - Login query: {query}")  # Debug print
            
            user = execute_query(query)
            print(f"Debug - Query result: {user}")  # Debug print
            
            if user and len(user) > 0:
                user = user[0]  # Get first row
                print(f"Debug - Found user: {user}")  # Debug print
                
                # Generate JWT token instead of using session
                token = generate_token(user[0], user[1], user[5])
                print(f"Debug - Generated token: {token}")  # Debug print
                
                response = make_response(jsonify({
                    'status': 'success',
                    'message': 'Login successful',
                    'token': token,
                    'debug_info': {  # Vulnerability: Information disclosure
                        'user_id': user[0],
                        'username': user[1],
                        'account_number': user[3],
                        'is_admin': user[5],
                        'login_time': str(datetime.now())
                    }
                }))
                # Vulnerability: Cookie without secure flag
                response.set_cookie('token', token, httponly=True)
                return response
            
            # Vulnerability: Username enumeration
            return jsonify({
                'status': 'error',
                'message': 'Invalid credentials',
                'debug_info': {  # Vulnerability: Information disclosure
                    'attempted_username': username,
                    'time': str(datetime.now())
                }
            }), 401
            
        except Exception as e:
            print(f"Login error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Login failed',
                'error': str(e)
            }), 500
        
    return render_template('login.html')

@app.route('/debug/users')
def debug_users():
    users = execute_query("SELECT id, username, password, account_number, is_admin FROM users")
    return jsonify({'users': [
        {
            'id': u[0],
            'username': u[1],
            'password': u[2],
            'account_number': u[3],
            'is_admin': u[4]
        } for u in users
    ]})

@app.route('/dashboard')
@token_required
def dashboard(current_user):
    # Vulnerability: No input validation on user_id
    user = execute_query(
        "SELECT * FROM users WHERE id = %s",
        (current_user['user_id'],)
    )[0]
    
    loans = execute_query(
        "SELECT * FROM loans WHERE user_id = %s",
        (current_user['user_id'],)
    )
    
    # Create a user dictionary with all fields
    user_data = {
        'id': user[0],
        'username': user[1],
        'account_number': user[3],
        'balance': float(user[4]),
        'is_admin': user[5],
        'profile_picture': user[6] if len(user) > 6 and user[6] else 'user.png'  # Default image
    }
    
    return render_template('dashboard.html',
                         user=user_data,
                         username=user[1],
                         balance=float(user[4]),
                         account_number=user[3],
                         loans=loans,
                         is_admin=current_user.get('is_admin', False))

# Check balance endpoint
@app.route('/check_balance/<account_number>')
def check_balance(account_number):
    # Broken Object Level Authorization (BOLA) vulnerability
    # No authentication check, anyone can check any account balance
    try:
        # Vulnerability: SQL Injection possible
        user = execute_query(
            f"SELECT username, balance FROM users WHERE account_number='{account_number}'"
        )
        
        if user:
            # Vulnerability: Information disclosure
            return jsonify({
                'status': 'success',
                'username': user[0][0],
                'balance': float(user[0][1]),
                'account_number': account_number
            })
        return jsonify({
            'status': 'error',
            'message': 'Account not found'
        }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Transfer endpoint
@app.route('/transfer', methods=['POST'])
@token_required
def transfer(current_user):
    try:
        data = request.get_json()
        # Vulnerability: No input validation on amount
        # Vulnerability: Negative amounts allowed
        amount = float(data.get('amount'))
        to_account = data.get('to_account')
        
        # Get sender's account number
        # Race condition vulnerability in checking balance
        sender_data = execute_query(
            "SELECT account_number, balance FROM users WHERE id = %s",
            (current_user['user_id'],)
        )[0]
        
        from_account = sender_data[0]
        balance = float(sender_data[1])
        
        if balance >= abs(amount):  # Check against absolute value of amount
            try:
                # Vulnerability: Negative transfers possible
                # Vulnerability: No transaction atomicity
                queries = [
                    (
                        "UPDATE users SET balance = balance - %s WHERE id = %s",
                        (amount, current_user['user_id'])
                    ),
                    (
                        "UPDATE users SET balance = balance + %s WHERE account_number = %s",
                        (amount, to_account)
                    ),
                    (
                        """INSERT INTO transactions 
                           (from_account, to_account, amount, transaction_type, description)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (from_account, to_account, amount, 'transfer', 
                         data.get('description', 'Transfer'))
                    )
                ]
                execute_transaction(queries)
                
                return jsonify({
                    'status': 'success',
                    'message': 'Transfer Completed',
                    'new_balance': balance - amount
                })
                
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        else:
            return jsonify({
                'status': 'error',
                'message': 'Insufficient funds'
            }), 400
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Get transaction history endpoint
@app.route('/transactions/<account_number>')
def get_transaction_history(account_number):
    # Vulnerability: No authentication required (BOLA)
    # Vulnerability: SQL Injection possible
    try:
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
        
        transactions = execute_query(query)
        
        # Vulnerability: Information disclosure
        transaction_list = [{
            'id': t[0],
            'from_account': t[1],
            'to_account': t[2],
            'amount': float(t[3]),
            'timestamp': str(t[4]),
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
        return jsonify({
            'status': 'error',
            'message': str(e),
            'query': query,  # Vulnerability: Query exposure
            'account_number': account_number
        }), 500

@app.route('/upload_profile_picture', methods=['POST'])
@token_required
def upload_profile_picture(current_user):
    if 'profile_picture' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['profile_picture']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    try:
        # Vulnerability: No file type validation
        # Vulnerability: Using user-controlled filename
        # Vulnerability: No file size check
        # Vulnerability: No content-type validation
        filename = secure_filename(file.filename)
        
        # Add random prefix to prevent filename collisions
        filename = f"{random.randint(1, 1000000)}_{filename}"
        
        # Vulnerability: Path traversal possible if filename contains ../
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        file.save(file_path)
        
        # Update database with just the filename
        execute_query(
            "UPDATE users SET profile_picture = %s WHERE id = %s",
            (filename, current_user['user_id']),
            fetch=False
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Profile picture uploaded successfully',
            'file_path': os.path.join('static/uploads', filename)  # Vulnerability: Path disclosure
        })
        
    except Exception as e:
        # Vulnerability: Detailed error exposure
        print(f"Profile picture upload error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'file_path': file_path  # Vulnerability: Information disclosure
        }), 500

# Loan request endpoint
@app.route('/request_loan', methods=['POST'])
@token_required
def request_loan(current_user):
    try:
        data = request.get_json()
        # Vulnerability: No input validation on amount
        amount = float(data.get('amount'))
        
        execute_query(
            "INSERT INTO loans (user_id, amount) VALUES (%s, %s)",
            (current_user['user_id'], amount),
            fetch=False
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Loan requested successfully'
        })
        
    except Exception as e:
        print(f"Loan request error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Hidden admin endpoint (security through obscurity)
@app.route('/sup3r_s3cr3t_admin')
@token_required
def admin_panel(current_user):
    if not current_user['is_admin']:
        return "Access Denied", 403
        
    users = execute_query("SELECT * FROM users")
    pending_loans = execute_query("SELECT * FROM loans WHERE status='pending'")
    
    return render_template('admin.html', users=users, pending_loans=pending_loans)

@app.route('/admin/approve_loan/<int:loan_id>', methods=['POST'])
@token_required
def approve_loan(current_user, loan_id):
    if not current_user.get('is_admin'):
        return jsonify({'error': 'Access Denied'}), 403
    
    try:
        # Vulnerability: Race condition in loan approval
        # Vulnerability: No validation if loan is already approved
        loan = execute_query(
            "SELECT * FROM loans WHERE id = %s",
            (loan_id,)
        )[0]
        
        if loan:
            # Vulnerability: No transaction atomicity
            # Vulnerability: No validation of loan amount
            queries = [
                (
                    "UPDATE loans SET status='approved' WHERE id = %s",
                    (loan_id,)
                ),
                (
                    "UPDATE users SET balance = balance + %s WHERE id = %s",
                    (float(loan[2]), loan[1])
                )
            ]
            execute_transaction(queries)
            
            return jsonify({
                'status': 'success',
                'message': 'Loan approved successfully',
                'debug_info': {  # Vulnerability: Information disclosure
                    'loan_id': loan_id,
                    'loan_amount': float(loan[2]),
                    'user_id': loan[1],
                    'approved_by': current_user['username'],
                    'approved_at': str(datetime.now()),
                    'loan_details': {  # Excessive data exposure
                        'id': loan[0],
                        'user_id': loan[1],
                        'amount': float(loan[2]),
                        'status': loan[3]
                    }
                }
            })
        
        return jsonify({
            'status': 'error',
            'message': 'Loan not found',
            'loan_id': loan_id
        }), 404
        
    except Exception as e:
        # Vulnerability: Detailed error exposure
        print(f"Loan approval error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to approve loan',
            'error': str(e),
            'loan_id': loan_id
        }), 500

# Delete account endpoint
@app.route('/admin/delete_account/<int:user_id>', methods=['POST'])
@token_required
def delete_account(current_user, user_id):
    if not current_user.get('is_admin'):
        return jsonify({'error': 'Access Denied'}), 403
    
    try:
        # Vulnerability: No user confirmation required
        # Vulnerability: No audit logging
        # Vulnerability: No backup creation
        execute_query(
            "DELETE FROM users WHERE id = %s",
            (user_id,),
            fetch=False
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Account deleted successfully',
            'debug_info': {
                'deleted_user_id': user_id,
                'deleted_by': current_user['username'],
                'timestamp': str(datetime.now())
            }
        })
        
    except Exception as e:
        print(f"Delete account error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Create admin endpoint
@app.route('/admin/create_admin', methods=['POST'])
@token_required
def create_admin(current_user):
    if not current_user.get('is_admin'):
        return jsonify({'error': 'Access Denied'}), 403
    
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        account_number = generate_account_number()
        
        # Vulnerability: SQL injection possible
        # Vulnerability: No password complexity requirements
        # Vulnerability: No account number uniqueness check
        execute_query(
            f"INSERT INTO users (username, password, account_number, is_admin) VALUES ('{username}', '{password}', '{account_number}', true)",
            fetch=False
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Admin created successfully'
        })
        
    except Exception as e:
        print(f"Create admin error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# Forgot password endpoint
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        try:
            data = request.get_json()  # Changed to get_json()
            username = data.get('username')
            
            # Vulnerability: SQL Injection possible
            user = execute_query(
                f"SELECT id FROM users WHERE username='{username}'"
            )
            
            if user:
                # Weak reset pin logic (CWE-330)
                # Using only 3 digits makes it easily guessable
                reset_pin = str(random.randint(100, 999))
                
                # Store the reset PIN in database (in plaintext - CWE-319)
                execute_query(
                    "UPDATE users SET reset_pin = %s WHERE username = %s",
                    (reset_pin, username),
                    fetch=False
                )
                
                # Vulnerability: Information disclosure
                return jsonify({
                    'status': 'success',
                    'message': 'Reset PIN has been sent to your email.',
                    'debug_info': {  # Vulnerability: Information disclosure
                        'timestamp': str(datetime.now()),
                        'username': username,
                        'pin_length': len(reset_pin),
                        'pin': reset_pin  # Intentionally exposing pin for learning
                    }
                })
            else:
                # Vulnerability: Username enumeration
                return jsonify({
                    'status': 'error',
                    'message': 'User not found'
                }), 404
                
        except Exception as e:
            print(f"Forgot password error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
            
    return render_template('forgot_password.html')

# Reset password endpoint
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        try:
            data = request.get_json()
            username = data.get('username')
            reset_pin = data.get('reset_pin')
            new_password = data.get('new_password')
            
            # Vulnerability: No rate limiting on PIN attempts
            # Vulnerability: Timing attack possible in PIN verification
            user = execute_query(
                "SELECT id FROM users WHERE username = %s AND reset_pin = %s",
                (username, reset_pin)
            )
            
            if user:
                # Vulnerability: No password complexity requirements
                # Vulnerability: No password history check
                execute_query(
                    "UPDATE users SET password = %s, reset_pin = NULL WHERE username = %s",
                    (new_password, username),
                    fetch=False
                )
                
                return jsonify({
                    'status': 'success',
                    'message': 'Password has been reset successfully'
                })
            else:
                # Vulnerability: Username enumeration possible
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid reset PIN'
                }), 400
                
        except Exception as e:
            # Vulnerability: Detailed error exposure
            print(f"Reset password error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Password reset failed',
                'error': str(e)
            }), 500
            
    return render_template('reset_password.html')

@app.route('/api/transactions', methods=['GET'])
@token_required
def api_transactions(current_user):
    # Vulnerability: No validation of account_number parameter
    account_number = request.args.get('account_number')
    
    if not account_number:
        return jsonify({'error': 'Account number required'}), 400
        
    # Vulnerability: SQL Injection
    query = f"""
        SELECT * FROM transactions 
        WHERE from_account='{account_number}' OR to_account='{account_number}'
        ORDER BY timestamp DESC
    """
    
    try:
        transactions = execute_query(query)
        
        return jsonify({
            'transactions': transactions,
            'account_number': account_number
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    init_auth_routes(app)
    # Vulnerability: Debug mode enabled in production
    app.run(host='0.0.0.0', port=5000, debug=True)