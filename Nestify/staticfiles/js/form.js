// Global form modal
let modalInstance = null;
let isFirstModal = true; // Track if this is the first modal we're opening

function getCurrentDateTime() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");
    const hours = String(now.getHours()).padStart(2, "0");
    const minutes = String(now.getMinutes()).padStart(2, "0");

    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

// Function to clean up any modal artifacts
function cleanupModals(isInitial = false) {
    try {
        console.log("Cleaning modals, isInitial:", isInitial);
        
        // Force cleanup for static HTML modals that might be in the page
        const staticModals = document.querySelectorAll('.modal[id]:not(#formModal)');
        staticModals.forEach(modal => {
            try {
                // Just hide these, don't remove them
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
                // Remove show class manually
                modal.classList.remove('show');
                modal.style.display = 'none';
                modal.setAttribute('aria-hidden', 'true');
                modal.removeAttribute('aria-modal');
                modal.removeAttribute('role');
            } catch (err) {
                console.log("Error hiding static modal:", err);
            }
        });
        
        // For dynamically created modals, we can remove them
        const formModal = document.getElementById('formModal');
        if (formModal) {
            try {
                const bsModal = bootstrap.Modal.getInstance(formModal);
                if (bsModal) {
                    bsModal.hide();
                }
                // Wait a bit before removing
                setTimeout(() => {
                    if (document.body.contains(formModal)) {
                        document.body.removeChild(formModal);
                    }
                }, isInitial ? 50 : 10);
            } catch (err) {
                console.log("Error removing form modal:", err);
            }
        }
        
        // Force modal elements to be hidden via CSS with !important
        const modalStyle = document.createElement('style');
        modalStyle.id = 'temp-modal-fix';
        modalStyle.innerHTML = `
            body.modal-open { overflow: auto !important; padding-right: 0 !important; }
            .modal-backdrop { opacity: 0 !important; pointer-events: none !important; }
        `;
        
        // Remove existing style if there
        const existingStyle = document.getElementById('temp-modal-fix');
        if (existingStyle) {
            document.head.removeChild(existingStyle);
        }
        
        // Add the new style
        document.head.appendChild(modalStyle);
        
        // Remove after a delay
        setTimeout(() => {
            if (document.head.contains(modalStyle)) {
                document.head.removeChild(modalStyle);
            }
            
            // More aggressive cleanup for backdrops
            const backdrops = document.querySelectorAll('.modal-backdrop');
            backdrops.forEach(backdrop => {
                if (document.body.contains(backdrop)) {
                    document.body.removeChild(backdrop);
                }
            });
            
            // Reset body classes and styles
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
            document.body.removeAttribute('style');
        }, isInitial ? 200 : 100);
        
        modalInstance = null;
    } catch (e) {
        console.error("Error in cleanupModals:", e);
    }
}

