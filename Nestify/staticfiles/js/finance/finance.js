document.addEventListener("DOMContentLoaded", function() {
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const financeCtx = document.getElementById('financeChart').getContext('2d');
    const categoryCtx = document.getElementById('categoryChart').getContext('2d');
    const operationsTable = document.getElementById('operations-table');
    const financeAdd = document.getElementById("addFinanceBtn");
    const refreshBtn = document.getElementById("refreshFinanceBtn");
    const categoryFilter = document.getElementById("category-filter");

    let currentOperations = []; // Store current operations for filtering

    const today = new Date();
    const lastYear = new Date();
    lastYear.setFullYear(today.getFullYear() - 1);
    
    startDateInput.value = lastYear.toISOString().slice(0, 7);
    endDateInput.value = today.toISOString().slice(0, 7);

    // Store chart instances so we can destroy them later
    let financeChartInstance;
    let categoryChartInstance;
    let finance_categories = [];

    // Add Font Awesome CSS if not already present
    if (!document.querySelector('link[href*="fontawesome"]')) {
        const fontAwesomeLink = document.createElement('link');
        fontAwesomeLink.rel = 'stylesheet';
        fontAwesomeLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css';
        document.head.appendChild(fontAwesomeLink);
    }

    // Add event listener for category filter changes
    if (categoryFilter) {
        categoryFilter.addEventListener('change', function() {
            if (currentOperations.length > 0) {
                updateOperationsTable(currentOperations);
            }
        });
    }

    // Fetch categories and populate filter
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
            
            // Populate category filter dropdown
            if (categoryFilter) {
                // Keep the "All categories" option
                categoryFilter.innerHTML = '<option value="">Visos kategorijos</option>';
                
                // Add each category
                finance_categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category.name;
                    option.textContent = category.name;
                    categoryFilter.appendChild(option);
                });
            }
        })
        .catch(error => console.error("Error fetching categories:", error));
    }

    // Call fetchCategories on page load
    fetchCategories();

    financeAdd.addEventListener("click", async function () {
        try {
            const scanOptions = [
                {
                    id: "scan_type",
                    label: "Įvedimo būdas",
                    type: "select",
                    required: true,
                    options: [
                        { value: "manual", label: "Įvesti rankiniu būdu" },
                        { value: "receipt", label: "Nuskaityti kvitą" }
                    ]
                }
            ];
            
            // Show type selection modal
            const scanChoice = await openModal({
                title: "Pasirinkite įvedimo būdą",
                fields: scanOptions
            });
            
            // If modal was closed without a selection, just return
            if (!scanChoice) return;
            
            console.log("Scan choice selected:", scanChoice.scan_type);
            
            // Make sure we wait just a little bit before showing the next modal
            await new Promise(resolve => setTimeout(resolve, 300));
            
            // Process the selection
            if (scanChoice.scan_type === "receipt") {
                // Receipt scanning option
                const receiptFields = [
                    {
                        id: "receipt_image",
                        label: "Įkelkite kvito nuotrauką",
                        type: "image",
                        required: true
                    }
                ];
                
                console.log("Opening receipt upload modal");
                const receiptData = await openModal({
                    title: "Kvito nuskaitymas",
                    fields: receiptFields
                });
                
                if (receiptData && receiptData.receipt_image) {
                    // Show loading indicator
                    const loadingIndicator = document.createElement('div');
                    loadingIndicator.id = 'loading-indicator';
                    loadingIndicator.textContent = 'Nuskaitoma...';
                    document.body.appendChild(loadingIndicator);
                    
                    try {
                        // Process receipt image
                        const formData = new FormData();
                        formData.append('receipt_image', receiptData.receipt_image);
                        
                        const response = await fetch("/finance/api/scan-receipt/", {
                            method: "POST",
                            headers: {
                                "X-CSRFToken": csrfToken
                            },
                            body: formData
                        });
                        
                        if (!response.ok) {
                            throw new Error("Failed to scan receipt");
                        }
                        
                        const extractedData = await response.json();
                        
                        // Find the category to check if it's income
                        const categoryId = extractedData.category_id || finance_categories[0].id;
                        const selectedCategory = finance_categories.find(cat => cat.id === categoryId);
                        
                        // Determine the sign based on the category type
                        let finalAmount = Math.abs(extractedData.total_amount);
                        if (selectedCategory && selectedCategory.income) {
                            // Income category - amount should be positive
                            finalAmount = Math.abs(finalAmount);
                        } else {
                            // Expense category - amount should be negative
                            finalAmount = -Math.abs(finalAmount);
                        }
                        
                        // Now use the extracted data to create a finance operation
                        const data = await createFinanceOperation({
                            category: categoryId,
                            amount: finalAmount,
                            date: new Date().toISOString()
                        });
                        
                        if (data.success && data.list_id) {
                            // Add items from receipt
                            for (const item of extractedData.items) {
                                await addReceiptItem(data.list_id, item);
                            }
                            
                            // Refresh the charts
                            processChartData();
                        }
                    } catch (error) {
                        console.error("Error scanning receipt:", error);
                        alert("Klaida: Nepavyko nuskaityti kvito. Bandykite įvesti rankiniu būdu.");
                    } finally {
                        document.getElementById('loading-indicator')?.remove();
                    }
                }
            } else {
                // Regular manual input
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
                ];
                
                console.log("Opening manual input modal");
                const formData = await openModal({
                    title: `Pridėti finansinį įrašą`,
                    fields: fields
                });

                if (formData) {
                    await createFinanceOperation(formData);
                }
            }
        } catch (error) {
            console.error("Error in finance add process:", error);
            alert("Klaida apdorojant jūsų užklausą. Bandykite dar kartą.");
        }
    });
    
    // Helper function to create finance operation
    async function createFinanceOperation(formData) {
        // Validate amount
        const amount = parseFloat(formData.amount);
        if (isNaN(amount)) {
            alert("Klaida: Neteisingas sumos formatas");
            return { success: false };
        }

        // Create loading indicator
        const loadingIndicator = document.createElement('div');
        loadingIndicator.id = 'loading-indicator';
        loadingIndicator.textContent = 'Įrašoma...';
        document.body.appendChild(loadingIndicator);

        try {
            // Find the selected category to check if it's income
            const selectedCategoryId = parseInt(formData.category);
            const selectedCategory = finance_categories.find(cat => cat.id === selectedCategoryId);
            
            // Determine the correct sign for the amount
            let finalAmount = Math.abs(amount);
            if (selectedCategory && selectedCategory.income) {
                // Income category - amount should be positive
                finalAmount = Math.abs(finalAmount);
            } else {
                // Expense category - amount should be negative
                finalAmount = -Math.abs(finalAmount);
            }

            const response = await fetch("../list/api/list/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({ 
                    name: `Finance Operation ${new Date().toLocaleString()}`,
                    list_type: "FINANCE",
                    datetime: formData.date ? new Date(formData.date).getTime() : new Date().getTime(),
                    amount: finalAmount,
                    category: formData.category
                })
            });

            const data = await response.json();
            
            if (data.success) {
                processChartData(); // Update charts dynamically
                return data;
            } else {
                alert("Klaida: " + (data.error || "Nepavyko pridėti įrašo"));
                return { success: false };
            }
        } catch (error) {
            console.error("Klaida pridedant įrašą:", error);
            alert("Klaida: Nepavyko pridėti įrašo. Bandykite dar kartą.");
            return { success: false };
        } finally {
            // Remove loading indicator
            document.getElementById('loading-indicator')?.remove();
        }
    }
    
    // Helper function to add items from receipt
    async function addReceiptItem(listId, item) {
        try {
            const response = await fetch("/list/api/item/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({
                    name: item.name,
                    quantity: item.quantity || 1,
                    price: item.price,
                    list_id: listId
                })
            });
            
            return await response.json();
        } catch (error) {
            console.error("Error adding receipt item:", error);
            return { success: false };
        }
    }

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
                                <th>Veiksmai</th>
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
                        <td>${item.qty !== null && item.qty !== undefined ? item.qty : 1}</td>
                        <td>${priceDisplay}</td>
                        <td class="text-end">
                            <div class="btn-group">
                                <button class="btn btn-sm btn-outline-secondary me-2 edit-item-btn" data-item-id="${item.id}">
                                    <i class="fas fa-pencil"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger delete-item-btn" data-item-id="${item.id}">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            });
            
            // Add total row if we have any items with prices
            tableHtml += `
                </tbody>
                <tfoot>
                    <tr>
                        <th colspan="3" class="text-end">Viso:</th>
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
            
            // Set up delete buttons for each item
            document.querySelectorAll('.delete-item-btn').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation(); // Prevent event bubbling
                    
                    const itemId = btn.dataset.itemId;
                    if (!itemId) {
                        alert("Klaida: Elemento ID nerastas");
                        return;
                    }
                    
                    if (confirm("Ar tikrai norite ištrinti šį elementą?")) {
                        try {
                            const response = await fetch("/list/api/item/", {
                                method: "DELETE",
                                headers: {
                                    "Content-Type": "application/json",
                                    "X-CSRFToken": csrfToken
                                },
                                body: JSON.stringify({ item_id: itemId })
                            });
                            
                            const data = await response.json();
                            
                            if (data.success) {
                                // Close the current modal
                                bsModal.hide();
                                
                                // Refresh the data and reshow the modal with updated items
                                setTimeout(() => {
                                    processChartData(); // Refresh all data
                                    showOperationItems(operationId); // Reshow the modal with updated items
                                }, 300);
                            } else {
                                alert("Klaida: " + (data.error || "Nepavyko ištrinti elemento"));
                            }
                        } catch (error) {
                            console.error("Klaida trinant elementą:", error);
                            alert("Klaida: Nepavyko ištrinti elemento");
                        }
                    }
                });
            });
            
            // Add event listeners for edit buttons
            document.querySelectorAll('.edit-item-btn').forEach(button => {
                button.addEventListener('click', async function() {
                    const itemId = this.dataset.itemId;
                    const item = data.items.find(i => i.id === parseInt(itemId));
                    
                    if (item) {
                        const fields = [
                            { 
                                id: "name", 
                                label: "Pavadinimas", 
                                type: "text", 
                                required: true,
                                value: item.name || ''
                            },
                            { 
                                id: "quantity", 
                                label: "Kiekis", 
                                type: "number", 
                                required: true,
                                min: "1",
                                step: "1",
                                value: item.qty || 1
                            },
                            { 
                                id: "amount", 
                                label: "Suma", 
                                type: "number", 
                                required: true,
                                step: "0.01",
                                value: item.price || ''
                            }
                        ];
                        
                        const formData = await openModal({
                            title: "Redaguoti operacijos elementą",
                            fields: fields
                        });
                        
                        if (formData) {
                            try {
                                const response = await fetch(`/finance/api/operation-items/${itemId}/edit/`, {
                                    method: "POST",
                                    headers: {
                                        "Content-Type": "application/json",
                                        "X-CSRFToken": csrfToken
                                    },
                                    body: JSON.stringify(formData)
                                });
                                
                                const data = await response.json();
                                
                                if (data.success) {
                                    // Close the current modal
                                    bsModal.hide();
                                    
                                    // Refresh the data and reshow the modal with updated items
                                    setTimeout(() => {
                                        showOperationItems(operationId);
                                    }, 300);
                                } else {
                                    alert("Klaida: " + (data.error || "Nepavyko atnaujinti elemento"));
                                }
                            } catch (error) {
                                console.error("Error editing operation item:", error);
                                alert("Klaida: Nepavyko atnaujinti elemento. Bandykite dar kartą.");
                            }
                        }
                    }
                });
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
        currentOperations = operations; // Store operations for filtering
        const selectedCategory = categoryFilter ? categoryFilter.value : '';
        
        // Filter operations if category is selected
        const filteredOperations = selectedCategory 
            ? operations.filter(op => op.category === selectedCategory)
            : operations;

        if (operationsTable) {
            operationsTable.innerHTML = '';
            
            if (filteredOperations.length === 0) {
                const emptyRow = document.createElement('tr');
                emptyRow.innerHTML = '<td colspan="4" class="text-center">Nėra operacijų</td>';
                operationsTable.appendChild(emptyRow);
                return;
            }

            filteredOperations.forEach(operation => {
                const row = document.createElement('tr');
                const date = new Date(operation.date);
                const formattedDate = date.toLocaleDateString('lt-LT');
                
                row.innerHTML = `
                    <td>${formattedDate}</td>
                    <td>${operation.category}</td>
                    <td class="${operation.amount < 0 ? 'text-danger' : 'text-success'}">${operation.amount} Eur</td>
                    <td class="text-end">
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-secondary me-2 view-items" data-operation-id="${operation.id}">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-secondary me-2 edit-operation" data-operation-id="${operation.id}">
                                <i class="fas fa-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger delete-operation" data-operation-id="${operation.id}">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                `;
                
                operationsTable.appendChild(row);
            });

            // Add event listeners for the new buttons
            document.querySelectorAll('.view-items').forEach(button => {
                button.addEventListener('click', function() {
                    const operationId = this.dataset.operationId;
                    showOperationItems(operationId);
                });
            });

            document.querySelectorAll('.delete-operation').forEach(button => {
                button.addEventListener('click', async function() {
                    if (confirm('Ar tikrai norite ištrinti šį įrašą?')) {
                        const operationId = this.dataset.operationId;
                        try {
                            const response = await fetch(`/finance/api/operations/${operationId}/delete/`, {
                                method: 'POST',
                                headers: {
                                    'X-CSRFToken': csrfToken
                                }
                            });
                            
                            if (response.ok) {
                                processChartData(); // Refresh data
                            } else {
                                alert('Klaida trinant operaciją');
                            }
                        } catch (error) {
                            console.error('Error deleting operation:', error);
                            alert('Klaida trinant operaciją');
                        }
                    }
                });
            });

            // Add event listeners for edit buttons
            document.querySelectorAll('.edit-operation').forEach(button => {
                button.addEventListener('click', async function() {
                    const operationId = this.dataset.operationId;
                    const operation = currentOperations.find(op => op.id === parseInt(operationId));
                    
                    if (operation) {
                        const fields = [
                            { 
                                id: "date", 
                                label: "Data", 
                                type: "datetime-local", 
                                required: true,
                                value: new Date(operation.date).toISOString().slice(0, 16)
                            },
                            { 
                                id: "amount", 
                                label: "Suma", 
                                type: "number", 
                                required: true,
                                step: "0.01",
                                value: operation.amount
                            }
                        ];
                        
                        const formData = await openModal({
                            title: "Redaguoti operaciją",
                            fields: fields
                        });
                        
                        if (formData) {
                            try {
                                const response = await fetch(`/finance/api/operations/${operationId}/edit/`, {
                                    method: "POST",
                                    headers: {
                                        "Content-Type": "application/json",
                                        "X-CSRFToken": csrfToken
                                    },
                                    body: JSON.stringify(formData)
                                });
                                
                                const data = await response.json();
                                
                                if (data.success) {
                                    processChartData();
                                } else {
                                    alert("Klaida: " + (data.error || "Nepavyko atnaujinti operacijos"));
                                }
                            } catch (error) {
                                console.error("Error editing operation:", error);
                                alert("Klaida: Nepavyko atnaujinti operacijos. Bandykite dar kartą.");
                            }
                        }
                    }
                });
            });
        }
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