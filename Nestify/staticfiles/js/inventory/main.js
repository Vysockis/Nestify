document.addEventListener("DOMContentLoaded", function() {
    function fetchItems() {
        Promise.all([
            fetch('/inventory/api/items/?type=FOOD').then(response => response.json()),
            fetch('/inventory/api/items/?type=MEDICINE').then(response => response.json())
        ]).then(([foodData, medicineData]) => {
            const allContainer = document.querySelector('.all-items-container');
            const allItems = [...foodData.items, ...medicineData.items];
            displayItems(allItems, allContainer, 999);
        });
        
        fetch('/inventory/api/items/?type=FOOD')
            .then(response => response.json())
            .then(data => {
                const foodContainer = document.querySelector('.food-items-container');
                displayItems(data.items, foodContainer, 999);
            });
        
        fetch('/inventory/api/items/?type=MEDICINE')
            .then(response => response.json())
            .then(data => {
                const medicineContainer = document.querySelector('.medicine-items-container');
                displayItems(data.items, medicineContainer, 999);
            });
    }
    
    function displayItems(items, container, limit) {
        container.innerHTML = '';
        
        if (items.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">Nėra įrašų</p>';
            return;
        }
        
        const table = document.createElement('table');
        table.className = 'table table-hover';
        
        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr>
                <th>Pavadinimas</th>
                <th>Tipas</th>
                <th>Kiekis</th>
                <th>Galiojimo data</th>
                <th>Veiksmai</th>
            </tr>
        `;
        
        const tbody = document.createElement('tbody');
        const itemsToShow = items.slice(0, limit);
        
        itemsToShow.forEach(item => {
            const row = document.createElement('tr');
            
            if (item.is_expired) {
                row.classList.add('table-danger');
            } else if (item.is_expiring_very_soon) {
                row.classList.add('table-warning');
            } else if (item.is_expiring_soon) {
                row.classList.add('table-orange');
            }
            
            row.innerHTML = `
                <td>${item.name}</td>
                <td>${item.type || (item.type_value === 'FOOD' ? 'Maistas' : 'Vaistai')}</td>
                <td>${item.qty}</td>
                <td>${item.exp_date || 'Nenustatyta'}</td>
                <td>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-outline-secondary me-2 edit-operation" data-operation-id="${item.id}">
                            <i class="fas fa-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger delete-operation" data-operation-id="${item.id}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            
            tbody.appendChild(row);
        });
        
        table.appendChild(thead);
        table.appendChild(tbody);
        container.appendChild(table);
        
        container.querySelectorAll('.delete-operation').forEach(button => {
            button.addEventListener('click', function() {
                const operationId = this.dataset.operationId;
                if (confirm('Ar tikrai norite ištrinti šį įrašą?')) {
                    fetch(`/inventory/api/operations/${operationId}/delete/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            fetchItems();
                        } else {
                            alert(data.error || 'Įvyko klaida. Bandykite dar kartą vėliau.');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('Įvyko klaida. Bandykite dar kartą vėliau.');
                    });
                }
            });
        });

        container.querySelectorAll('.edit-operation').forEach(button => {
            button.addEventListener('click', async function() {
                const operationId = this.dataset.operationId;
                const item = items.find(i => i.id === parseInt(operationId));
                if (!item) return;

                const formData = await openModal({
                    title: `Redaguoti kiekį: ${item.name}`,
                    fields: [
                        {
                            id: "qty",
                            label: "Kiekis",
                            type: "number",
                            value: item.qty.toString(),
                            min: "1",
                            required: true
                        }
                    ]
                });

                if (formData) {
                    fetch(`/inventory/api/operations/${operationId}/update/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken
                        },
                        body: JSON.stringify({
                            qty: parseInt(formData.qty)
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            fetchItems();
                        } else {
                            alert(data.error || 'Įvyko klaida. Bandykite dar kartą vėliau.');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('Įvyko klaida. Bandykite dar kartą vėliau.');
                    });
                }
            });
        });
    }
    
    const addItemBtn = document.getElementById('addItemBtn');
    if (addItemBtn) {
        addItemBtn.addEventListener('click', async function() {
            const typeOptions = itemTypes.map(type => ({
                value: type.value,
                label: type.label
            }));
            
            const formData = await openModal({
                title: "Pridėti naują turtą",
                fields: [
                    {
                        id: "name",
                        label: "Pavadinimas",
                        type: "text",
                        required: true
                    },
                    {
                        id: "item_type",
                        label: "Tipas",
                        type: "select",
                        required: true,
                        options: typeOptions
                    },
                    {
                        id: "qty",
                        label: "Kiekis",
                        type: "number",
                        value: "1",
                        min: "1"
                    },
                    {
                        id: "exp_date",
                        label: "Galiojimo data",
                        type: "date"
                    }
                ]
            });
            
            if (formData) {
                const form = new FormData();
                for (const key in formData) {
                    form.append(key, formData[key]);
                }
                
                fetch('/inventory/add/', {
                    method: 'POST',
                    body: form,
                    headers: {
                        'X-CSRFToken': csrfToken
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                    } else if (data.success) {
                        fetchItems();
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Įvyko klaida. Bandykite dar kartą vėliau.');
                });
            }
        });
    }
    
    fetchItems();
}); 