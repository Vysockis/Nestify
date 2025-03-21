document.addEventListener("DOMContentLoaded", function() {
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const financeCtx = document.getElementById('financeChart').getContext('2d');
    const categoryCtx = document.getElementById('categoryChart').getContext('2d');
    const operationsTable = document.getElementById('operations-table');
    const financeAdd = document.getElementById("addFinanceBtn");
    const refreshBtn = document.getElementById("refreshFinanceBtn");

    const today = new Date();
    const lastYear = new Date();
    lastYear.setFullYear(today.getFullYear() - 1);
    
    startDateInput.value = lastYear.toISOString().slice(0, 7);
    endDateInput.value = today.toISOString().slice(0, 7);

    // Store chart instances so we can destroy them later
    let financeChartInstance;
    let categoryChartInstance;
    let finance_categories = [];

    // Fetch categories on page load
    function fetchCategories() {
        fetch("../finance/api/categories/", {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            finance_categories = data.finance_categories;
        })
        .catch(error => console.error("Error fetching categories:", error));
    }

    fetchCategories();

    financeAdd.addEventListener("click", async function () {
        fields = [
            { 
                id: "category", 
                label: "Kategorija", 
                type: "select", 
                required: true, 
                options: finance_categories.map(cat => ({
                    value: cat.id,
                    label: cat.name
                }))
            },
            { 
                id: "amount", 
                label: "Suma", 
                type: "number", 
                placeholder: "Įveskite sumą", 
                required: true, 
                step: "0.01",
                min: "-999999.99",
                max: "999999.99"
            },
            {
                id: "date",
                label: "Data",
                type: "datetime-local",
                required: true,
                value: new Date().toISOString().slice(0, 16)
            }
        ]  
        const formData = await openModal({
            title: `Pridėti finansinį įrašą`,
            fields: fields
        });

        if (formData) {
            // Validate amount
            const amount = parseFloat(formData.amount);
            if (isNaN(amount)) {
                alert("Klaida: Neteisingas sumos formatas");
                return;
            }

            // Create loading indicator
            const loadingIndicator = document.createElement('div');
            loadingIndicator.id = 'loading-indicator';
            loadingIndicator.textContent = 'Įrašoma...';
            document.body.appendChild(loadingIndicator);

            try {
                const response = await fetch("../list/api/list/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrfToken
                    },
                    body: JSON.stringify({ 
                        name: `Finance Operation ${new Date().toLocaleString()}`,
                        list_type: "FINANCE",
                        datetime: new Date(formData.date).getTime(),
                        amount: amount,
                        category: formData.category
                    })
                });

                const data = await response.json();
                
                if (data.success) {
                    processChartData(); // Update charts dynamically
                } else {
                    alert("Klaida: " + (data.error || "Nepavyko pridėti įrašo"));
                }
            } catch (error) {
                console.error("Klaida pridedant įrašą:", error);
                alert("Klaida: Nepavyko pridėti įrašo. Bandykite dar kartą.");
            } finally {
                // Remove loading indicator
                document.getElementById('loading-indicator')?.remove();
            }
        }
    });

    function createCharts(data) {
        // Destroy previous instances if they exist
        if (financeChartInstance) {
            financeChartInstance.destroy();
        }
        if (categoryChartInstance) {
            categoryChartInstance.destroy();
        }

        financeChartInstance = new Chart(financeCtx, {
            type: 'bar',
            data: {
                labels: data.chart.labels,
                datasets: [{
                    label: "Išlaidos",
                    data: data.chart.dataExp,
                    backgroundColor: "#36a2eb"
                }, {
                    label: "Įplaukos",
                    data: data.chart.dataInc,
                    backgroundColor: "rgba(75, 192, 192, 0.5)"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                return label + ': ' + context.parsed.y + ' Eur';
                            }
                        }
                    }
                }
            }
        });
        
        categoryChartInstance = new Chart(categoryCtx, {
            type: 'doughnut',
            data: {
                labels: data.pie.labels,
                datasets: [{
                    data: data.pie.data,
                    backgroundColor: data.pie.backgroundColor
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const dataset = context.chart.data.datasets[context.datasetIndex];
                                const currentValue = dataset.data[context.dataIndex];
                                const label = context.chart.data.labels[context.dataIndex] || '';
                                return label + ': ' + currentValue + ' Eur';
                            }
                        }
                    }
                }
            }
        });
    
        updateOperationsTable(data.all_operations);
    }
    
    // Add a new function to fetch and display operation items
    async function showOperationItems(operationId) {
        // Create loading indicator
        const loadingIndicator = document.createElement('div');
        loadingIndicator.id = 'loading-indicator';
        loadingIndicator.textContent = 'Kraunama...';
        document.body.appendChild(loadingIndicator);
        
        try {
            const response = await fetch(`/list/api/items/?list_id=${operationId}`, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                }
            });
            
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.status}`);
            }
            
            const data = await response.json();
            console.log("Items data:", data);
            
            // After fetching data, directly call the form function if no items
            if (!data.items || data.items.length === 0) {
                // If no items, directly open the add item dialog
                handleAddItemClick({ target: { dataset: { operationId } } });
                return;
            }
            
            // For items, proceed with displaying them
            // Create a table to display items
            let tableHtml = `
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Pavadinimas</th>
                                <th>Kiekis</th>
                                <th>Kaina</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            // Calculate total sum
            let totalAmount = 0;
            
            data.items.forEach(item => {
                // Format price with 2 decimal places if it exists
                let priceDisplay = '-';
                if (item.price !== null && item.price !== undefined) {
                    // Ensure price is treated as a number and formatted with 2 decimal places
                    const priceNum = parseFloat(item.price);
                    if (!isNaN(priceNum)) {
                        priceDisplay = priceNum.toFixed(2) + ' Eur';
                        // Add to total
                        if (item.quantity !== null && item.quantity !== undefined) {
                            totalAmount += priceNum * parseInt(item.quantity);
                        } else {
                            totalAmount += priceNum;
                        }
                    }
                }
                
                tableHtml += `
                    <tr>
                        <td>${item.name || '-'}</td>
                        <td>${item.quantity !== null && item.quantity !== undefined ? item.quantity : 1}</td>
                        <td>${priceDisplay}</td>
                    </tr>
                `;
            });
            
            // Add total row if we have any items with prices
            tableHtml += `
                </tbody>
                <tfoot>
                    <tr>
                        <th colspan="2" class="text-end">Viso:</th>
                        <th>${totalAmount.toFixed(2)} Eur</th>
                    </tr>
                </tfoot>
            </table>
            </div>
            `;
            
            // Create a simple modal by hand instead of trying to use the form modal
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.id = 'operationItemsModal';
            modal.tabIndex = '-1';
            modal.setAttribute('aria-hidden', 'true');
            
            modal.innerHTML = `
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Operacijos detalės</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            ${tableHtml}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Uždaryti</button>
                            <button type="button" class="btn btn-primary" id="add-more-items-btn">Pridėti dar</button>
                        </div>
                    </div>
                </div>
            `;
            
            // Add the modal to the body
            document.body.appendChild(modal);
            
            // Initialize the Bootstrap modal
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
            
            // Set up the "Add more" button
            document.getElementById('add-more-items-btn').addEventListener('click', () => {
                bsModal.hide();
                // Wait for modal to close completely before opening the add form
                setTimeout(() => {
                    handleAddItemClick({ target: { dataset: { operationId } } });
                }, 300);
            });
            
            // Clean up when modal is hidden
            modal.addEventListener('hidden.bs.modal', () => {
                document.body.removeChild(modal);
            });
            
        } catch (error) {
            console.error("Error fetching operation items:", error);
            alert("Klaida: Nepavyko gauti operacijos detalių.");
            // If error, still allow adding items
            handleAddItemClick({ target: { dataset: { operationId } } });
        } finally {
            // Remove loading indicator
            document.getElementById('loading-indicator')?.remove();
        }
    }
    
    function updateOperationsTable(operations) {
        operationsTable.innerHTML = "";
        
        if (!operations || operations.length === 0) {
            const row = document.createElement("tr");
            row.innerHTML = `<td colspan="3" class="text-center">Nėra operacijų pasirinktame laikotarpyje</td>`;
            operationsTable.appendChild(row);
            return;
        }
        
        console.log("Operations data:", operations);
        
        // Sort operations by date (newest first)
        operations.sort((a, b) => new Date(b.date) - new Date(a.date));
        
        operations.forEach(operation => {
            // Log each operation to verify ID is present
            console.log("Processing operation:", operation);
            
            const row = document.createElement("tr");
            row.classList.add('operation-row');
            row.dataset.operationId = operation.id;
            row.dataset.hasItems = operation.has_items ? 'true' : 'false';
            
            // Format the amount class and display
            let amountClass = '';
            if (operation.amount > 0) {
                amountClass = 'profit';
            } else if (operation.amount < 0) {
                amountClass = 'expense';
            }
            
            row.innerHTML = `
                <td>${operation.date}</td>
                <td>${operation.category}</td>
                <td class="${amountClass}">
                    ${operation.amount} Eur
                </td>
            `;
            
            operationsTable.appendChild(row);
        });
        
        // Add event listeners to all rows and buttons
        document.querySelectorAll('.operation-row').forEach(row => {
            // Make the entire row clickable
            row.addEventListener('click', function(e) {
                // Get the operation ID from this row
                const operationId = this.dataset.operationId;
                if (operationId) {
                    // Show items or add item form
                    showOperationItems(operationId);
                }
            });
        });
    }

    // Handler for add item button click
    async function handleAddItemClick(event) {
        const operationId = event.target.dataset.operationId;
        
        // Debug the operation ID
        console.log("Operation ID:", operationId);
        
        if (!operationId) {
            alert("Klaida: Operacijos ID nerastas");
            return;
        }
        
        const fields = [
            { 
                id: "name", 
                label: "Pavadinimas", 
                type: "text", 
                placeholder: "Įveskite pavadinimą", 
                required: true 
            },
            { 
                id: "quantity", 
                label: "Kiekis", 
                type: "number", 
                placeholder: "Įveskite kiekį", 
                required: true,
                min: "1",
                step: "1",
                value: "1"
            },
            { 
                id: "price", 
                label: "Kaina", 
                type: "number", 
                placeholder: "Įveskite kainą", 
                required: false,
                step: "0.01"
            }
        ];
        
        const formData = await openModal({
            title: `Pridėti įrašą į operaciją (ID: ${operationId})`,
            fields: fields
        });
        
        if (formData) {
            // Create loading indicator
            const loadingIndicator = document.createElement('div');
            loadingIndicator.id = 'loading-indicator';
            loadingIndicator.textContent = 'Įrašoma...';
            document.body.appendChild(loadingIndicator);
            
            try {
                console.log("Sending request with operation ID:", operationId);
                
                const payload = { 
                    name: formData.name,
                    quantity: parseInt(formData.quantity) || 1,
                    price: formData.price ? parseFloat(formData.price) : null,
                    list_id: operationId
                };
                
                console.log("Request payload:", payload);
                
                const response = await fetch("/list/api/item/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrfToken
                    },
                    body: JSON.stringify(payload)
                });
                
                // Log the raw response
                console.log("Response status:", response.status);
                console.log("Response headers:", [...response.headers.entries()]);
                
                const data = await response.json();
                console.log("Response data:", data);
                
                if (data.success) {
                    // First refresh the charts and operations data
                    processChartData();
                    
                    // Then show the updated items for this operation
                    setTimeout(() => {
                        showOperationItems(operationId);
                    }, 500); // Small delay to allow the backend to update
                } else {
                    console.error("API error:", data);
                    alert("Klaida: " + (data.error || "Nepavyko pridėti įrašo"));
                }
            } catch (error) {
                console.error("Klaida pridedant įrašą:", error);
                alert("Klaida: Nepavyko pridėti įrašo. Bandykite dar kartą.");
            } finally {
                // Remove loading indicator
                document.getElementById('loading-indicator')?.remove();
            }
        }
    }

    // New function to handle form submission
    async function submitItemForm(formData, operationId) {
        // Create loading indicator
        const loadingIndicator = document.createElement('div');
        loadingIndicator.id = 'loading-indicator';
        loadingIndicator.textContent = 'Įrašoma...';
        document.body.appendChild(loadingIndicator);
        
        try {
            console.log("Sending request with operation ID:", operationId);
            
            const payload = { 
                name: formData.name,
                quantity: parseInt(formData.quantity) || 1,
                price: formData.price ? parseFloat(formData.price) : null,
                list_id: operationId
            };
            
            console.log("Request payload:", payload);
            
            const response = await fetch("/list/api/item/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify(payload)
            });
            
            // Log the raw response
            console.log("Response status:", response.status);
            console.log("Response headers:", [...response.headers.entries()]);
            
            const data = await response.json();
            console.log("Response data:", data);
            
            if (data.success) {
                // First refresh the charts and operations data
                processChartData();
                
                // Then show the updated items for this operation
                setTimeout(() => {
                    showOperationItems(operationId);
                }, 500); // Small delay to allow the backend to update
            } else {
                console.error("API error:", data);
                alert("Klaida: " + (data.error || "Nepavyko pridėti įrašo"));
            }
        } catch (error) {
            console.error("Klaida pridedant įrašą:", error);
            alert("Klaida: Nepavyko pridėti įrašo. Bandykite dar kartą.");
        } finally {
            // Remove loading indicator
            document.getElementById('loading-indicator')?.remove();
        }
    }

    function processChartData() {
        // Extract year and month from the input values (format: "YYYY-MM")
        const [startYear, startMonth] = startDateInput.value.split("-");
        const [endYear, endMonth] = endDateInput.value.split("-");

        // Build the URL with query parameters
        const url = `../finance/api/dashboard/?startYear=${startYear}&startMonth=${startMonth}&endYear=${endYear}&endMonth=${endMonth}`;

        fetch(url, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            createCharts(data.data);
        })
        .catch(error => console.error("Error fetching data:", error));
    }

    // Initial data load
    processChartData();
    
    // Event listeners
    startDateInput.addEventListener('change', processChartData);
    endDateInput.addEventListener('change', processChartData);
    refreshBtn.addEventListener('click', processChartData);
}); 