document.addEventListener("DOMContentLoaded", function () {
    const plansContainer = document.getElementById("plansContainer");
    const planAdd = document.getElementById("addPlanBtn");

    planAdd.addEventListener("click", async function () {
        const fields = [
            { id: "name", label: "Pavadinimas", type: "text", placeholder: "Įveskite pavadinimą", required: true },
            { id: "description", label: "Aprašymas", type: "textarea", placeholder: "Aprašymas...", required: false },
            { 
                id: "plan_type", label: "Tipas", type: "select", required: true, 
                options: [
                    { value: "MEAL", label: "Maisto planas" },
                    { value: "VACATION", label: "Atostogos" },
                    { value: "OTHER", label: "Kiti planai" }
                ] 
            },
            { id: "image", label: "Nuotrauka", type: "image", required: false }, // Added image field
            { id: "datetime", label: "Data ir laikas", type: "datetime-local", required: true, today: true }
        ];  
    
        const formData = await openModal({
            title: `Pridėti įrašą`,
            fields: fields
        });
    
        if (formData) {
            const fd = new FormData(); // Create FormData object
    
            // Append all keys from formData to FormData instance
            for (const key in formData) {
                if (formData[key] instanceof File) {
                    fd.append(key, formData[key], formData[key].name); // Append image correctly
                } else {
                    fd.append(key, formData[key]);
                }
            }
    
            fetch("../plan/api/plan/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken // CSRF token for Django
                },
                body: fd // Send FormData instead of JSON
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    fetchFamilyPlans(); // Update the list dynamically
                } else {
                    alert("Klaida: " + JSON.stringify(data.error));
                }
            })
            .catch(error => console.error("Klaida pridedant įrašą:", error));
        }
    });

    // Fetch family list from the API
    function fetchFamilyPlans() {
        fetch("../plan/api/plans/")  // Django API URL
            .then(response => response.json())
            .then(data => {
                console.log(data)
                plansContainer.innerHTML = "";  // Clear existing content

                if (data.plan_list.length === 0) {
                    plansContainer.innerHTML = "<p>No lists found.</p>";
                    return;
                }

                data.plan_list.forEach((plan, index) => {
                    const planElement = document.createElement("li");
                    planElement.classList.add("list-group-item", "d-flex", "justify-content-between", "align-items-center", "toggle-list");
                    planElement.setAttribute("data-toggle", `plan-${plan.id}`);

                    planElement.innerHTML = `
                        <span>${plan.name}</span>
                        <span class="text-muted">${plan.date}</span>
                    `;

                    plansContainer.appendChild(planElement);

                    planElement.addEventListener("click", function () {
                        window.location.href = `../plan/?planId=${plan.id}`;
                    });
                });

                //addToggleFunctionality(); // Attach click event to newly created elements
            })
            .catch(error => console.error("Error fetching lists:", error));
    }

    fetchFamilyPlans(); // Initial API call to populate data
});
