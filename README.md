# Vulnerable Bank Application 🏦

A deliberately vulnerable web application for practicing application security testing, secure code review and implementing security in CI/CD pipelines.

⚠️ **WARNING: This application is intentionally vulnerable and should only be used for educational purposes in isolated environments.**

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

### Implemented Vulnerabilities

1. **Authentication & Authorization**
   - SQL Injection in login
   - Weak JWT implementation
   - Broken object level authorization (BOLA)
   - Broken object property level authorization (BOPLA)- Mass Assignment & Excessive Data Exposure
   - Weak password reset mechanism (3-digit PIN)

2. **Data Security**
   - Information disclosure
   - Sensitive data exposure
   - Plaintext password storage
   - SQL injection points

3. **File Operations**
   - Unrestricted file upload
   - Path traversal vulnerabilities
   - No file type validation
   - Directory traversal

4. **Session Management**
   - Token vulnerabilities
   - No session expiration
   - Weak secret keys

5. **Client and Server-Side Flaws**
   - Cross Site Scripting (XSS)
   - Cross Site Request Forgery (CSRF)

## Installation & Setup 🚀

### Option 1: Using Docker (Recommended)

#### Prerequisites
- Docker installed

#### Steps
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

### Option 2: Local Installation (Without Docker)

#### Prerequisites
- Python 3.9 or higher
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

5. Run the application:
```bash
# On Windows
python app.py

# On Linux/Mac
python3 app.py
```

### Accessing the Application
Once running, access the application at:
```
http://localhost:5000
```

### Accessing the Application
Once running, access the api documentation at:
```
http://localhost:5000/api/docs
```

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

## Testing Guide 🎯

### Authentication Testing
1. SQL Injection in login
2. Weak password reset (bruteforce 3-digit PIN)
3. JWT token manipulation
4. Username enumeration

### Authorization Testing
1. Access other users' transaction history via account number
2. Upload malicious files
3. Access admin panel
4. Manipulate JWT claims
5. Exploit BOPLA (Excessive Data Exposure and Mass Assignment) to esclate privilege and increase balance during registration

### File Upload Testing
1. Upload unauthorized file types
2. Attempt path traversal
3. Upload oversized files
4. Test file overwrite scenarios

### Logic Flaw Testing
1. Race Conditions
2. Funds Transfer flaws

## Contributing 🤝

Contributions are welcome! Feel free to:
- Add new vulnerabilities
- Improve existing features
- Add security testing tools
- Enhance documentation
- Fix bugs

## Disclaimer ⚠️

This application contains intentional security vulnerabilities for educational purposes. DO NOT:
- Deploy in production
- Use with real personal data
- Run on public networks
- Use for malicious purposes


---
Made with ❤️ for Security Education