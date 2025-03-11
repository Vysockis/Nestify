document.addEventListener("DOMContentLoaded", function() {
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const financeCtx = document.getElementById('financeChart').getContext('2d');
    const categoryCtx = document.getElementById('categoryChart').getContext('2d');
    const newestExpensesList = document.getElementById('newest-expenses');
    const financeAdd = document.getElementById("addFinanceBtn");

    const today = new Date();
    const lastYear = new Date();
    lastYear.setFullYear(today.getFullYear() - 1);
    
    startDateInput.value = lastYear.toISOString().slice(0, 7);
    endDateInput.value = today.toISOString().slice(0, 7);

    // Store chart instances so we can destroy them later
    let financeChartInstance;
    let categoryChartInstance;

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
    
        updateExpensesList(data.newest);
    }
    
    function updateExpensesList(newestExpenses) {
        newestExpensesList.innerHTML = "";
        newestExpenses.forEach(expense => {
            const li = document.createElement("li");
            if (expense.amount > 0) {
                li.innerHTML = `${expense.category}<span class="price profit">${expense.amount} Eur</span>`;
            }
            else if (expense.amount < 0) {
                li.innerHTML = `${expense.category}<span class="price expense">${expense.amount} Eur</span>`;
            }
            else {
                li.innerHTML = `${expense.category}<span class="price">${expense.amount} Eur</span>`;
            }
            newestExpensesList.appendChild(li);
        });
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
            console.log(data);
            createCharts(data.data);
        })
        .catch(error => console.error("Error fetching data:", error));
    }

    processChartData();
    startDateInput.addEventListener('change', processChartData);
    endDateInput.addEventListener('change', processChartData);
});
