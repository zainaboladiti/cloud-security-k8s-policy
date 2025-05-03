// Set current date
document.addEventListener('DOMContentLoaded', function() {
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const today = new Date();
    document.getElementById('current-date').textContent = today.toLocaleDateString('en-US', options);
});

// Vulnerability: Token stored in localStorage
document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('jwt_token');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    fetchTransactions();

    // Add event listeners
    document.getElementById('transferForm').addEventListener('submit', handleTransfer);
    document.getElementById('loanForm').addEventListener('submit', handleLoanRequest);
    document.getElementById('profileUploadForm').addEventListener('submit', handleProfileUpload);
    
    // Add virtual cards event listener
    document.getElementById('createCardForm').addEventListener('submit', handleCreateCard);
    
    // Load virtual cards
    fetchVirtualCards();

    // Add bill payment functions
    document.getElementById('payBillForm').addEventListener('submit', handleBillPayment);
    
    // Load initial data
    loadBillCategories();
    loadPaymentHistory();

    // Set active nav link based on URL hash
    const hash = window.location.hash || '#profile';
    const activeLink = document.querySelector(`.nav-link[href='${hash}']`);
    if (activeLink) {
        setActiveLink(activeLink);
    }
    
    // Add scroll event listener
    window.addEventListener('scroll', handleScroll);
});

// Navigation functions
function setActiveLink(element) {
    // Remove active class from all links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Add active class to clicked link
    element.classList.add('active');
    
    // For mobile view, close the menu
    if (window.innerWidth <= 768) {
        document.querySelector('.side-panel').classList.remove('active');
    }
}

function toggleSidePanel() {
    document.querySelector('.side-panel').classList.toggle('active');
}

function handleScroll() {
    const sections = document.querySelectorAll('.dashboard-section');
    const navLinks = document.querySelectorAll('.nav-link');
    
    let current = '';
    
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        if (pageYOffset >= (sectionTop - 200)) {
            current = '#' + section.getAttribute('id');
        }
    });
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === current) {
            link.classList.add('active');
        }
    });
}

// Transfer money handler
async function handleTransfer(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const jsonData = {};
    formData.forEach((value, key) => jsonData[key] = value);

    try {
        const response = await fetch('/transfer', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(jsonData)
        });

        const data = await response.json();
        if (data.status === 'success') {
            // Update message and balance
            document.getElementById('message').innerHTML = data.message;
            document.getElementById('message').style.color = 'green';
            document.getElementById('balance').textContent = data.new_balance;
            
            // Refresh transactions
            fetchTransactions();
            
            // Clear form
            event.target.reset();
        } else {
            document.getElementById('message').innerHTML = data.message;
            document.getElementById('message').style.color = 'red';
        }
    } catch (error) {
        document.getElementById('message').innerHTML = 'Transfer failed';
        document.getElementById('message').style.color = 'red';
    }
}

// Loan request handler
async function handleLoanRequest(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const jsonData = {};
    formData.forEach((value, key) => jsonData[key] = value);

    try {
        const response = await fetch('/request_loan', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(jsonData)
        });

        const data = await response.json();
        if (data.status === 'success') {
            document.getElementById('message').innerHTML = 'Loan requested successfully, our staff will review and approve!';
            document.getElementById('message').style.color = 'green';
            
            // Check if loans section exists, if not create it
            let loansSection = document.querySelector('.loans-section');
            if (!loansSection) {
                // Create new loans section
                loansSection = document.createElement('div');
                loansSection.className = 'loans-section';
                loansSection.style.marginTop = '2rem';
                loansSection.innerHTML = `
                    <h3 style="margin-bottom: 1rem;">Your Loan Applications</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Amount</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                `;
                // Add it to the loans section
                document.getElementById('loans').appendChild(loansSection);
            }
            
            // Add new loan to the table
            const loansTableBody = loansSection.querySelector('tbody');
            const newRow = document.createElement('tr');
            newRow.innerHTML = `
                <td>$${jsonData.amount}</td>
                <td><span class="status-pending">pending</span></td>
            `;
            loansTableBody.appendChild(newRow);
            
            // Clear form
            event.target.reset();
        } else {
            document.getElementById('message').innerHTML = data.message;
            document.getElementById('message').style.color = 'red';
        }
    } catch (error) {
        document.getElementById('message').innerHTML = 'Loan request failed';
        document.getElementById('message').style.color = 'red';
    }
}

