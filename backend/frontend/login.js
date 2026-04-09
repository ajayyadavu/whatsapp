// ✅ Configuration
// const API_BASE_URL = 'http://localhost:8000/api/v1';
// const API_BASE_URL = 'https://abc123.ngrok-free.app/api/v1';
const API_BASE_URL = window.location.origin + '/api/v1';

// ✅ DOM Elements
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const loginMessage = document.getElementById('loginMessage');
const regMessage = document.getElementById('regMessage');
const loginLoading = document.getElementById('loginLoading');
const regLoading = document.getElementById('regLoading');
const loginBtn = document.getElementById('loginBtn');
const registerBtn = document.getElementById('registerBtn');

// ✅ Switch between login and register forms
function switchForm(formType) {
    const loginFormDiv = document.querySelector('.login-form');
    const registerFormDiv = document.querySelector('.register-form');
    
    if (formType === 'register') {
        loginFormDiv.classList.remove('show');
        registerFormDiv.classList.add('show');
    } else {
        registerFormDiv.classList.remove('show');
        loginFormDiv.classList.add('show');
    }
    
    // Clear messages
    clearMessages();
}

// ✅ Clear all messages
function clearMessages() {
    loginMessage.classList.remove('show', 'error', 'success');
    regMessage.classList.remove('show', 'error', 'success');
    loginMessage.textContent = '';
    regMessage.textContent = '';
}

// ✅ Show message
function showMessage(messageEl, text, type) {
    messageEl.textContent = text;
    messageEl.classList.add('show', type);
    console.log(`[${type}] ${text}`);
}

// ✅ LOGIN HANDLER
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearMessages();
    
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    
    if (!username || !password) {
        showMessage(loginMessage, '❌ Please fill in all fields', 'error');
        return;
    }
    
    loginBtn.disabled = true;
    loginLoading.classList.add('show');
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage(loginMessage, '✅ Login successful! Redirecting...', 'success');
            
            // ✅ Store token and user info
            localStorage.setItem('accessToken', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            
            // Redirect to chat page after 2 seconds
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 2000);
        } else {
            showMessage(loginMessage, `❌ ${data.detail || 'Login failed'}`, 'error');
        }
    } catch (error) {
        showMessage(loginMessage, `❌ Error: ${error.message}`, 'error');
        console.error('Login error:', error);
    } finally {
        loginBtn.disabled = false;
        loginLoading.classList.remove('show');
    }
});

// ✅ REGISTER HANDLER
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearMessages();
    
    const username = document.getElementById('regUsername').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const password = document.getElementById('regPassword').value;
    
    if (!username || !email || !password) {
        showMessage(regMessage, '❌ Please fill in all fields', 'error');
        return;
    }
    
    // ✅ Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showMessage(regMessage, '❌ Please enter a valid email', 'error');
        return;
    }
    
    // ✅ Password strength check
    if (password.length < 6) {
        showMessage(regMessage, '❌ Password must be at least 6 characters', 'error');
        return;
    }
    
    registerBtn.disabled = true;
    regLoading.classList.add('show');
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                email: email,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage(regMessage, '✅ Account created! Switching to login...', 'success');
            
            // Clear form
            registerForm.reset();
            
            // Switch to login form after 2 seconds
            setTimeout(() => {
                switchForm('login');
                document.getElementById('loginUsername').value = username;
                showMessage(loginMessage, '✅ Registration successful! Please login.', 'success');
            }, 2000);
        } else {
            showMessage(regMessage, `❌ ${data.detail || 'Registration failed'}`, 'error');
        }
    } catch (error) {
        showMessage(regMessage, `❌ Error: ${error.message}`, 'error');
        console.error('Register error:', error);
    } finally {
        registerBtn.disabled = false;
        regLoading.classList.remove('show');
    }
});

// ✅ Check if user is already logged in
function checkAuthStatus() {
    const token = localStorage.getItem('accessToken');
    if (token) {
        // User is already logged in, redirect to chat
        window.location.href = 'index.html';
    }
}

// Run on page load
window.addEventListener('load', checkAuthStatus);
