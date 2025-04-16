document.addEventListener('DOMContentLoaded', function() {
    function loadData() {
        fetch('/list/api/points/')
            .then(response => response.json())
            .then(data => {
                // Update points
                document.getElementById('userPoints').textContent = `${data.points} 💎`;

                // Update leaderboard
                const leaderboardTable = document.getElementById('leaderboardTable');
                leaderboardTable.innerHTML = data.leaderboard.map(member => `
                    <tr class="${member.is_current_user ? 'table-active' : ''}">
                        <td>${member.name}</td>
                        <td>${member.points} 💎</td>
                        ${data.is_admin ? `
                        <td class="text-end">
                            <button class="btn btn-sm btn-outline-secondary square-btn edit-points-btn" data-member-id="${member.id}" data-points="${member.points}">
                                <i class="fas fa-pencil-alt"></i>
                            </button>
                        </td>
                        ` : ''}
                    </tr>
                `).join('');

                // Update prizes
                if (data.is_admin) {
                    const prizesTable = document.getElementById('prizesTable');
                    prizesTable.innerHTML = data.prizes.map(prize => `
                        <tr>
                            <td>${prize.name}</td>
                            <td>${prize.points_required} 💎</td>
                            <td class="text-end">
                                <button class="btn btn-sm btn-outline-danger square-btn delete-prize-btn" data-prize-id="${prize.id}">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `).join('');
                } else {
                    const availablePrizes = document.getElementById('availablePrizes');
                    availablePrizes.innerHTML = data.prizes.map(prize => `
                        <div class="col-md-4 mb-3">
                            <div class="card ${prize.is_available ? 'border-success' : 'border-secondary'}">
                                <div class="card-body">
                                    <h5 class="card-title">${prize.name}</h5>
                                    <p class="card-text">${prize.points_required} 💎</p>
                                    ${prize.is_available ? 
                                        `<div class="d-flex justify-content-between align-items-center">
                                            <span class="badge bg-success">Galima iškeisti</span>
                                            <button class="btn btn-sm btn-outline-success square-btn redeem-prize-btn" data-prize-id="${prize.id}">
                                                <i class="fas fa-gift"></i>
                                            </button>
                                        </div>` : 
                                        '<span class="badge bg-secondary">Dar nepakanka taškų</span>'
                                    }
                                </div>
                            </div>
                        </div>
                    `).join('');
                }

                // Update redeemed prizes
                const redeemedPrizesTable = document.getElementById('redeemedPrizesTable');
                if (redeemedPrizesTable) {
                    if (!data.redeemed_prizes || data.redeemed_prizes.length === 0) {
                        redeemedPrizesTable.innerHTML = `
                            <tr>
                                <td colspan="${data.is_admin ? '4' : '3'}" class="text-center text-muted">
                                    Nėra iškeistų prizų
                                </td>
                            </tr>
                        `;
                    } else {
                        redeemedPrizesTable.innerHTML = data.redeemed_prizes.map(prize => `
                            <tr>
                                <td>${prize.name}</td>
                                <td>${prize.points} 💎</td>
                                ${data.is_admin ? `<td>${prize.member_name}</td>` : ''}
                                <td>${prize.date}</td>
                            </tr>
                        `).join('');
                    }
                }
            })
            .catch(error => {
                console.error('Error loading data:', error);
            });

        // Load pending tasks for admin
        const pendingTasksTable = document.getElementById('pendingTasksTable');
        if (pendingTasksTable) {
            fetch('/list/api/pending-tasks/')
                .then(response => response.json())
                .then(data => {
                    pendingTasksTable.innerHTML = data.pending_tasks.map(task => `
                        <tr>
                            <td>${task.task_name}</td>
                            <td>${task.member_name}</td>
                            <td>${task.points} 💎</td>
                            <td>${new Date(task.created_at).toLocaleString()}</td>
                            <td class="text-end">
                                <button class="btn btn-sm btn-outline-success square-btn me-2 approve-task-btn" data-task-id="${task.id}">
                                    <i class="fas fa-check"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger square-btn delete-task-btn" data-task-id="${task.id}">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `).join('');
                })
                .catch(error => {
                    console.error('Error loading pending tasks:', error);
                });
        }
    }

    // Initial load
    loadData();

    // Points editing functionality
    document.addEventListener('click', function(e) {
        if (e.target.closest('.edit-points-btn')) {
            const btn = e.target.closest('.edit-points-btn');
            const memberId = btn.dataset.memberId;
            const currentPoints = parseInt(btn.dataset.points);
            const modal = new bootstrap.Modal(document.getElementById('addPointsModal'));
            
            // Update modal title
            document.querySelector('#addPointsModal .modal-title').textContent = 'Koreguoti Taškus';
            
            // Pre-fill the points input
            document.querySelector('#addPointsForm [name="points"]').value = currentPoints;
            
            document.getElementById('savePointsBtn').onclick = function() {
                const form = document.getElementById('addPointsForm');
                const formData = new FormData(form);
                const newPoints = parseInt(formData.get('points'));
                const pointsDifference = newPoints - currentPoints;
                
                fetch('/list/api/add-points/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        member_id: memberId,
                        points: pointsDifference
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        modal.hide();
                        form.reset();
                        loadData();
                    } else {
                        alert('Klaida: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error managing points:', error);
                    alert('Įvyko klaida tvarkant taškus');
                });
            };
            
            modal.show();
        }
    });

    // Add prize functionality
    const addPrizeBtn = document.getElementById('addPrizeBtn');
    if (addPrizeBtn) {
        addPrizeBtn.addEventListener('click', function() {
            const modal = new bootstrap.Modal(document.getElementById('addPrizeModal'));
            modal.show();
        });

        document.getElementById('savePrizeBtn').addEventListener('click', function() {
            const form = document.getElementById('addPrizeForm');
            const formData = new FormData(form);
            
            fetch('/list/api/prize/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    name: formData.get('name'),
                    points_required: parseInt(formData.get('points_required'))
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addPrizeModal'));
                    modal.hide();
                    form.reset();
                    loadData();
                } else {
                    alert('Klaida: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error adding prize:', error);
                alert('Įvyko klaida pridedant prizą');
            });
        });
    }

    // Delete prize functionality
    document.addEventListener('click', function(e) {
        if (e.target.closest('.delete-prize-btn')) {
            if (!confirm('Ar tikrai norite ištrinti šį prizą?')) return;
            
            const btn = e.target.closest('.delete-prize-btn');
            const prizeId = btn.dataset.prizeId;
            
            fetch('/list/api/prize/', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    prize_id: prizeId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadData();
                } else {
                    alert('Klaida: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error deleting prize:', error);
                alert('Įvyko klaida trinant prizą');
            });
        }
    });

    // Approve task functionality
    document.addEventListener('click', function(e) {
        if (e.target.closest('.approve-task-btn')) {
            const btn = e.target.closest('.approve-task-btn');
            const taskId = btn.dataset.taskId;
            
            fetch(`/list/api/approve-task/${taskId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadData();
                } else {
                    alert('Klaida: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error approving task:', error);
                alert('Įvyko klaida tvirtinant užduotį');
            });
        }
    });

    // Delete task functionality
    document.addEventListener('click', function(e) {
        if (e.target.closest('.delete-task-btn')) {
            if (!confirm('Ar tikrai norite ištrinti šią užduotį?')) return;
            
            const btn = e.target.closest('.delete-task-btn');
            const taskId = btn.dataset.taskId;
            
            fetch(`/list/api/pending-task/${taskId}/`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadData();
                } else {
                    alert('Klaida: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error deleting task:', error);
                alert('Įvyko klaida trinant užduotį');
            });
        }
    });

    // Prize redemption functionality
    document.addEventListener('click', function(e) {
        if (e.target.closest('.redeem-prize-btn')) {
            if (!confirm('Ar tikrai norite iškeisti šį prizą?')) return;
            
            const btn = e.target.closest('.redeem-prize-btn');
            const prizeId = btn.dataset.prizeId;
            
            fetch(`/list/api/redeem-prize/${prizeId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadData();
                    alert('Prizas sėkmingai iškeistas!');
                } else {
                    alert('Klaida: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error redeeming prize:', error);
                alert('Įvyko klaida iškeičiant prizą');
            });
        }
    });
}); 