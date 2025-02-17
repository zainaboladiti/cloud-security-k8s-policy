import os
import psycopg2
from psycopg2 import pool
from datetime import datetime
import time

# Vulnerable database configuration
# CWE-259: Use of Hard-coded Password
# CWE-798: Use of Hard-coded Credentials
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'vulnerable_bank'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),  # Hardcoded password in default value
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

# Create a connection pool
connection_pool = None

def init_connection_pool(min_connections=1, max_connections=10, max_retries=5, retry_delay=2):
    """
    Initialize the database connection pool with retry mechanism
    Vulnerability: No connection encryption enforced
    """
    global connection_pool
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            connection_pool = psycopg2.pool.SimpleConnectionPool(
                min_connections,
                max_connections,
                **DB_CONFIG
            )
            print("Database connection pool created successfully")
            return
        except Exception as e:
            retry_count += 1
            print(f"Failed to connect to database (attempt {retry_count}/{max_retries}): {e}")
            if retry_count < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Could not establish database connection.")
                raise e

def get_connection():
    if connection_pool:
        return connection_pool.getconn()
    raise Exception("Connection pool not initialized")

def return_connection(connection):
    if connection_pool:
        connection_pool.putconn(connection)

def init_db():
    """
    Initialize database tables
    Multiple vulnerabilities present for learning purposes
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,  -- Vulnerability: Passwords stored in plaintext
                    account_number TEXT NOT NULL UNIQUE,
                    balance DECIMAL(15, 2) DEFAULT 1000.0,
                    is_admin BOOLEAN DEFAULT FALSE,
                    profile_picture TEXT,
                    reset_pin TEXT  -- Vulnerability: Reset PINs stored in plaintext
                )
            ''')
            
            # Create loans table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS loans (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    amount DECIMAL(15, 2),
                    status TEXT DEFAULT 'pending'
                )
            ''')
            
            # Create transactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    from_account TEXT NOT NULL,
                    to_account TEXT NOT NULL,
                    amount DECIMAL(15, 2) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    transaction_type TEXT NOT NULL,
                    description TEXT
                )
            ''')
            
            # Create default admin account if it doesn't exist
            cursor.execute("SELECT * FROM users WHERE username='admin'")
            if not cursor.fetchone():
                cursor.execute(
                    """
                    INSERT INTO users (username, password, account_number, balance, is_admin) 
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    ('admin', 'admin123', 'ADMIN001', 1000000.0, True)
                )
            
            conn.commit()
            print("Database initialized successfully")
            
    except Exception as e:
        # Vulnerability: Detailed error information exposed
        print(f"Error initializing database: {e}")
        conn.rollback()
        raise e
    finally:
        return_connection(conn)

def execute_query(query, params=None, fetch=True):
    """
    Execute a database query
    Vulnerability: This function still allows for SQL injection if called with string formatting
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            result = None
            if fetch:
                result = cursor.fetchall()
            # Always commit for INSERT, UPDATE, DELETE operations
            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                conn.commit()
            return result
    except Exception as e:
        # Vulnerability: Error details might be exposed to users
        conn.rollback()
        raise e
    finally:
        return_connection(conn)

def execute_transaction(queries_and_params):
    """
    Execute multiple queries in a transaction
    Vulnerability: No input validation on queries
    queries_and_params: list of tuples (query, params)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            for query, params in queries_and_params:
                cursor.execute(query, params)
            conn.commit()
    except Exception as e:
        # Vulnerability: Transaction rollback exposed
        conn.rollback()
        raise e
    finally:
        return_connection(conn)