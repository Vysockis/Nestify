document.addEventListener("DOMContentLoaded", function () {
    // Get DOM elements
    const planContainer = document.getElementById("planContainer"); // Plan list container
    if (!planContainer) {
        console.error("Plan container element not found! ID: planContainer");
        return; // Exit if essential element is missing
    }
    
    const planDisplay = document.getElementById("list"); // Main plan display container 
    const addPlanMemberBtn = document.getElementById("addPlanMemberBtn");
    const addPlanItemBtn = document.getElementById("addPlanItemBtn");
    const addPlanBtn = document.getElementById("addPlanBtn");
    const editDescriptionBtn = document.getElementById("editDescriptionBtn");
    const planTypeFilter = document.getElementById("planTypeFilter"); // Add reference to the filter
    
    if (!planTypeFilter) {
        console.warn("Plan type filter not found!");
    }
    
    console.log("Essential DOM elements loaded:", {
        planContainer: !!planContainer,
        planDisplay: !!planDisplay,
        planTypeFilter: !!planTypeFilter
    });

    let plansData = []; // Global storage for fetched plans
    let filteredPlansData = []; // Store filtered plans

    // Get CSRF token for POST requests
    let csrfToken = '';
    
    // Try to get CSRF token from meta tag
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken) {
        csrfToken = metaToken.getAttribute('content');
    } 
    // Fallback: try to get from cookies
    else {
        const tokenCookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
        if (tokenCookie) {
            csrfToken = tokenCookie.split('=')[1];
        }
    }
    
    console.log("CSRF Token loaded:", csrfToken ? "Yes" : "No");

    // Event listener for editing plan description
    editDescriptionBtn.addEventListener("click", function () {
        const planId = editDescriptionBtn.dataset.planId;
        if (!planId) {
            console.error("No plan ID found.");
            return;
        }
        const plan = plansData.find(p => p.id.toString() === planId);
        if (!plan) {
            console.error("Plan not found in data.");
            return;
        }
        openEditPlanModal(plan);
    });

    // Event listener for adding a member to a plan
    addPlanMemberBtn.addEventListener("click", function () {
        const planId = addPlanMemberBtn.dataset.planId;
        if (!planId) {
            console.error("No plan ID found.");
            return;
        }
        // Open modal to add a new plan member (replace with actual modal function)
        openAddPlanMemberModal(planId);
    });

    addPlanItemBtn.addEventListener("click", function () {
        const listId = addPlanItemBtn.dataset.listId;
        const planId = addPlanMemberBtn.dataset.planId;
        if (!listId) {
            console.error("No plan ID found.");
            return;
        }
        // Open modal to add a new plan member (replace with actual modal function)
        openAddPlanItemModal(listId, planId);
    });

    addPlanBtn.addEventListener("click", function () {
        openAddPlanModal();
    });

    // Add event listener for the type filter dropdown
    planTypeFilter.addEventListener("change", function() {
        filterAndDisplayPlans();
    });

    async function openAddPlanItemModal(listId, planId) {
        fields = [
            { id: "name", label: "Pavadinimas", type: "text", placeholder: "Įveskite pavadinimą", required: true }
        ] 
    
        const formData = await openModal({
            title: `Pridėti įrašą`,
            fields: fields
        });
    
        if (formData) {
            fetch("../list/api/item/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({ list_id: listId, ...formData })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (planId) {
                        const newUrl = new URL(window.location.href);
                        newUrl.searchParams.set("planId", planId);
                        window.history.pushState({}, "", newUrl); 
                    }

                    fetchPlanList();
                } else {
                    alert("Klaida: " + JSON.stringify(data.error));
                }
            })
            .catch(error => console.error("Klaida pridedant įrašą:", error));
        }
    }

    async function openAddPlanMemberModal(planId) {
        let memberOption = [];
        console.log(family_members)
        family_members.forEach(element => {
            memberOption.push({
                value: element.id,
                label: element.name
            });
        });

        fields = [
            { 
                id: "member_id", label: "Pasirinkite žmogų", type: "select", required: true, 
                options: memberOption
            }
        ];
    
        const formData = await openModal({
            title: `Pridėti įrašą`,
            fields: fields
        });
    
        if (formData) {
            fetch("../plan/api/member/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({ plan_id: planId, ...formData })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const newPlanId = data.plan_id;

                    if (newPlanId) {
                        const newUrl = new URL(window.location.href);
                        newUrl.searchParams.set("planId", newPlanId);
                        window.history.pushState({}, "", newUrl); 
                    }

                    fetchPlanList();
                } else {
                    alert("Klaida: " + JSON.stringify(data.error));
                }
            })
            .catch(error => console.error("Klaida pridedant įrašą:", error));
        }
    }

    async function openAddPlanModal() {
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
            { id: "image", label: "Nuotrauka", type: "image", required: false },
            { id: "datetime", label: "Data ir laikas", type: "datetime-local", required: true, today: true }
        ];  
    
        const formData = await openModal({
            title: `Pridėti įrašą`,
            fields: fields
        });
    
        if (formData) {
            const fd = new FormData();
    
            for (const key in formData) {
                if (formData[key] instanceof File) {
                    fd.append(key, formData[key], formData[key].name);
                } else {
                    fd.append(key, formData[key]);
                }
            }
    
            fetch("../plan/api/plan/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: fd
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const newPlanId = data.plan_id;

                    if (newPlanId) {
                        const newUrl = new URL(window.location.href);
                        newUrl.searchParams.set("planId", newPlanId);
                        window.history.pushState({}, "", newUrl); 
                    }

                    fetchPlanList();
                } else {
                    alert("Klaida: " + JSON.stringify(data.error));
                }
            })
            .catch(error => console.error("Klaida pridedant įrašą:", error));
        }
    }

    async function openEditPlanModal(plan) {
        const fields = [
            { id: "name", label: "Pavadinimas", type: "text", placeholder: "Įveskite pavadinimą", required: true, value: plan.name, visible: false },
            { id: "description", label: "Aprašymas", type: "textarea", placeholder: "Aprašymas...", required: false, value: plan.description },
            { id: "plan_type", type: "hidden", required: true, value: plan.plan_type, visible: false },
            { id: "image", label: "Nuotrauka", type: "image", required: false },
            { id: "datetime", label: "Data ir laikas", type: "datetime-local", required: true, value: plan.datetime, visible: false }
        ];
        
        const formData = await openModal({
            title: `Redaguoti planą`,
            fields: fields
        });

        if (formData) {
            const fd = new FormData();
            // Add the plan ID to identify which plan to update
            fd.append("plan_id", plan.id);
            
            for (const key in formData) {
                if (formData[key] instanceof File) {
                    fd.append(key, formData[key], formData[key].name);
                } else {
                    fd.append(key, formData[key]);
                }
            }
            
            fetch("../plan/api/plan/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: fd
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update URL with planId
                    const newUrl = new URL(window.location.href);
                    newUrl.searchParams.set("planId", plan.id);
                    window.history.pushState({}, "", newUrl);
                    
                    fetchPlanList(); // Update list dynamically
                } else {
                    alert("Klaida: " + JSON.stringify(data.error));
                }
            })
            .catch(error => console.error("Klaida atnaujinant planą:", error));
        }
    }
    
    // Function to filter and display plans based on selected type
    function filterAndDisplayPlans() {
        const selectedType = planTypeFilter.value;
        
        // Filter the plans data based on selected type
        filteredPlansData = selectedType === "ALL" 
            ? [...plansData] // Show all plans
            : plansData.filter(plan => plan.plan_type === selectedType);
        
        // Clear existing content
        planContainer.innerHTML = "";
        
        if (!filteredPlansData || filteredPlansData.length === 0) {
            planContainer.innerHTML = "<p>Nėra planų pagal pasirinktą tipą.</p>";
            return;
        }
        
        // Get planId from URL
        const urlParams = new URLSearchParams(window.location.search);
        const urlPlanId = urlParams.get("planId");
        
        let foundPlan = null;
        
        // Display filtered plans
        filteredPlansData.forEach((plan) => {
            const listElement = document.createElement("li");
            listElement.classList.add(
                "list-group-item",
                "d-flex",
                "justify-content-between",
                "align-items-center",
                "toggle-plan"
            );
            listElement.setAttribute("data-toggle", `plan-${plan.id}`);
            
            // Create text container for name and date
            const textContainer = document.createElement("div");
            textContainer.classList.add("plan-text-container");
            
            // Create name span
            const nameSpan = document.createElement("div");
            nameSpan.classList.add("plan-name");
            nameSpan.textContent = plan.name;
            
            // Create date span
            const dateSpan = document.createElement("div");
            dateSpan.classList.add("plan-date");
            dateSpan.textContent = plan.date_formatted;
            
            // Append name and date to container
            textContainer.appendChild(nameSpan);
            textContainer.appendChild(dateSpan);
            listElement.appendChild(textContainer);
            
            // Create delete button
            const deleteBtn = document.createElement("button");
            deleteBtn.classList.add("btn", "btn-sm", "btn-outline-danger");
            deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
            // Hide delete button for kid users
            if (window.isKid) {
                deleteBtn.style.display = 'none';
            }
            deleteBtn.addEventListener("click", function(event) {
                event.stopPropagation(); // Prevent plan item click
                if (confirm("Ar tikrai norite ištrinti šį planą?")) {
                    fetch("../plan/api/plan/", {
                        method: "DELETE",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRFToken": csrfToken
                        },
                        body: JSON.stringify({ plan_id: plan.id })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            fetchPlanList(); // Refresh the list
                        } else {
                            alert("Klaida: " + JSON.stringify(data.error));
                        }
                    })
                    .catch(error => console.error("Klaida trinant planą:", error));
                }
            });
            
            listElement.appendChild(deleteBtn);
            planContainer.appendChild(listElement);

            // Check if this plan is the one from the URL
            if (urlPlanId && plan.id.toString() === urlPlanId) {
                foundPlan = plan;
                listElement.classList.add("active"); // Mark as active
            }
        });

        // Add toggle functionality to plan items
        addToggleFunctionality();

        // If a valid planId was found, update the display accordingly
        if (foundPlan) {
            updatePlanDisplay(foundPlan);
        } else if (filteredPlansData.length > 0) {
            // Set the first plan as active by default if no specific plan is selected
            const firstItem = planContainer.querySelector(".toggle-plan");
            if (firstItem) {
                firstItem.classList.add("active");
                updatePlanDisplay(filteredPlansData[0]);
            }
        }
    }

    // Fetch list of plans from the API
    function fetchPlanList() {
        // Įsitikinti, kad turime CSRF token
        if (!csrfToken) {
            const tokenMeta = document.querySelector('meta[name="csrf-token"]');
            if (tokenMeta) {
                csrfToken = tokenMeta.getAttribute('content');
            }
        }
        
        fetch("api/plans/")  // Adjust this Django API URL as needed
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                if (data && data.plan_list) {
                    plansData = data.plan_list; // Save plans for later reference
                    
                    // Log the data to debug
                    console.log("Loaded plans:", plansData);
                    
                    // Update the plan type dropdown to include all plan types that exist in the data
                    filterAndDisplayPlans();
                } else {
                    console.error("Invalid data format received:", data);
                    planContainer.innerHTML = "<p>Klaida gaunant planus.</p>";
                }
            })
            .catch(error => {
                console.error("Klaida gaunant planus:", error);
                planContainer.innerHTML = "<p>Klaida gaunant planus.</p>";
            });
    }
    

    // Attach click events to each plan item to update the main display
    function addToggleFunctionality() {
        const togglePlanItems = document.querySelectorAll(".toggle-plan");
        togglePlanItems.forEach(item => {
            item.addEventListener("click", function () {
                togglePlanItems.forEach(el => el.classList.remove("active")); // Remove active class from all
                this.classList.add("active"); // Add active class to clicked item

                const planId = this.getAttribute("data-toggle").split("-")[1]; // Extract ID
                const plan = plansData.find(p => p.id.toString() === planId);
                if (plan) {
                    updatePlanDisplay(plan);
                }
            });
        });
    }

    // Update the main plan display with selected plan details
    function updatePlanDisplay(plan) {
        if (!planDisplay) {
            console.error("Plan display element not found");
            return;
        }
        if (!plan) {
            console.error("Plan data is empty");
            return;
        }

        console.log("Updating plan display with:", plan);

        const imageDiv = planDisplay.querySelector(".plans-image-content");
        if (imageDiv) {
            imageDiv.style.backgroundImage = plan.image ? `url('${plan.image}')` : 'none';
        } else {
            console.warn("Image div not found in plan display");
        }

        const nameEl = planDisplay.querySelector(".plans-image-text");
        if (nameEl) {
            nameEl.textContent = plan.name;
        } else {
            console.warn("Name element not found in plan display");
        }

        const descriptionEl = planDisplay.querySelector("#planDescription");
        if (descriptionEl) {
            descriptionEl.innerHTML = plan.description ? plan.description.replace(/\n/g, "<br>") : '';
        } else {
            console.warn("Description element not found in plan display");
        }

        if (addPlanItemBtn) {
            addPlanItemBtn.dataset.listId = plan.listId;
            if (addPlanMemberBtn) addPlanMemberBtn.dataset.planId = plan.id;
            if (editDescriptionBtn) editDescriptionBtn.dataset.planId = plan.id;
        } else {
            console.warn("Action buttons not found");
        }

        updateListItems(plan);
        updatePlanMembers(plan);
    }

    // Fetch and update list items inside #listContainer
    function updateListItems(plan) {
        const listContainer = document.getElementById("planItemList"); // Target list container
        if (!listContainer) return;
        listContainer.innerHTML = ""; // Clear previous members

        if (plan.listitems.length === 0) {
            listContainer.innerHTML = "<p class='text-muted'>Nėra įrašų.</p>"; // Show loading state
            return;
        }

        plan.listitems.forEach(item => {
            const listItem = document.createElement("li");
            listItem.classList.add("list-group-item", "d-flex", "justify-content-between", "align-items-center");

            // Create wrapper div for name
            const nameDiv = document.createElement("div");
            nameDiv.textContent = item.name;

            // Create delete button
            const deleteButton = document.createElement("button");
            deleteButton.classList.add("btn", "btn-sm", "btn-outline-danger");
            deleteButton.innerHTML = '<i class="fas fa-trash"></i>';
            // Hide delete button for kid users
            if (window.isKid) {
                deleteButton.style.display = 'none';
            }
            deleteButton.dataset.listId = item.id;

            deleteButton.addEventListener("click", function () {
                confirmAndDeleteItem(item.id)
            });

            // Append elements in correct order
            listItem.appendChild(nameDiv); // Name
            listItem.appendChild(deleteButton); // Delete Button

            listContainer.appendChild(listItem);
        })
    }

    // Fetch and update list items inside #listContainer
    function updatePlanMembers(plan) { 
        // Update the list of members inside the correct #planMembersList div
        const membersList = document.getElementById("planMembersList"); // Target correct div
        if (membersList) {
            membersList.innerHTML = ""; // Clear previous members
            if (!plan.members || plan.members.length === 0) {
                membersList.innerHTML = "<p class='text-muted'>Nėra narių.</p>";
            } else {
                plan.members.forEach(member => {
                    const itemElement = document.createElement("li");
                    itemElement.classList.add("list-group-item", "d-flex", "justify-content-between", "align-items-center");

                    // Create a wrapper div for the left content (Name)
                    const leftContent = document.createElement("div");
                    leftContent.classList.add("d-flex", "align-items-center");
                    leftContent.textContent = member.name; // Correctly add text instead of appending directly

                    // Create delete button
                    const deleteButton = document.createElement("button");
                    deleteButton.classList.add("btn", "btn-sm", "btn-outline-danger");
                    deleteButton.innerHTML = '<i class="fas fa-trash"></i>';
                    // Hide delete button for kid users
                    if (window.isKid) {
                        deleteButton.style.display = 'none';
                    }
                    deleteButton.dataset.memberId = member.id; // Store member ID in dataset

                    deleteButton.addEventListener("click", function () {
                        confirmAndDeleteMember(member.id, plan.id)
                        //removePlanMember(plan.id, member.id); // Use correct member ID
                    });

                    // Append elements in correct order
                    itemElement.appendChild(leftContent); // Left: Name
                    itemElement.appendChild(deleteButton); // Right: Delete Button

                    membersList.appendChild(itemElement);
                });
            }
        }
    }

    function confirmAndDeleteItem(itemId) {
        if (confirm("Ar tikrai norite tai ištrinti?")) {
            fetch("../list/api/item/", {
                method: "DELETE",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken // Include CSRF token for security
                },
                body: JSON.stringify({
                    item_id: itemId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    fetchPlanList(); // Reload the list after deletion
                } else {
                    console.log("Error: " + data.error);
                }
            })
            .catch(error => console.error("Error deleting list:", error));
        }
    }

    function confirmAndDeleteMember(memberId, planId) {
        if (confirm("Ar tikrai norite tai ištrinti?")) {
            fetch("../plan/api/member/", {
                method: "DELETE",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken // Include CSRF token for security
                },
                body: JSON.stringify({
                    member_id: memberId,
                    plan_id: planId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    fetchPlanList(); // Reload the list after deletion
                } else {
                    console.log("Error: " + data.error);
                }
            })
            .catch(error => console.error("Error deleting list:", error));
        }
    }

    function formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        if (isNaN(date)) return dateString;
        
        const options = { 
            year: 'numeric', 
            month: '2-digit', 
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        };
        return date.toLocaleString('lt-LT', options)
            .replace(',', '')
            .replace(/\./g, '-');
    }

    fetchPlanList(); // Populate plans on page load
});