// Profile picture upload handler
async function handleProfileUpload(event) {
    event.preventDefault();
    const formData = new FormData(event.target);

    try {
        const response = await fetch('/upload_profile_picture', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
            },
            body: formData
        });

        const data = await response.json();
        if (data.status === 'success') {
            // Vulnerability: No sanitization of file_path
            const img = document.getElementById('profile-picture');
            img.src = '/' + data.file_path + '?v=' + new Date().getTime(); // Prevent caching
            document.getElementById('upload-message').innerText = 'Upload successful!';
            document.getElementById('upload-message').style.color = 'green';
            event.target.reset();
        } else {
            document.getElementById('upload-message').innerText = data.message;
            document.getElementById('upload-message').style.color = 'red';
        }
    } catch (error) {
        document.getElementById('upload-message').innerText = 'Upload failed';
        document.getElementById('upload-message').style.color = 'red';
    }
}


// Fetch transactions
// Vulnerability: No rate limiting on transaction fetches
async function fetchTransactions() {
    try {
        const accountNumber = document.getElementById('account-number').textContent;
        const response = await fetch(`/transactions/${accountNumber}`, {
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
            }
        });

        const data = await response.json();
        if (data.status === 'success') {
            if (data.transactions.length === 0) {
                document.getElementById('transaction-list').innerHTML = '<p style="text-align: center; padding: 2rem;">No transactions found</p>';
                return;
            }
            
            // Vulnerability: innerHTML used with unsanitized data
            const transactionHtml = data.transactions.map(t => {
                const isOutgoing = t.from_account === accountNumber;
                const transactionType = isOutgoing ? 'sent' : 'received';
                
                return `
                    <div class="transaction-item ${transactionType}">
                        <div class="transaction-details">
                            <div class="transaction-account">
                                ${isOutgoing ? 'To: ' + t.to_account : 'From: ' + t.from_account}
                            </div>
                            <div class="transaction-date">${t.timestamp}</div>
                            ${t.description ? `<div class="transaction-description">${t.description}</div>` : ''}
                        </div>
                        <div class="transaction-amount ${transactionType}">
                            ${isOutgoing ? '-' : '+'}$${Math.abs(t.amount)}
                        </div>
                    </div>
                `;
            }).join('');
            
            document.getElementById('transaction-list').innerHTML = transactionHtml;
        } else {
            document.getElementById('transaction-list').innerHTML = '<p style="text-align: center; padding: 2rem;">Error loading transactions</p>';
        }
    } catch (error) {
        document.getElementById('transaction-list').innerHTML = '<p style="text-align: center; padding: 2rem;">Error loading transactions</p>';
    }
}

// Virtual Cards Management
let virtualCards = [];

async function fetchVirtualCards() {
    try {
        const response = await fetch('/api/virtual-cards', {
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
            }
        });

        const data = await response.json();
        if (data.status === 'success') {
            virtualCards = data.cards;
            renderVirtualCards();
        } else {
            document.getElementById('virtual-cards-list').innerHTML = '<p style="text-align: center;">No virtual cards found</p>';
        }
    } catch (error) {
        document.getElementById('virtual-cards-list').innerHTML = '<p style="text-align: center;">Error loading virtual cards</p>';
    }
}

function renderVirtualCards() {
    const container = document.getElementById('virtual-cards-list');
    if (virtualCards.length === 0) {
        container.innerHTML = '<p style="text-align: center;">No virtual cards found. Create one to get started.</p>';
        return;
    }
    
    // Vulnerability: XSS possible in card rendering
    container.innerHTML = virtualCards.map(card => `
        <div class="virtual-card ${card.is_frozen ? 'frozen' : ''}" id="card-${card.id}">
            <div class="card-type">${card.card_type.toUpperCase()}</div>
            <div class="card-number">${formatCardNumber(card.card_number)}</div>
            <div class="card-details">
                <div>Exp: ${card.expiry_date}</div>
                <div>CVV: ${card.cvv}</div>
            </div>
            <div>Limit: $${card.limit}</div>
            <div>Balance: $${card.balance}</div>
            <div class="card-actions">
                <button onclick="toggleCardFreeze(${card.id})">${card.is_frozen ? 'Unfreeze' : 'Freeze'}</button>
                <button onclick="showCardDetails(${card.id})">Details</button>
                <button onclick="showTransactionHistory(${card.id})">History</button>
                <button onclick="showUpdateLimit(${card.id})">Update Limit</button>
            </div>
        </div>
    `).join('');
}

