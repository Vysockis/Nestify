document.addEventListener("DOMContentLoaded", function() {
    function fetchItems() {
        Promise.all([
            fetch('/inventory/api/items/?type=FOOD').then(response => response.json()),
            fetch('/inventory/api/items/?type=MEDICINE').then(response => response.json()),
            fetch('/inventory/api/items/?type=CONTRACTS').then(response => response.json())
        ]).then(([foodData, medicineData, contractsData]) => {
            const allContainer = document.querySelector('.all-items-container');
            const allItems = [...foodData.items, ...medicineData.items, ...contractsData.items];
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

        fetch('/inventory/api/items/?type=CONTRACTS')
            .then(response => response.json())
            .then(data => {
                const contractsContainer = document.querySelector('.contracts-items-container');
                displayItems(data.items, contractsContainer, 999);
            });
    }
    
    function displayItems(items, container, limit) {
        container.innerHTML = '';
        
        if (items.length === 0) {
            container.innerHTML = '<p class="text-center text-muted my-3">No items found</p>';
            return;
        }
        
        const table = document.createElement('table');
        table.classList.add('table', 'table-hover');
        
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
        
        items.forEach(item => {
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
                <td>${item.type || (item.type_value === 'FOOD' ? 'Maistas' : item.type_value === 'MEDICINE' ? 'Vaistai' : 'Sutartys')}</td>
                ${item.type_value !== 'CONTRACTS' ? `<td>${item.total_qty}</td>` : '</td><td>'}
                <td>${item.exp_date || 'Nenustatyta'}</td>
                <td>
                    <div class="btn-group">
                        ${!window.isKid ? `
                            ${item.type_value !== 'CONTRACTS' ? `
                                <button class="btn btn-sm btn-outline-secondary me-2 edit-operation" data-operation-id="${item.id}">
                                    <i class="fas fa-pencil"></i>
                                </button>
                            ` : ''}
                            <button class="btn btn-sm btn-outline-danger delete-operation" data-operation-id="${item.id}" data-type="${item.type_value}">
                                <i class="fas fa-trash"></i>
                            </button>
                        ` : ''}
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
                const itemType = this.dataset.type;
                
                if (confirm('Ar tikrai norite ištrinti šį įrašą?')) {
                    const url = itemType === 'CONTRACTS' 
                        ? `/inventory/api/contracts/${operationId}/delete/`
                        : `/inventory/api/operations/${operationId}/delete/`;
                    
                    fetch(url, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': window.inventoryToken
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
                const row = this.closest('tr');
                const currentQty = parseInt(row.querySelector('td:nth-child(3)').textContent);

                const formData = await openModal({
                    title: `Redaguoti kiekį: ${row.querySelector('td:nth-child(1)').textContent}`,
                    fields: [
                        {
                            id: "qty",
                            label: "Kiekis",
                            type: "number",
                            value: currentQty.toString(),
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
                            'X-CSRFToken': window.inventoryToken
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
        // Hide add button for kids
        if (window.isKid) {
            addItemBtn.style.display = 'none';
        }

        addItemBtn.addEventListener('click', async function() {
            const typeOptions = window.itemTypes.map(type => ({
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
                        options: typeOptions,
                        onChange: function(value, form) {
                            const qtyField = form.querySelector('[name="qty"]').closest('.mb-3');
                            if (value === 'CONTRACTS') {
                                qtyField.style.display = 'none';
                            } else {
                                qtyField.style.display = 'block';
                            }
                        }
                    },
                    {
                        id: "qty",
                        label: "Kiekis",
                        type: "number",
                        value: "1",
                        min: "1",
                        required: true
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
                    if (key === 'qty' && formData.item_type === 'CONTRACTS') {
                        continue; // Skip quantity for contracts
                    }
                    form.append(key, formData[key]);
                }
                
                fetch('/inventory/add/', {
                    method: 'POST',
                    body: form,
                    headers: {
                        'X-CSRFToken': window.inventoryToken
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

// Function to fetch and display items
async function fetchAndDisplayItems() {
    try {
        const [foodData, medicineData, contractsData] = await Promise.all([
            fetch('/inventory/api/items/?type=FOOD').then(response => response.json()),
            fetch('/inventory/api/items/?type=MEDICINE').then(response => response.json()),
            window.isKid ? Promise.resolve({ items: [] }) : fetch('/inventory/api/items/?type=CONTRACTS').then(response => response.json())
        ]);

        const allItems = [...foodData.items, ...medicineData.items, ...contractsData.items];
        
        // Display items in their respective containers
        const allContainer = document.querySelector('.all-items-container');
        const foodContainer = document.querySelector('.food-items-container');
        const medicineContainer = document.querySelector('.medicine-items-container');
        const contractsContainer = document.querySelector('.contracts-items-container');
        
        displayItems(allItems, allContainer, 999);
        displayItems(foodData.items, foodContainer, 999);
        displayItems(medicineData.items, medicineContainer, 999);
        
        if (!window.isKid && contractsContainer) {
            displayItems(contractsData.items, contractsContainer, 999);
        }
    } catch (error) {
        console.error('Error fetching items:', error);
    }
} 