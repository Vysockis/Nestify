document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded'); // Debug log

    const inviteModal = new bootstrap.Modal(document.getElementById('inviteModal'));
    
    // Handle invite button click
    const inviteBtn = document.getElementById('inviteBtn');
    console.log('Invite button:', inviteBtn); // Debug log
    if (inviteBtn) {
        inviteBtn.addEventListener('click', function() {
            inviteModal.show();
        });
    }

    // Function to generate code
    async function generateCode() {
        console.log('Generate code function called'); // Debug log
        try {
            const csrftoken = getCookie('csrftoken');
            console.log('CSRF Token:', csrftoken); // Debug log
            
            const response = await fetch('/family/api/generate-code/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json',
                }
            });
            
            console.log('Response status:', response.status); // Debug log
            
            if (!response.ok) {
                const errorData = await response.json();
                console.error('Server error:', errorData); // Debug log
                throw new Error(errorData.error || 'Failed to generate code');
            }
            
            const data = await response.json();
            console.log('Response data:', data); // Debug log
            
            // Add code to the list
            const codesList = document.querySelector('.invitation-codes-list');
            const emptyMessage = codesList.querySelector('p.text-muted');
            
            if (emptyMessage) {
                emptyMessage.remove();
            }
            
            const codeItem = document.createElement('div');
            codeItem.className = 'invitation-code-item d-flex justify-content-between align-items-center p-2 border-bottom';
            codeItem.innerHTML = `
                <code>${data.code}</code>
                <button class="btn btn-sm btn-outline-danger delete-code-btn" data-code-id="${data.id}">
                    <i class="fas fa-trash"></i>
                </button>
            `;
            
            // Insert before the generate button container
            const generateBtnContainer = codesList.querySelector('.mt-3');
            codesList.insertBefore(codeItem, generateBtnContainer);
            
            // If modal is open, update the input field
            const invitationCodeInput = document.getElementById('invitationCode');
            if (invitationCodeInput) {
                invitationCodeInput.value = data.code;
            }
            
            showAlert('success', 'Kodas sugeneruotas sėkmingai');
            return data.code;
        } catch (error) {
            console.error('Error generating code:', error);
            showAlert('error', 'Nepavyko sugeneruoti kodo: ' + error.message);
            return null;
        }
    }

    // Handle generate code button in modal
    const modalGenerateBtn = document.getElementById('modalGenerateCodeBtn');
    console.log('Modal generate button:', modalGenerateBtn); // Debug log
    if (modalGenerateBtn) {
        modalGenerateBtn.addEventListener('click', function() {
            console.log('Modal generate button clicked'); // Debug log
            generateCode();
        });
    }

    // Handle generate code button in main page
    const mainGenerateBtn = document.getElementById('generateCodeBtn');
    console.log('Main generate button:', mainGenerateBtn); // Debug log
    if (mainGenerateBtn) {
        mainGenerateBtn.addEventListener('click', function() {
            console.log('Main generate button clicked'); // Debug log
            generateCode();
        });
    }

    // Delete invitation code
    document.addEventListener('click', async function(e) {
        if (e.target.closest('.delete-code-btn')) {
            const btn = e.target.closest('.delete-code-btn');
            const codeId = btn.dataset.codeId;
            
            try {
                const response = await fetch(`/family/api/delete-code/${codeId}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    }
                });
                
                if (!response.ok) throw new Error('Failed to delete code');
                
                btn.closest('.invitation-code-item').remove();
                
                const codesList = document.querySelector('.invitation-codes-list');
                if (!codesList.querySelector('.invitation-code-item')) {
                    const emptyMessage = document.createElement('p');
                    emptyMessage.className = 'text-center text-muted my-3';
                    emptyMessage.textContent = 'Nėra aktyvių kodų';
                    codesList.insertBefore(emptyMessage, codesList.querySelector('#generateCodeBtn').parentElement);
                }
                
                showAlert('success', 'Kodas ištrintas sėkmingai');
            } catch (error) {
                console.error('Error deleting code:', error);
                showAlert('error', 'Nepavyko ištrinti kodo');
            }
        }
    });

    // Toggle kid status
    document.addEventListener('click', async function(e) {
        if (e.target.closest('.toggle-kid-btn')) {
            const btn = e.target.closest('.toggle-kid-btn');
            const memberId = btn.dataset.memberId;
            const isCurrentlyKid = btn.dataset.isKid === 'true';
            
            try {
                const response = await fetch(`/family/api/toggle-kid/${memberId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ is_kid: !isCurrentlyKid })
                });
                
                if (!response.ok) throw new Error('Failed to update status');
                
                const memberItem = btn.closest('.member-item');
                const statusText = memberItem.querySelector('small.text-muted');
                
                statusText.textContent = isCurrentlyKid ? 'Narys' : 'Vaikas';
                btn.innerHTML = isCurrentlyKid ? 
                    '<i class="fas fa-child me-1"></i>Pažymėti Vaiku' :
                    '<i class="fas fa-user me-1"></i>Pažymėti Suaugusiu';
                btn.dataset.isKid = (!isCurrentlyKid).toString();
                
            } catch (error) {
                console.error('Error updating status:', error);
                showAlert('error', 'Nepavyko atnaujinti statuso');
            }
        }
    });

    // Remove member
    document.addEventListener('click', async function(e) {
        if (e.target.closest('.remove-member-btn')) {
            if (!confirm('Ar tikrai norite pašalinti šį narį iš šeimos?')) return;
            
            const btn = e.target.closest('.remove-member-btn');
            const memberId = btn.dataset.memberId;
            
            try {
                const response = await fetch(`/family/api/remove-member/${memberId}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    }
                });
                
                if (!response.ok) throw new Error('Failed to remove member');
                
                const memberItem = btn.closest('.member-item');
                memberItem.remove();
                
                const membersList = document.querySelector('.members-list');
                if (!membersList.querySelector('.member-item')) {
                    membersList.innerHTML = '<p class="text-center text-muted my-3">Šeimos narių nerasta</p>';
                }
                
            } catch (error) {
                console.error('Error removing member:', error);
                showAlert('error', 'Nepavyko pašalinti nario');
            }
        }
    });

    // Copy invitation code
    const copyCodeBtn = document.getElementById('copyCodeBtn');
    if (copyCodeBtn) {
        copyCodeBtn.addEventListener('click', function() {
            const codeInput = document.getElementById('invitationCode');
            codeInput.select();
            document.execCommand('copy');
            
            const originalIcon = copyCodeBtn.innerHTML;
            copyCodeBtn.innerHTML = '<i class="fas fa-check"></i>';
            setTimeout(() => {
                copyCodeBtn.innerHTML = originalIcon;
            }, 2000);
            
            showAlert('success', 'Kodas nukopijuotas');
        });
    }

    // Approve member
    document.addEventListener('click', async function(e) {
        if (e.target.closest('.approve-member-btn')) {
            const btn = e.target.closest('.approve-member-btn');
            const memberId = btn.dataset.memberId;
            
            try {
                const response = await fetch(`/family/api/approve-member/${memberId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json',
                    }
                });
                
                if (!response.ok) throw new Error('Failed to approve member');
                
                // Remove from pending list and add to members list
                const memberItem = btn.closest('.member-item');
                const memberName = memberItem.querySelector('h6').textContent;
                
                // Create new member item
                const newMemberItem = document.createElement('div');
                newMemberItem.className = 'member-item d-flex justify-content-between align-items-center p-2 border-bottom';
                newMemberItem.innerHTML = `
                    <div class="d-flex align-items-center">
                        <div class="member-avatar me-3">
                            <i class="fas fa-user"></i>
                        </div>
                        <div>
                            <h6 class="mb-0">${memberName}</h6>
                            <small class="text-muted">Narys</small>
                        </div>
                    </div>
                    <div class="member-actions">
                        <button class="btn btn-outline-secondary btn-sm me-2 toggle-kid-btn" 
                                data-member-id="${memberId}"
                                data-is-kid="false">
                            <i class="fas fa-child me-1"></i>Pažymėti Vaiku
                        </button>
                        <button class="btn btn-danger btn-sm remove-member-btn" 
                                data-member-id="${memberId}">
                            <i class="fas fa-trash-alt me-1"></i>Pašalinti
                        </button>
                    </div>
                `;
                
                // Add to members list
                const membersList = document.querySelector('.members-list');
                const emptyMessage = membersList.querySelector('p.text-muted');
                if (emptyMessage) {
                    emptyMessage.remove();
                }
                membersList.appendChild(newMemberItem);
                
                // Remove from pending list
                memberItem.remove();
                
                // Check if pending list is empty
                const pendingList = document.querySelector('.pending-members-list');
                if (!pendingList.querySelector('.member-item')) {
                    pendingList.closest('.card').remove();
                }
                
                showAlert('success', 'Narys patvirtintas sėkmingai');
            } catch (error) {
                console.error('Error approving member:', error);
                showAlert('error', 'Nepavyko patvirtinti nario');
            }
        }
    });

    // Reject member
    document.addEventListener('click', async function(e) {
        if (e.target.closest('.reject-member-btn')) {
            if (!confirm('Ar tikrai norite atmesti šį narį?')) return;
            
            const btn = e.target.closest('.reject-member-btn');
            const memberId = btn.dataset.memberId;
            
            try {
                const response = await fetch(`/family/api/reject-member/${memberId}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    }
                });
                
                if (!response.ok) throw new Error('Failed to reject member');
                
                // Remove from pending list
                const memberItem = btn.closest('.member-item');
                memberItem.remove();
                
                // Check if pending list is empty
                const pendingList = document.querySelector('.pending-members-list');
                if (!pendingList.querySelector('.member-item')) {
                    pendingList.closest('.card').remove();
                }
                
                showAlert('success', 'Narys atmestas sėkmingai');
            } catch (error) {
                console.error('Error rejecting member:', error);
                showAlert('error', 'Nepavyko atmesti nario');
            }
        }
    });

    // Settings form handling
    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = {
                inventory_notifications: settingsForm.querySelector('[name="inventory_notifications"]').value,
                task_notifications: settingsForm.querySelector('[name="task_notifications"]').value
            };

            fetch('/family/settings/api/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('success', 'Nustatymai sėkmingai išsaugoti');
                } else {
                    showAlert('danger', data.error || 'Klaida išsaugant nustatymus');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('danger', 'Klaida išsaugant nustatymus');
            });
        });
    }

    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Helper function to show alerts
    function showAlert(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show w-100`;
        alertDiv.style.borderRadius = '0';
        alertDiv.style.position = 'relative';
        alertDiv.style.textAlign = 'center';
        alertDiv.style.marginBottom = '0';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Remove any existing alerts
        const existingAlerts = document.querySelectorAll('.alert-container');
        existingAlerts.forEach(alert => alert.remove());
        
        // Create a container for the alert with padding
        const alertContainer = document.createElement('div');
        alertContainer.className = 'alert-container';
        alertContainer.style.backgroundColor = '#f8f9fa';
        alertContainer.style.padding = '1rem 0';
        alertContainer.style.marginTop = '1rem';
        alertContainer.appendChild(alertDiv);
        
        // Insert after navbar
        const masterContainer = document.querySelector('.master-container');
        if (masterContainer) {
            masterContainer.insertBefore(alertContainer, masterContainer.firstChild);
        } else {
            const navbar = document.querySelector('nav');
            if (navbar && navbar.nextSibling) {
                document.body.insertBefore(alertContainer, navbar.nextSibling);
            } else {
                document.body.insertBefore(alertContainer, document.body.firstChild);
            }
        }
        
        setTimeout(() => {
            alertContainer.remove();
        }, 3000);
    }
}); 