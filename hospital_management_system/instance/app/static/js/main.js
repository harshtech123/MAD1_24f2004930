// Hospital Management System JavaScript

// Global Variables
let currentUser = null;

// Document Ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips and popovers
    initializeBootstrapComponents();
    
    // Initialize form validations
    initializeFormValidations();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize date/time pickers
    initializeDateTimePickers();
    
    // Add animation classes
    addAnimations();
});

// Initialize Bootstrap Components
function initializeBootstrapComponents() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Form Validations
function initializeFormValidations() {
    // Bootstrap form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Real-time validation for specific fields
    const emailFields = document.querySelectorAll('input[type="email"]');
    emailFields.forEach(field => {
        field.addEventListener('blur', validateEmail);
    });

    const phoneFields = document.querySelectorAll('input[type="tel"]');
    phoneFields.forEach(field => {
        field.addEventListener('blur', validatePhone);
    });

    const passwordFields = document.querySelectorAll('input[type="password"]');
    passwordFields.forEach(field => {
        field.addEventListener('input', validatePasswordStrength);
    });
}

// Email Validation
function validateEmail(event) {
    const email = event.target.value.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (email && !emailRegex.test(email)) {
        event.target.classList.add('is-invalid');
        showFieldError(event.target, 'Please enter a valid email address');
    } else {
        event.target.classList.remove('is-invalid');
        hideFieldError(event.target);
    }
}

// Phone Validation
function validatePhone(event) {
    const phone = event.target.value.trim();
    const phoneRegex = /^\+?[\d\s\-\(\)]{10,}$/;
    
    if (phone && !phoneRegex.test(phone)) {
        event.target.classList.add('is-invalid');
        showFieldError(event.target, 'Please enter a valid phone number');
    } else {
        event.target.classList.remove('is-invalid');
        hideFieldError(event.target);
    }
}

// Password Strength Validation
function validatePasswordStrength(event) {
    const password = event.target.value;
    const strengthMeter = event.target.parentNode.querySelector('.password-strength');
    
    if (password.length === 0) {
        removePasswordStrength(event.target);
        return;
    }

    let strength = 0;
    let message = '';
    let color = '';

    // Length check
    if (password.length >= 8) strength++;
    else message = 'At least 8 characters required';

    // Uppercase check
    if (/[A-Z]/.test(password)) strength++;
    
    // Lowercase check
    if (/[a-z]/.test(password)) strength++;
    
    // Number check
    if (/\d/.test(password)) strength++;
    
    // Special character check
    if (/[^A-Za-z\d]/.test(password)) strength++;

    // Determine strength level
    if (strength <= 2) {
        message = 'Weak password';
        color = 'danger';
    } else if (strength <= 3) {
        message = 'Medium password';
        color = 'warning';
    } else {
        message = 'Strong password';
        color = 'success';
    }

    showPasswordStrength(event.target, message, color);
}

// Show Password Strength
function showPasswordStrength(field, message, color) {
    let strengthMeter = field.parentNode.querySelector('.password-strength');
    
    if (!strengthMeter) {
        strengthMeter = document.createElement('div');
        strengthMeter.className = 'password-strength form-text';
        field.parentNode.appendChild(strengthMeter);
    }
    
    strengthMeter.innerHTML = `<i class="fas fa-shield-alt text-${color}"></i> ${message}`;
    strengthMeter.className = `password-strength form-text text-${color}`;
}

// Remove Password Strength
function removePasswordStrength(field) {
    const strengthMeter = field.parentNode.querySelector('.password-strength');
    if (strengthMeter) {
        strengthMeter.remove();
    }
}

// Show Field Error
function showFieldError(field, message) {
    let errorDiv = field.parentNode.querySelector('.invalid-feedback');
    
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        field.parentNode.appendChild(errorDiv);
    }
    
    errorDiv.textContent = message;
}

