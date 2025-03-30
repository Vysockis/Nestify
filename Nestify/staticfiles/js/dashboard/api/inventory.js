document.addEventListener("DOMContentLoaded", function() {
    function fetchExpiringItems() {
        fetch('/inventory/api/expiring-items/')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('expiringItemsContainer');
                container.innerHTML = '';
                
                if (data.items.length === 0) {
                    container.innerHTML = '<p class="text-muted text-center">Nėra greitai besibaigiančių produktų</p>';
                    return;
                }
                
                const table = document.createElement('table');
                table.className = 'table table-hover';
                
                const tbody = document.createElement('tbody');
                
                data.items.forEach(item => {
                    const row = document.createElement('tr');
                    
                    // Add appropriate color class
                    if (item.is_expired) {
                        row.classList.add('table-danger');
                    } else {
                        row.classList.add('table-warning');
                    }
                    
                    // Format days text
                    let daysText = '';
                    if (item.is_expired) {
                        daysText = `<div class="text-danger small">Pasibaigęs ${Math.abs(item.days_left)} d.</div>`;
                    } else {
                        daysText = `<div class="text-warning small">Liko ${item.days_left} d.</div>`;
                    }
                    
                    row.innerHTML = `
                        <td>
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>${item.name}</strong>
                                    <div class="text-muted small">${item.type}</div>
                                </div>
                                <div class="text-end">
                                    <div>${item.qty} vnt.</div>
                                    ${daysText}
                                </div>
                            </div>
                        </td>
                    `;
                    
                    tbody.appendChild(row);
                });
                
                table.appendChild(tbody);
                container.appendChild(table);
            })
            .catch(error => {
                console.error('Error:', error);
                const container = document.getElementById('expiringItemsContainer');
                container.innerHTML = '<p class="text-danger">Įvyko klaida gaunant duomenis</p>';
            });
    }
    
    fetchExpiringItems();
    // Refresh every 5 minutes
    setInterval(fetchExpiringItems, 300000);
}); 