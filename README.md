# Vulnerable Bank Application 🏦

A deliberately vulnerable web application for practicing application security testing, secure code review and implementing security in CI/CD pipelines.

⚠️ **WARNING: This application is intentionally vulnerable and should only be used for educational purposes in isolated environments.**

![image](https://github.com/user-attachments/assets/7fda0106-b083-48d6-8629-f7ee3c8eb73d)

## Overview

This project is a simple banking application with multiple security vulnerabilities built in. It's designed to help security engineers, developers, interns, QA analyst and DevSecOps practitioners learn about:
- Common web application and API vulnerabilities
- Secure coding practices
- Security testing automation
- DevSecOps implementation

## Features & Vulnerabilities

### Core Banking Features
- 🔐 User Authentication & Authorization
- 💰 Account Balance Management
- 💸 Money Transfers
- 📝 Loan Requests
- 👤 Profile Picture Upload
- 📊 Transaction History
- 🔑 Password Reset System (3-digit PIN)
- 💳 Virtual Cards Management
- 📱 Bill Payments System

![image](https://github.com/user-attachments/assets/f8d14d62-d71e-41f3-85c7-133553a75989)

### Implemented Vulnerabilities

1. **Authentication & Authorization**
   - SQL Injection in login
   - Weak JWT implementation
   - Broken object level authorization (BOLA)
   - Broken object property level authorization (BOPLA)
   - Mass Assignment & Excessive Data Exposure
   - Weak password reset mechanism (3-digit PIN)
   - Token stored in localStorage
   - No server-side token invalidation
   - No session expiration

2. **Data Security**
   - Information disclosure
   - Sensitive data exposure
   - Plaintext password storage
   - SQL injection points
   - Debug information exposure
   - Detailed error messages exposed

3. **Transaction Vulnerabilities**
   - No amount validation
   - Negative amount transfers possible
   - No transaction limits
   - Race conditions in transfers and balance updates
   - Transaction history information disclosure
   - No validation on recipient accounts

4. **File Operations**
   - Unrestricted file upload
   - Path traversal vulnerabilities
   - No file type validation
   - Directory traversal
   - No file size limits
   - Unsafe file naming

5. **Session Management**
   - Token vulnerabilities
   - No session expiration
   - Weak secret keys
   - Token exposure in URLs

6. **Client and Server-Side Flaws**
   - Cross Site Scripting (XSS)
   - Cross Site Request Forgery (CSRF)
   - Insecure direct object references
   - No rate limiting

7. **Virtual Card Vulnerabilities**
   - Mass Assignment in card limit updates
   - Predictable card number generation
   - Plaintext storage of card details
   - No validation on card limits
   - BOLA in card operations
   - Race conditions in balance updates
   - Card detail information disclosure
   - No transaction verification
   - Lack of card activity monitoring

8. **Bill Payment Vulnerabilities**
   - No validation on payment amounts
   - SQL injection in biller queries
   - Information disclosure in payment history
   - Predictable reference numbers
   - Transaction history exposure
   - No validation on biller accounts
   - Race conditions in payment processing
   - BOLA in payment history access
   - Missing payment limits

## Installation & Setup 🚀

### Prerequisites
- Docker and Docker Compose (for containerized setup)
- PostgreSQL (if running locally)
- Python 3.9 or higher (for local setup)
- Git

### Option 1: Using Docker (Recommended)

#### Using Docker Compose (Easiest)
1. Clone the repository:
```bash
git clone https://github.com/Commando-X/vuln-bank.git
cd vuln-bank
```

2. Start the application:
```bash
docker-compose up --build
```

The application will be available at `http://localhost:5000`

#### Using Docker Only
1. Clone the repository:
```bash
git clone https://github.com/Commando-X/vuln-bank.git
cd vuln-bank
```

2. Build the Docker image:
```bash
docker build -t vuln-bank .
```

3. Run the container:
```bash
docker run -p 5000:5000 vuln-bank
```

### Option 2: Local Installation

#### Prerequisites
- Python 3.9 or higher
- PostgreSQL installed and running
- pip (Python package manager)
- Git

#### Steps
1. Clone the repository:
```bash
git clone https://github.com/Commando-X/vuln-bank.git
cd vuln-bank
```

2. Create and activate a virtual environment (recommended):
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Create necessary directories:
```bash
# On Windows
mkdir static\uploads

# On Linux/Mac
mkdir -p static/uploads
```

5. Modify the .env file:
   - Open .env and change DB_HOST from 'db' to 'localhost' for local PostgreSQL connection

6. Run the application:
```bash
# On Windows
python app.py

# On Linux/Mac
python3 app.py
```

### Environment Variables
The `.env` file is intentionally included in this repository to facilitate easy setup for educational purposes. In a real-world application, you should never commit `.env` files to version control.

Current environment variables:
```bash
DB_NAME=vulnerable_bank
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db  # Change to 'localhost' for local installation
DB_PORT=5432
```

### Database Setup
The application uses PostgreSQL. The database will be automatically initialized when you first run the application, creating:
- Users table
- Transactions table
- Loans table

### Accessing the Application
- Main application: `http://localhost:5000`
- API documentation: `http://localhost:5000/api/docs`

### Common Issues & Solutions

#### Windows
1. If you get "python not found":
   - Ensure Python is added to your system PATH
   - Try using `py` instead of `python`

2. Permission issues with uploads folder:
   - Run command prompt as administrator
   - Ensure you have write permissions in the project directory

#### Linux/Mac
1. Permission denied when creating directories:
   ```bash
   sudo mkdir -p static/uploads
   sudo chown -R $USER:$USER static/uploads
   ```

2. Port 5000 already in use:
   ```bash
   # Kill process using port 5000
   sudo lsof -i:5000
   sudo kill <PID>
   ```

#### PostgreSQL Issues
1. Connection refused:
   - Ensure PostgreSQL is running
   - Check credentials in .env file
   - Verify PostgreSQL port is not blocked

## Testing Guide 🎯

### Authentication Testing
1. SQL Injection in login
2. Weak password reset (bruteforce 3-digit PIN)
3. JWT token manipulation
4. Username enumeration
5. Token storage vulnerabilities

### Authorization Testing
1. Access other users' transaction history via account number
2. Upload malicious files
3. Access admin panel
4. Manipulate JWT claims
5. Exploit BOPLA (Excessive Data Exposure and Mass Assignment)
6. Privilege escalation through registration

### Transaction Testing
1. Attempt negative amount transfers
2. Race conditions in transfers
3. Transaction history access
4. Balance manipulation

### File Upload Testing
1. Upload unauthorized file types
2. Attempt path traversal
3. Upload oversized files
4. Test file overwrite scenarios
5. File type bypass

### API Security Testing
1. Token manipulation
2. BOLA/BOPLA in API endpoints
3. Information disclosure
4. Error message analysis

### Virtual Card Testing

1. Exploit mass assignment in card limit updates
2. Analyze card number generation patterns
3. Access unauthorized card details
4. Test card freezing bypasses
5. Transaction history manipulation
6. Card limit validation bypass

### Bill Payment Testing

1. Test biller enumeration
2. Payment amount validation bypass
3. Access unauthorized payment history
4. SQL injection in biller selection
5. Reference number prediction
6. Race condition exploitation in payments

## Contributing 🤝

Contributions are welcome! Feel free to:
- Add new vulnerabilities
- Improve existing features
- Document testing scenarios
- Enhance documentation
- Fix bugs (that aren't intentional vulnerabilities)


## 📝 Blog Write-Up

A detailed walkthrough about this lab and my findings here:  
👇 Read the Blog By [DghostNinja](https://github.com/DghostNinja)

(https://dghostninja.github.io/posts/Vulnerable-Bank-API/)

> Ethical hacking only. Scope respected. Coffee consumed. ☕



## Disclaimer ⚠️

This application contains intentional security vulnerabilities for educational purposes. DO NOT:
- Deploy in production
- Use with real personal data
- Run on public networks
- Use for malicious purposes
- Store sensitive information

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---
Made with ❤️ for Security Education