function formatCardNumber(number) {
    return number.match(/.{1,4}/g).join(' ');
}

function showCreateCardModal() {
    document.getElementById('createCardModal').style.display = 'flex';
}

function hideCreateCardModal() {
    document.getElementById('createCardModal').style.display = 'none';
    document.getElementById('createCardForm').reset();
}

function showCardDetails(cardId) {
    const card = virtualCards.find(c => c.id === cardId);
    if (!card) return;

    const modal = document.getElementById('cardDetailsModal');
    const content = document.getElementById('cardDetailsContent');
    
    content.innerHTML = `
        <div class="form-group">
            <label>Card Number</label>
            <p>${formatCardNumber(card.card_number)}</p>
        </div>
        <div class="form-group">
            <label>CVV</label>
            <p>${card.cvv}</p>
        </div>
        <div class="form-group">
            <label>Expiry Date</label>
            <p>${card.expiry_date}</p>
        </div>
        <div class="form-group">
            <label>Card Type</label>
            <p>${card.card_type}</p>
        </div>
        <div class="form-group">
            <label>Current Limit</label>
            <p>$${card.limit}</p>
        </div>
        <div class="form-group">
            <label>Current Balance</label>
            <p>$${card.balance}</p>
        </div>
        <div class="form-group">
            <label>Status</label>
            <p>${card.is_frozen ? 'Frozen' : 'Active'}</p>
        </div>
        <div class="form-group">
            <label>Created</label>
            <p>${new Date(card.created_at).toLocaleDateString()}</p>
        </div>
    `;
    
    modal.style.display = 'flex';
}

function hideCardDetailsModal() {
    document.getElementById('cardDetailsModal').style.display = 'none';
}

async function handleCreateCard(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const jsonData = {};
    formData.forEach((value, key) => jsonData[key] = value);

    try {
        const response = await fetch('/api/virtual-cards/create', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(jsonData)
        });

        const data = await response.json();
        if (data.status === 'success') {
            hideCreateCardModal();
            await fetchVirtualCards();
            
            document.getElementById('message').innerHTML = 'Virtual card created successfully!';
            document.getElementById('message').style.color = 'green';
        } else {
            document.getElementById('message').innerHTML = data.message;
            document.getElementById('message').style.color = 'red';
        }
    } catch (error) {
        document.getElementById('message').innerHTML = 'Failed to create virtual card';
        document.getElementById('message').style.color = 'red';
    }
}

async function toggleCardFreeze(cardId) {
    try {
        const response = await fetch(`/api/virtual-cards/${cardId}/toggle-freeze`, {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
            }
        });

        const data = await response.json();
        if (data.status === 'success') {
            await fetchVirtualCards();
        } else {
            document.getElementById('message').innerHTML = data.message;
            document.getElementById('message').style.color = 'red';
        }
    } catch (error) {
        document.getElementById('message').innerHTML = 'Failed to freeze/unfreeze card';
        document.getElementById('message').style.color = 'red';
    }
}

async function showTransactionHistory(cardId) {
    try {
        const response = await fetch(`/api/virtual-cards/${cardId}/transactions`, {
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
            }
        });

        const data = await response.json();
        if (data.status === 'success') {
            const modal = document.getElementById('cardDetailsModal');
            const content = document.getElementById('cardDetailsContent');
            
            if (data.transactions.length === 0) {
                content.innerHTML = '<p style="text-align: center; padding: 1rem;">No transactions found for this card</p>';
                modal.style.display = 'flex';
                return;
            }
            
            content.innerHTML = `
                <h4>Transaction History</h4>
                <div class="transaction-list">
                    ${data.transactions.map(t => `
                        <div class="transaction-item">
                            <div class="transaction-details">
                                <div class="transaction-account">${t.merchant}</div>
                                <div class="transaction-date">${new Date(t.timestamp).toLocaleString()}</div>
                            </div>
                            <div class="transaction-amount">${t.amount}</div>
                        </div>
                    `).join('')}
                </div>
            `;
            
            modal.style.display = 'flex';
        } else {
            document.getElementById('message').innerHTML = data.message;
            document.getElementById('message').style.color = 'red';
        }
    } catch (error) {
        document.getElementById('message').innerHTML = 'Failed to load transaction history';
        document.getElementById('message').style.color = 'red';
    }
}