// Hide Field Error
function hideFieldError(field) {
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// Initialize Search Functionality
function initializeSearch() {
    const searchInputs = document.querySelectorAll('.search-input');
    searchInputs.forEach(input => {
        input.addEventListener('input', debounce(performSearch, 300));
    });
}

// Debounce Function
function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

// Perform Search
function performSearch(event) {
    const query = event.target.value.trim().toLowerCase();
    const searchType = event.target.dataset.searchType;
    
    if (!searchType) return;
    
    const items = document.querySelectorAll(`[data-searchable="${searchType}"]`);
    
    items.forEach(item => {
        const searchText = item.dataset.searchText?.toLowerCase() || item.textContent.toLowerCase();
        
        if (query === '' || searchText.includes(query)) {
            item.style.display = '';
            item.classList.remove('fade-out');
            item.classList.add('fade-in');
        } else {
            item.style.display = 'none';
            item.classList.remove('fade-in');
            item.classList.add('fade-out');
        }
    });
    
    updateSearchResults(items, query);
}

// Update Search Results
function updateSearchResults(items, query) {
    const resultsContainer = document.querySelector('.search-results');
    if (!resultsContainer) return;
    
    const visibleItems = Array.from(items).filter(item => item.style.display !== 'none');
    const totalItems = items.length;
    
    if (query === '') {
        resultsContainer.innerHTML = `Showing all ${totalItems} items`;
    } else {
        resultsContainer.innerHTML = `Found ${visibleItems.length} of ${totalItems} items for "${query}"`;
    }
}

// Initialize Date/Time Pickers
function initializeDateTimePickers() {
    // Set minimum date to today for appointment booking
    const dateInputs = document.querySelectorAll('input[type="date"].future-only');
    const today = new Date().toISOString().split('T')[0];
    
    dateInputs.forEach(input => {
        input.min = today;
    });

    // Set maximum date to today for birth date
    const birthDateInputs = document.querySelectorAll('input[type="date"].past-only');
    birthDateInputs.forEach(input => {
        input.max = today;
    });
}

// Add Animations
function addAnimations() {
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fade-in');
        }, index * 100);
    });

    // Add slide-in animation to navigation items
    const navItems = document.querySelectorAll('.navbar-nav .nav-item');
    navItems.forEach((item, index) => {
        setTimeout(() => {
            item.classList.add('slide-in');
        }, index * 50);
    });
}

// Utility Functions

// Format Date
function formatDate(date) {
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    };
    return new Date(date).toLocaleDateString('en-US', options);
}

// Format Time
function formatTime(time) {
    return new Date(`1970-01-01T${time}`).toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
}

// Show Loading State
function showLoading(element, text = 'Loading...') {
    const originalContent = element.innerHTML;
    element.dataset.originalContent = originalContent;
    element.innerHTML = `
        <span class="loading me-2"></span>
        ${text}
    `;
    element.disabled = true;
}

// Hide Loading State
function hideLoading(element) {
    const originalContent = element.dataset.originalContent;
    if (originalContent) {
        element.innerHTML = originalContent;
        delete element.dataset.originalContent;
    }
    element.disabled = false;
}

// Show Toast Notification
function showToast(message, type = 'info') {
    const toastContainer = getOrCreateToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Get or Create Toast Container
function getOrCreateToastContainer() {
    let container = document.querySelector('.toast-container');
    
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '11';
        document.body.appendChild(container);
    }
    
    return container;
}

// Confirm Action
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// AJAX Helper Functions

// API Request
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    const config = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, config);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        showToast('An error occurred. Please try again.', 'danger');
        throw error;
    }
}

// Load Departments
async function loadDepartments() {
    try {
        const departments = await apiRequest('/api/departments');
        return departments;
    } catch (error) {
        console.error('Failed to load departments:', error);
        return [];
    }
}

// Load Doctors
async function loadDoctors(departmentId = null, search = null) {
    try {
        let url = '/api/doctors';
        const params = new URLSearchParams();
        
        if (departmentId) params.append('department_id', departmentId);
        if (search) params.append('search', search);
        
        if (params.toString()) {
            url += '?' + params.toString();
        }
        
        const doctors = await apiRequest(url);
        return doctors;
    } catch (error) {
        console.error('Failed to load doctors:', error);
        return [];
    }
}

// Form Submission Helpers

// Submit Form with AJAX
async function submitForm(form, successCallback = null) {
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    
    showLoading(submitButton, 'Submitting...');
    
    try {
        const response = await fetch(form.action || window.location.pathname, {
            method: form.method || 'POST',
            body: formData
        });
        
        if (response.ok) {
            if (successCallback) {
                successCallback(response);
            } else {
                showToast('Operation completed successfully!', 'success');
            }
        } else {
            throw new Error('Form submission failed');
        }
    } catch (error) {
        console.error('Form submission error:', error);
        showToast('An error occurred. Please try again.', 'danger');
    } finally {
        hideLoading(submitButton);
    }
}

// Chart Helper Functions (for dashboard charts)

// Create Appointment Status Chart
function createAppointmentChart(data) {
    const ctx = document.getElementById('appointmentChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Booked', 'Completed', 'Cancelled'],
            datasets: [{
                data: [data.booked, data.completed, data.cancelled],
                backgroundColor: ['#0dcaf0', '#198754', '#dc3545'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                }
            }
        }
    });
}

// Create Monthly Appointments Chart
function createMonthlyChart(data) {
    const ctx = document.getElementById('monthlyChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.months,
            datasets: [{
                label: 'Appointments',
                data: data.appointments,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Export functions for global use
window.HMS = {
    formatDate,
    formatTime,
    showToast,
    confirmAction,
    apiRequest,
    loadDepartments,
    loadDoctors,
    submitForm,
    createAppointmentChart,
    createMonthlyChart
};