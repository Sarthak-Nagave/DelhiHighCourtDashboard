document.addEventListener('DOMContentLoaded', function() {
    updateTime();
    setInterval(updateTime, 1000);
    
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
      
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
      
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertContainer);
        bsAlert.close();
    }, 5000);
}

document.addEventListener('DOMContentLoaded', function() {
    const caseNumberInput = document.getElementById('case_number');
    if (caseNumberInput) {
        caseNumberInput.addEventListener('input', function(e) {
            
            let value = e.target.value.replace(/[^0-9]/g, '');
            
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

document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            if (!validateSearchForm()) {
                e.preventDefault();
                return false;
            }
                        
            const submitBtn = document.getElementById('searchBtn');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Searching...';
                submitBtn.disabled = true;
                
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 10000);
            }
        });
    }
});

document.addEventListener('keydown', function(e) {

    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const caseTypeSelect = document.getElementById('case_type');
        if (caseTypeSelect) {
            caseTypeSelect.focus();
        }
    }
    
    if (e.key === 'Escape') {
        const activeElement = document.activeElement;
        if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'SELECT')) {
            activeElement.blur();
        }
    }
});

function printCaseDetails() {
    window.print();
}

function copyCaseInfo(caseInfo) {
    navigator.clipboard.writeText(caseInfo).then(function() {
        showAlert('Case information copied to clipboard!', 'success');
    }, function(err) {
        showAlert('Failed to copy case information.', 'error');
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const downloadLinks = document.querySelectorAll('a[href*="download_pdf"]');
    downloadLinks.forEach(link => {
        link.addEventListener('click', function() {
            showAlert('PDF download started...', 'info');
        });
    });
});