// Make openModal available globally
window.openModal = function(options) {
    return new Promise((resolve, reject) => {
        try {
            // Special handling for first run
            const firstRun = isFirstModal;
            if (isFirstModal) {
                isFirstModal = false;
                // More aggressive initial cleanup
                cleanupModals(true);
                
                // Add small delay before creating first modal
                setTimeout(() => createAndShowModal(), 100);
            } else {
                // For subsequent modals, clean up and show immediately
                cleanupModals(false);
                createAndShowModal();
            }
            
            function createAndShowModal() {
                // Create modal element
                const modal = document.createElement('div');
                modal.className = 'modal fade';
                modal.id = 'formModal';
                modal.tabIndex = '-1';
                modal.setAttribute('aria-hidden', 'true');
                
                // Start building the form
                let formHtml = '';
                let hasImageField = false;
                
                if (options.fields && options.fields.length > 0) {
                    options.fields.forEach(field => {
                        let fieldHtml = '';
                        const fieldId = `modal-field-${field.id}`;
                        
                        if (field.type === 'select') {
                            fieldHtml = `
                                <div class="mb-3">
                                    <label for="${fieldId}" class="form-label">${field.label}${field.required ? ' *' : ''}</label>
                                    <select class="form-select${field.required ? ' required' : ''}" id="${fieldId}" name="${field.id}" ${field.required ? 'required' : ''}>
                                        ${field.id === 'scan_type' ? '<option value="">-- Pasirinkite --</option>' : ''}
                                        ${field.options.map(option => `<option value="${option.value}">${option.label}</option>`).join('')}
                                    </select>
                                </div>
                            `;
                        } else if (field.type === 'image') {
                            hasImageField = true;
                            fieldHtml = `
                                <div class="mb-3">
                                    <label for="${fieldId}" class="form-label">${field.label}${field.required ? ' *' : ''}</label>
                                    <input type="file" class="form-control${field.required ? ' required' : ''}" id="${fieldId}" name="${field.id}" accept="image/*,.pdf" ${field.required ? 'required' : ''}>
                                    <div id="${fieldId}-preview" class="mt-2 img-preview"></div>
                                </div>
                            `;
                        } else if (field.type === 'textarea') {
                            fieldHtml = `
                                <div class="mb-3">
                                    <label for="${fieldId}" class="form-label">${field.label}${field.required ? ' *' : ''}</label>
                                    <textarea class="form-control${field.required ? ' required' : ''}" id="${fieldId}" name="${field.id}" placeholder="${field.placeholder || ''}" rows="3" ${field.required ? 'required' : ''}>${field.value || ''}</textarea>
                                </div>
                            `;
                        } else {
                            // Default to input type="text" or specified type
                            const inputType = field.type || 'text';
                            fieldHtml = `
                                <div class="mb-3">
                                    <label for="${fieldId}" class="form-label">${field.label}${field.required ? ' *' : ''}</label>
                                    <input type="${inputType}" class="form-control${field.required ? ' required' : ''}" id="${fieldId}" name="${field.id}" placeholder="${field.placeholder || ''}" value="${field.value || ''}" ${field.min ? `min="${field.min}"` : ''} ${field.max ? `max="${field.max}"` : ''} ${field.step ? `step="${field.step}"` : ''} ${field.required ? 'required' : ''}>
                                </div>
                            `;
                        }
                        
                        formHtml += fieldHtml;
                    });
                }
                
                modal.innerHTML = `
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">${options.title || 'Form'}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <form id="dynamicForm" ${hasImageField ? 'enctype="multipart/form-data"' : ''}>
                                    ${formHtml}
                                </form>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Uždaryti</button>
                                <button type="button" class="btn btn-primary" id="saveButton">Išsaugoti</button>
                            </div>
                        </div>
                    </div>
                `;
                
                // Add the modal to the body
                document.body.appendChild(modal);
                
                // Initialize the modal
                modalInstance = new bootstrap.Modal(modal);
                modalInstance.show();
                
                // Handle form submission
                const form = document.getElementById('dynamicForm');
                const saveButton = document.getElementById('saveButton');
                
                // Special handling for scan_type selection which should auto-submit when changed
                const scanTypeSelect = document.getElementById('modal-field-scan_type');
                if (scanTypeSelect) {
                    // Auto-submit when scan_type selection changes
                    scanTypeSelect.addEventListener('change', () => {
                        if (scanTypeSelect.value) {
                            console.log("Scan type selected:", scanTypeSelect.value);
                            // Give a short delay to allow the UI to update
                            setTimeout(() => {
                                saveButton.click();
                            }, 50);
                        }
                    });
                }
                
                // Handle file input change for image preview
                if (hasImageField) {
                    options.fields.forEach(field => {
                        if (field.type === 'image') {
                            const fileInput = document.getElementById(`modal-field-${field.id}`);
                            const previewDiv = document.getElementById(`modal-field-${field.id}-preview`);
                            
                            fileInput.addEventListener('change', function(e) {
                                if (e.target.files && e.target.files[0]) {
                                    const file = e.target.files[0];
                                    
                                    if (file.type.startsWith('image/')) {
                                        const reader = new FileReader();
                                        reader.onload = function(e) {
                                            previewDiv.innerHTML = `<img src="${e.target.result}" class="img-fluid preview-image">`;
                                        }
                                        reader.readAsDataURL(file);
                                    } else if (file.type === 'application/pdf') {
                                        previewDiv.innerHTML = `<p>PDF Failas: ${file.name}</p>`;
                                    }
                                }
                            });
                        }
                    });
                }
                
                // Set up save button click handler
                saveButton.addEventListener('click', () => {
                    if (form.checkValidity()) {
                        const formData = {};
                        
                        options.fields.forEach(field => {
                            const fieldElement = document.getElementById(`modal-field-${field.id}`);
                            
                            if (field.type === 'image') {
                                if (fieldElement.files && fieldElement.files[0]) {
                                    formData[field.id] = fieldElement.files[0];
                                }
                            } else {
                                formData[field.id] = fieldElement.value;
                            }
                        });
                        
                        cleanupModals(firstRun); // Use firstRun flag to give special handling
                        resolve(formData);
                    } else {
                        // Trigger HTML5 validation
                        const submitEvent = new Event('submit', {
                            'bubbles': true,
                            'cancelable': true
                        });
                        form.dispatchEvent(submitEvent);
                    }
                });
                
                // Handle modal close
                modal.addEventListener('hidden.bs.modal', () => {
                    resolve(null); // Return null if modal is closed without saving
                    // Clean up all modal artifacts with special handling for first run
                    cleanupModals(firstRun);
                });
            }
        } catch (error) {
            console.error("Error opening modal:", error);
            reject(error);
        }
    });
};

// Make cleanupModals available globally for emergency use
window.forceCleanupModals = function() {
    console.log("Force cleanup called");
    cleanupModals();
    
    // Extra aggressive cleanup
    document.querySelectorAll('.modal, .modal-backdrop').forEach(el => {
        if (document.body.contains(el)) {
            try {
                document.body.removeChild(el);
            } catch (e) {
                console.error("Error removing modal element:", e);
            }
        }
    });
    
    // Reset body
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
    document.body.removeAttribute('style');
    
    return "Cleanup complete";
};

// Cleanup modals on page load to ensure a clean start
document.addEventListener('DOMContentLoaded', function() {
    cleanupModals();
    
    // Add global click handler to clean up modals when clicking outside
    document.body.addEventListener('click', function(e) {
        // Check if we clicked outside any modal and if there are any .modal-backdrop elements
        if (document.querySelector('.modal-backdrop') && 
            !e.target.closest('.modal-content')) {
            cleanupModals();
        }
    });
    
    // Setup ESC key to force modal cleanup
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            setTimeout(cleanupModals, 100);
        }
    });
    
    // Add a safety interval to periodically check for and clean orphaned modals
    // This is a last resort for modals that weren't properly cleaned up
    setInterval(function() {
        // Only clean if there's a backdrop but no visible modal
        const hasBackdrop = document.querySelector('.modal-backdrop');
        const hasVisibleModal = document.querySelector('.modal.show');
        
        if (hasBackdrop && !hasVisibleModal) {
            console.log("Safety cleanup: Found orphaned modal backdrop");
            cleanupModals();
        }
        
        // Also check if body has modal-open class but no visible modal
        if (document.body.classList.contains('modal-open') && !hasVisibleModal) {
            console.log("Safety cleanup: Body has modal-open but no visible modal");
            cleanupModals();
        }
    }, 2000); // Check every 2 seconds
});