async function showUpdateLimit(cardId) {
    const card = virtualCards.find(c => c.id === cardId);
    if (!card) return;

    const modal = document.getElementById('cardDetailsModal');
    const content = document.getElementById('cardDetailsContent');
    
    // Vulnerability: Exposing form that allows updating any field
    content.innerHTML = `
        <h4>Update Card Limit</h4>
        <form id="updateCardForm" onsubmit="return handleCardUpdate(event, ${cardId})">
            <div class="form-group">
                <label for="card_limit_update">Card Limit</label>
                <input type="number" id="card_limit_update" name="card_limit" value="${card.limit}" step="0.01" required>
            </div>
            <div class="modal-footer">
                <button type="submit">Update Limit</button>
                <button type="button" onclick="hideCardDetailsModal()">Cancel</button>
            </div>
        </form>
    `;
    
    modal.style.display = 'flex';
}

// Add handleCardUpdate function
async function handleCardUpdate(event, cardId) {
    event.preventDefault();
    const formData = new FormData(event.target);
    
    // Only send card_limit from UI
    const jsonData = {
        card_limit: parseFloat(formData.get('card_limit'))
    };

    try {
        // Vulnerability: Sending all form data including sensitive fields
        const response = await fetch(`/api/virtual-cards/${cardId}/update-limit`, {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(jsonData)
        });

        const data = await response.json();
        if (data.status === 'success') {
            await fetchVirtualCards();
            hideCardDetailsModal();
            document.getElementById('message').innerHTML = 'Card limit updated successfully';
            document.getElementById('message').style.color = 'green';
        } else {
            document.getElementById('message').innerHTML = data.message;
            document.getElementById('message').style.color = 'red';
        }
    } catch (error) {
        document.getElementById('message').innerHTML = 'Error updating card limit';
        document.getElementById('message').style.color = 'red';
    }
    
    return false; // Prevent form submission
}

// Bill Payments Functions
function showPayBillModal() {
    document.getElementById('payBillModal').style.display = 'flex';
}

function hidePayBillModal() {
    document.getElementById('payBillModal').style.display = 'none';
    document.getElementById('payBillForm').reset();
    document.getElementById('biller').disabled = true;
    document.getElementById('cardSelection').style.display = 'none';
}

// Load bill categories
async function loadBillCategories() {
    try {
        const response = await fetch('/api/bill-categories');
        const data = await response.json();
        
        if (data.status === 'success') {
            const select = document.getElementById('billCategory');
            // Vulnerability: XSS possible in category name and description
            select.innerHTML = `
                <option value="">Select Category</option>
                ${data.categories.map(cat => `
                    <option value="${cat.id}">${cat.name}</option>
                `).join('')}
            `;
        }
    } catch (error) {
        console.error('Error loading bill categories:', error);
    }
}

// Load billers for selected category
async function loadBillers(categoryId) {
    if (!categoryId) {
        const select = document.getElementById('biller');
        select.innerHTML = '<option value="">Select Biller</option>';
        select.disabled = true;
        return;
    }
    
    try {
        const response = await fetch(`/api/billers/by-category/${categoryId}`);
        const data = await response.json();
        
        const select = document.getElementById('biller');
        if (data.status === 'success') {
            // Create a Map to store unique billers by name
            const billerMap = new Map();
            
            // Only keep the first occurrence of each biller name
            data.billers.forEach(biller => {
                if (!billerMap.has(biller.name)) {
                    billerMap.set(biller.name, biller);
                }
            });

            // Convert Map values back to array
            const uniqueBillers = Array.from(billerMap.values());

            // Sort billers by name for consistency
            uniqueBillers.sort((a, b) => a.name.localeCompare(b.name));

            select.innerHTML = `
                <option value="">Select Biller</option>
                ${uniqueBillers.map(biller => `
                    <option value="${biller.id}" 
                            data-min="${biller.minimum_amount}"
                            data-max="${biller.maximum_amount || ''}"
                    >${biller.name}</option>
                `).join('')}
            `;
            select.disabled = false;
        } else {
            select.innerHTML = '<option value="">No billers available</option>';
            select.disabled = true;
        }
    } catch (error) {
        console.error('Error loading billers:', error);
        const select = document.getElementById('biller');
        select.innerHTML = '<option value="">Error loading billers</option>';
        select.disabled = true;
    }
}

