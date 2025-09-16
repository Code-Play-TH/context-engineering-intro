/**
 * Factory ERP System - Main JavaScript Application
 * 
 * Handles all frontend interactions, API calls, and UI updates
 */

// Global app configuration
const APP_CONFIG = {
    apiBaseUrl: '/api',
    csrfToken: null,
    currentUser: null,
    debug: window.location.hostname === 'localhost'
};

// Utility functions
const Utils = {
    /**
     * Make authenticated API request
     */
    async apiRequest(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        };

        // Add JWT token if available
        const token = localStorage.getItem('access_token');
        if (token) {
            defaultOptions.headers['Authorization'] = `Bearer ${token}`;
        }

        // Add CSRF token if available
        if (APP_CONFIG.csrfToken) {
            defaultOptions.headers['X-CSRF-Token'] = APP_CONFIG.csrfToken;
        }

        const finalOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        try {
            const response = await fetch(`${APP_CONFIG.apiBaseUrl}${endpoint}`, finalOptions);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                
                // Handle authentication errors
                if (response.status === 401) {
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('user');
                    window.location.href = '/auth/login';
                    return;
                }
                
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return response;
        } catch (error) {
            console.error('API Request failed:', error);
            this.showNotification('API request failed: ' + error.message, 'error');
            throw error;
        }
    },

    /**
     * Show loading overlay
     */
    showLoading(message = 'Loading...') {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.querySelector('span').textContent = message;
            overlay.classList.remove('hidden');
        }
    },

    /**
     * Hide loading overlay
     */
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.add('hidden');
        }
    },

    /**
     * Show notification
     */
    showNotification(message, type = 'info', duration = 5000) {
        const notificationArea = document.getElementById('notification-area');
        if (!notificationArea) return;

        const notification = document.createElement('div');
        notification.className = `notification ${type} fade-in mb-4`;
        
        const iconMap = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        notification.innerHTML = `
            <div class="p-4">
                <div class="flex">
                    <div class="flex-shrink-0">
                        <i class="${iconMap[type] || iconMap.info} h-5 w-5 text-${type === 'error' ? 'red' : type === 'success' ? 'green' : type === 'warning' ? 'yellow' : 'blue'}-400"></i>
                    </div>
                    <div class="ml-3">
                        <p class="text-sm font-medium text-gray-900">${message}</p>
                    </div>
                    <div class="ml-auto pl-3">
                        <div class="-mx-1.5 -my-1.5">
                            <button type="button" class="notification-close inline-flex bg-white rounded-md p-1.5 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                                <span class="sr-only">Dismiss</span>
                                <i class="fas fa-times h-4 w-4"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add close button functionality
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });

        notificationArea.appendChild(notification);

        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, duration);
        }
    },

    /**
     * Format number with commas
     */
    formatNumber(num) {
        return new Intl.NumberFormat().format(num);
    },

    /**
     * Format currency
     */
    formatCurrency(amount, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(amount);
    },

    /**
     * Format date
     */
    formatDate(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        };
        
        return new Intl.DateTimeFormat('en-US', {
            ...defaultOptions,
            ...options
        }).format(new Date(date));
    },

    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Validate email
     */
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    /**
     * Get query parameter
     */
    getQueryParam(param) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param);
    },

    /**
     * Set query parameter
     */
    setQueryParam(param, value) {
        const url = new URL(window.location);
        url.searchParams.set(param, value);
        window.history.pushState({}, '', url);
    }
};

// Excel Integration Functions
const ExcelIntegration = {
    /**
     * Upload Excel file
     */
    async uploadFile(file, fileType, validateOnly = false) {
        const formData = new FormData();
        formData.append('file', file);
        
        const endpoint = fileType === 'products' 
            ? `/excel/upload/products?validate_only=${validateOnly}`
            : `/excel/upload/customer-requirements?validate_only=${validateOnly}`;

        try {
            Utils.showLoading('Processing Excel file...');
            
            const response = await fetch(`${APP_CONFIG.apiBaseUrl}${endpoint}`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.detail || 'Upload failed');
            }

            Utils.hideLoading();
            
            if (validateOnly) {
                Utils.showNotification('File validation completed', 'success');
            } else {
                Utils.showNotification(
                    `Upload completed: ${result.created} created, ${result.updated} updated`,
                    'success'
                );
            }
            
            return result;
        } catch (error) {
            Utils.hideLoading();
            Utils.showNotification('Upload failed: ' + error.message, 'error');
            throw error;
        }
    },

    /**
     * Download Excel file
     */
    async downloadFile(type, filters = {}) {
        const queryParams = new URLSearchParams(filters).toString();
        const endpoint = `${APP_CONFIG.apiBaseUrl}/excel/download/${type}?${queryParams}`;
        
        try {
            Utils.showLoading('Generating Excel file...');
            
            const response = await fetch(endpoint);
            
            if (!response.ok) {
                throw new Error('Download failed');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${type}_${new Date().toISOString().split('T')[0]}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            Utils.hideLoading();
            Utils.showNotification('File downloaded successfully', 'success');
        } catch (error) {
            Utils.hideLoading();
            Utils.showNotification('Download failed: ' + error.message, 'error');
        }
    },

    /**
     * Download template
     */
    async downloadTemplate(templateType) {
        const endpoint = `${APP_CONFIG.apiBaseUrl}/excel/templates/${templateType}`;
        
        try {
            const response = await fetch(endpoint);
            
            if (!response.ok) {
                throw new Error('Template download failed');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${templateType}_template.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            Utils.showNotification('Template downloaded successfully', 'success');
        } catch (error) {
            Utils.showNotification('Template download failed: ' + error.message, 'error');
        }
    }
};

// ERPNext Integration Functions
const ERPNextIntegration = {
    /**
     * Test ERPNext connection
     */
    async testConnection() {
        try {
            Utils.showLoading('Testing ERPNext connection...');
            const result = await Utils.apiRequest('/erpnext/test-connection');
            Utils.hideLoading();
            
            if (result.connected) {
                Utils.showNotification('ERPNext connection successful', 'success');
            } else {
                Utils.showNotification('ERPNext connection failed: ' + result.error, 'error');
            }
            
            return result;
        } catch (error) {
            Utils.hideLoading();
            return { connected: false, error: error.message };
        }
    },

    /**
     * Sync data to ERPNext
     */
    async syncData(syncRequest) {
        try {
            Utils.showLoading('Synchronizing with ERPNext...');
            
            const result = await Utils.apiRequest('/erpnext/sync/bulk', {
                method: 'POST',
                body: JSON.stringify(syncRequest)
            });
            
            Utils.hideLoading();
            
            if (result.success) {
                Utils.showNotification('Synchronization completed successfully', 'success');
            } else {
                Utils.showNotification('Synchronization completed with errors: ' + result.message, 'warning');
            }
            
            return result;
        } catch (error) {
            Utils.hideLoading();
            Utils.showNotification('Synchronization failed: ' + error.message, 'error');
            throw error;
        }
    }
};

// Form handling
const FormHandler = {
    /**
     * Handle form submission with validation
     */
    async submitForm(form, options = {}) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // Basic validation
        const errors = this.validateForm(form);
        if (errors.length > 0) {
            this.displayFormErrors(form, errors);
            return false;
        }
        
        try {
            Utils.showLoading('Submitting form...');
            
            const endpoint = options.endpoint || form.action || form.dataset.endpoint;
            const method = options.method || form.method || 'POST';
            
            const result = await Utils.apiRequest(endpoint, {
                method: method.toUpperCase(),
                body: JSON.stringify(data)
            });
            
            Utils.hideLoading();
            
            if (options.onSuccess) {
                options.onSuccess(result);
            } else {
                Utils.showNotification('Form submitted successfully', 'success');
                if (options.redirect) {
                    window.location.href = options.redirect;
                }
            }
            
            return result;
        } catch (error) {
            Utils.hideLoading();
            if (options.onError) {
                options.onError(error);
            }
            return false;
        }
    },

    /**
     * Validate form fields
     */
    validateForm(form) {
        const errors = [];
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        
        inputs.forEach(input => {
            if (!input.value.trim()) {
                errors.push({
                    field: input.name,
                    message: `${this.getFieldLabel(input)} is required`
                });
            }
            
            // Email validation
            if (input.type === 'email' && input.value && !Utils.isValidEmail(input.value)) {
                errors.push({
                    field: input.name,
                    message: 'Please enter a valid email address'
                });
            }
            
            // Number validation
            if (input.type === 'number' && input.value) {
                const min = parseFloat(input.min);
                const max = parseFloat(input.max);
                const value = parseFloat(input.value);
                
                if (!isNaN(min) && value < min) {
                    errors.push({
                        field: input.name,
                        message: `${this.getFieldLabel(input)} must be at least ${min}`
                    });
                }
                
                if (!isNaN(max) && value > max) {
                    errors.push({
                        field: input.name,
                        message: `${this.getFieldLabel(input)} must not exceed ${max}`
                    });
                }
            }
        });
        
        return errors;
    },

    /**
     * Display form errors
     */
    displayFormErrors(form, errors) {
        // Clear existing errors
        form.querySelectorAll('.form-error').forEach(error => error.remove());
        form.querySelectorAll('.error').forEach(input => input.classList.remove('error'));
        
        errors.forEach(error => {
            const input = form.querySelector(`[name="${error.field}"]`);
            if (input) {
                input.classList.add('error');
                
                const errorDiv = document.createElement('div');
                errorDiv.className = 'form-error';
                errorDiv.textContent = error.message;
                
                input.parentNode.appendChild(errorDiv);
            }
        });
    },

    /**
     * Get field label
     */
    getFieldLabel(input) {
        const label = input.closest('.form-group')?.querySelector('label');
        return label?.textContent?.replace('*', '').trim() || input.name;
    }
};

// Data table functionality
const DataTable = {
    /**
     * Initialize sortable table
     */
    initSortableTable(table) {
        const headers = table.querySelectorAll('th[data-sortable]');
        
        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                this.sortTable(table, header);
            });
        });
    },

    /**
     * Sort table by column
     */
    sortTable(table, header) {
        const column = header.dataset.sortable;
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        const currentSort = header.dataset.sort;
        const isAsc = currentSort !== 'asc';
        
        // Clear all sort indicators
        table.querySelectorAll('th').forEach(th => {
            th.dataset.sort = '';
            th.classList.remove('sort-asc', 'sort-desc');
        });
        
        // Set current sort
        header.dataset.sort = isAsc ? 'asc' : 'desc';
        header.classList.add(isAsc ? 'sort-asc' : 'sort-desc');
        
        // Sort rows
        rows.sort((a, b) => {
            const aVal = a.querySelector(`td[data-column="${column}"]`)?.textContent?.trim() || '';
            const bVal = b.querySelector(`td[data-column="${column}"]`)?.textContent?.trim() || '';
            
            // Try to parse as numbers
            const aNum = parseFloat(aVal);
            const bNum = parseFloat(bVal);
            
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return isAsc ? aNum - bNum : bNum - aNum;
            }
            
            // String comparison
            return isAsc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        });
        
        // Re-append sorted rows
        rows.forEach(row => tbody.appendChild(row));
    },

    /**
     * Filter table rows
     */
    filterTable(table, searchTerm) {
        const rows = table.querySelectorAll('tbody tr');
        const term = searchTerm.toLowerCase();
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(term) ? '' : 'none';
        });
    }
};

// File upload functionality
const FileUpload = {
    /**
     * Initialize drag and drop file upload
     */
    initDragDrop(dropArea, fileInput, options = {}) {
        const defaultOptions = {
            allowedTypes: ['.xlsx', '.xls'],
            maxSize: 10 * 1024 * 1024, // 10MB
            onFileSelect: null,
            onError: null
        };
        
        const config = { ...defaultOptions, ...options };
        
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });
        
        // Highlight drop area when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => {
                dropArea.classList.add('dragover');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => {
                dropArea.classList.remove('dragover');
            }, false);
        });
        
        // Handle dropped files
        dropArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            this.handleFiles(files, config);
        }, false);
        
        // Handle file input change
        fileInput.addEventListener('change', (e) => {
            const files = e.target.files;
            this.handleFiles(files, config);
        });
        
        // Click to select files
        dropArea.addEventListener('click', () => {
            fileInput.click();
        });
    },

    /**
     * Prevent default behaviors
     */
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    },

    /**
     * Handle selected files
     */
    handleFiles(files, config) {
        Array.from(files).forEach(file => {
            if (this.validateFile(file, config)) {
                if (config.onFileSelect) {
                    config.onFileSelect(file);
                }
            }
        });
    },

    /**
     * Validate file
     */
    validateFile(file, config) {
        // Check file type
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        if (!config.allowedTypes.includes(extension)) {
            const message = `Invalid file type. Allowed types: ${config.allowedTypes.join(', ')}`;
            if (config.onError) {
                config.onError(message);
            } else {
                Utils.showNotification(message, 'error');
            }
            return false;
        }
        
        // Check file size
        if (file.size > config.maxSize) {
            const message = `File too large. Maximum size: ${this.formatFileSize(config.maxSize)}`;
            if (config.onError) {
                config.onError(message);
            } else {
                Utils.showNotification(message, 'error');
            }
            return false;
        }
        
        return true;
    },

    /**
     * Format file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
};

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Factory ERP System initialized');
    
    // Initialize sortable tables
    document.querySelectorAll('.data-table').forEach(table => {
        DataTable.initSortableTable(table);
    });
    
    // Initialize search functionality
    document.querySelectorAll('[data-search-target]').forEach(input => {
        const targetSelector = input.dataset.searchTarget;
        const target = document.querySelector(targetSelector);
        
        if (target) {
            input.addEventListener('input', Utils.debounce((e) => {
                DataTable.filterTable(target, e.target.value);
            }, 300));
        }
    });
    
    // Initialize file upload areas
    document.querySelectorAll('.upload-area').forEach(area => {
        const fileInput = area.querySelector('input[type="file"]');
        if (fileInput) {
            FileUpload.initDragDrop(area, fileInput, {
                onFileSelect: (file) => {
                    console.log('File selected:', file.name);
                    // Handle file selection based on context
                },
                onError: (message) => {
                    Utils.showNotification(message, 'error');
                }
            });
        }
    });
    
    // Initialize forms
    document.querySelectorAll('form[data-async]').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await FormHandler.submitForm(form, {
                endpoint: form.dataset.endpoint,
                method: form.dataset.method,
                redirect: form.dataset.redirect
            });
        });
    });
});

// Global helper functions for templates
window.getAuthHeaders = function() {
    const token = localStorage.getItem('access_token');
    const headers = {};
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
};

window.getAuthHeadersWithContent = function() {
    const token = localStorage.getItem('access_token');
    const headers = {
        'Content-Type': 'application/json'
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
};

window.handleAuthError = function(response) {
    if (response.status === 401) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        window.location.href = '/auth/login';
        return true;
    }
    return false;
};

// Global showToast function for all templates
window.showToast = function(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `erp-alert erp-alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'info'} position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px; max-width: 400px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-radius: 0.375rem; padding: 1rem; margin-bottom: 1rem;';
    
    const iconMap = {
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-triangle', 
        'warning': 'fas fa-exclamation-triangle',
        'info': 'fas fa-info-circle'
    };
    
    const colorMap = {
        'success': '#10b981',
        'error': '#ef4444',
        'warning': '#f59e0b', 
        'info': '#3b82f6'
    };
    
    toast.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <i class="${iconMap[type]}" style="color: ${colorMap[type]}; font-size: 1.25rem;"></i>
            <span style="flex: 1; color: #374151; font-weight: 500;">${message}</span>
            <button type="button" style="background: none; border: none; color: #6b7280; cursor: pointer; padding: 0; font-size: 1.125rem;" onclick="this.closest('.erp-alert').remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease-out';
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
    
    // Add entrance animation
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease-out';
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0)';
    }, 10);
};

// Export for global use
window.FactoryERP = {
    Utils,
    ExcelIntegration,
    ERPNextIntegration,
    FormHandler,
    DataTable,
    FileUpload
};