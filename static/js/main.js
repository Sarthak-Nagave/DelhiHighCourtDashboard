// Main JavaScript file for Delhi High Court Case Management Dashboard

document.addEventListener('DOMContentLoaded', function() {
    // Update current time in navbar
    updateTime();
    setInterval(updateTime, 1000);
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

function updateTime() {
    const now = new Date();
    const timeString = now.toLocaleString('en-IN', {
        timeZone: 'Asia/Kolkata',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        timeElement.textContent = timeString;
    }
}

// Form validation enhancement
function validateSearchForm() {
    const caseType = document.getElementById('case_type').value;
    const caseNumber = document.getElementById('case_number').value;
    const filingYear = document.getElementById('filing_year').value;
    
    if (!caseType || !caseNumber || !filingYear) {
        showAlert('Please fill in all required fields.', 'warning');
        return false;
    }
    
    if (!/^\d+$/.test(caseNumber)) {
        showAlert('Case number should contain only numbers.', 'error');
        return false;
    }
    
    return true;
}

function showAlert(message, type = 'info') {
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    alertContainer.innerHTML = `
        <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    const firstChild = container.firstElementChild;
    container.insertBefore(alertContainer, firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertContainer);
        bsAlert.close();
    }, 5000);
}

// Enhanced case number input formatting
document.addEventListener('DOMContentLoaded', function() {
    const caseNumberInput = document.getElementById('case_number');
    if (caseNumberInput) {
        caseNumberInput.addEventListener('input', function(e) {
            // Remove non-numeric characters
            let value = e.target.value.replace(/[^0-9]/g, '');
            // Limit to reasonable length
            if (value.length > 8) {
                value = value.substring(0, 8);
            }
            e.target.value = value;
        });
        
        caseNumberInput.addEventListener('paste', function(e) {
            setTimeout(() => {
                let value = e.target.value.replace(/[^0-9]/g, '');
                if (value.length > 8) {
                    value = value.substring(0, 8);
                }
                e.target.value = value;
            }, 10);
        });
    }
});

// Search form enhancement
document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            if (!validateSearchForm()) {
                e.preventDefault();
                return false;
            }
            
            // Show loading state
            const submitBtn = document.getElementById('searchBtn');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Searching...';
                submitBtn.disabled = true;
                
                // Re-enable button after 10 seconds as fallback
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 10000);
            }
        });
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const caseTypeSelect = document.getElementById('case_type');
        if (caseTypeSelect) {
            caseTypeSelect.focus();
        }
    }
    
    // Escape to clear form
    if (e.key === 'Escape') {
        const activeElement = document.activeElement;
        if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'SELECT')) {
            activeElement.blur();
        }
    }
});

// Print functionality
function printCaseDetails() {
    window.print();
}

// Copy case information to clipboard
function copyCaseInfo(caseInfo) {
    navigator.clipboard.writeText(caseInfo).then(function() {
        showAlert('Case information copied to clipboard!', 'success');
    }, function(err) {
        showAlert('Failed to copy case information.', 'error');
    });
}

// Download tracking
document.addEventListener('DOMContentLoaded', function() {
    const downloadLinks = document.querySelectorAll('a[href*="download_pdf"]');
    downloadLinks.forEach(link => {
        link.addEventListener('click', function() {
            showAlert('PDF download started...', 'info');
        });
    });
});