// Toggle card selection based on payment method
function toggleCardSelection(method) {
    const cardSelection = document.getElementById('cardSelection');
    if (method === 'virtual_card') {
        cardSelection.style.display = 'block';
        loadVirtualCardsForPayment();  // Load the cards
    } else {
        cardSelection.style.display = 'none';
    }
}

// Function to load virtual cards for payment selection
async function loadVirtualCardsForPayment() {
    try {
        const response = await fetch('/api/virtual-cards', {
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
            }
        });

        const data = await response.json();
        if (data.status === 'success') {
            const select = document.querySelector('select[name="card_id"]');
            // Only show non-frozen cards with available balance
            select.innerHTML = `
                <option value="">Select Card</option>
                ${data.cards.filter(card => !card.is_frozen).map(card => `
                    <option value="${card.id}">
                        Card ending in ${card.card_number.slice(-4)} 
                        (Balance: $${card.balance})
                    </option>
                `).join('')}
            `;
        }
    } catch (error) {
        console.error('Error loading virtual cards:', error);
    }
}

// Handle bill payment submission
async function handleBillPayment(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const jsonData = {
        biller_id: parseInt(formData.get('biller_id')),
        amount: parseFloat(formData.get('amount')),
        payment_method: formData.get('payment_method'),
        description: formData.get('description') || 'Bill Payment'
    };
    
    if (jsonData.payment_method === 'virtual_card') {
        jsonData.card_id = parseInt(formData.get('card_id'));
    }

    try {
        const response = await fetch('/api/bill-payments/create', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(jsonData)
        });

        const data = await response.json();
        if (data.status === 'success') {
            hidePayBillModal();
            document.getElementById('message').innerHTML = 'Bill payment successful!';
            document.getElementById('message').style.color = 'green';
            await loadPaymentHistory();
            
            // Refresh balances if necessary
            if (jsonData.payment_method === 'virtual_card') {
                await fetchVirtualCards();
            } else {
                // Update account balance
                const balanceElement = document.getElementById('balance');
                const currentBalance = parseFloat(balanceElement.textContent);
                balanceElement.textContent = (currentBalance - jsonData.amount).toFixed(2);
            }
        } else {
            document.getElementById('message').innerHTML = data.message;
            document.getElementById('message').style.color = 'red';
        }
    } catch (error) {
        document.getElementById('message').innerHTML = 'Payment failed';
        document.getElementById('message').style.color = 'red';
    }
}

// Load payment history
async function loadPaymentHistory() {
    try {
        const response = await fetch('/api/bill-payments/history', {
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
            }
        });

        const data = await response.json();
        if (data.status === 'success') {
            const container = document.getElementById('bill-payments-list');
            if (data.payments.length === 0) {
                container.innerHTML = '<p style="text-align: center; padding: 2rem;">No bill payments found</p>';
                return;
            }

            // Vulnerability: XSS possible in payment details
            container.innerHTML = data.payments.map(payment => `
                <div class="payment-item">
                    <div class="payment-header">
                        <div class="payment-amount">$${payment.amount}</div>
                        <div class="payment-status">${payment.status}</div>
                    </div>
                    <div class="payment-details">
                        <div>Biller: ${payment.biller_name}</div>
                        <div>Category: ${payment.category_name}</div>
                        <div>Payment Method: ${payment.payment_method}
                            ${payment.card_number ? ` (Card ending in ${payment.card_number.slice(-4)})` : ''}
                        </div>
                        <div>Reference: ${payment.reference}</div>
                        <div>Date: ${new Date(payment.created_at).toLocaleString()}</div>
                        ${payment.description ? `<div>Description: ${payment.description}</div>` : ''}
                    </div>
                </div>
            `).join('');
        } else {
            document.getElementById('bill-payments-list').innerHTML = '<p style="text-align: center; padding: 2rem;">Error loading payment history</p>';
        }
    } catch (error) {
        document.getElementById('bill-payments-list').innerHTML = '<p style="text-align: center; padding: 2rem;">Error loading payment history</p>';
    }
}

// Vulnerability: No server-side token invalidation
function logout() {
    localStorage.removeItem('jwt_token');
    window.location.href = '/login';
}
