document.addEventListener("DOMContentLoaded", function () {
    const planContainer = document.getElementById("planContainer"); // Plan list container
    const planDisplay = document.getElementById("list"); // Main plan display container
    const addPlanMemberBtn = document.getElementById("addPlanMemberBtn");
    const addPlanBtn = document.getElementById("addPlanBtn");

    let plansData = []; // Global storage for fetched plans

    // Event listener for adding a member to a plan
    addPlanMemberBtn.addEventListener("click", function () {
        const planId = addPlanMemberBtn.dataset.planId;
        if (!planId) {
            console.error("No plan ID found.");
            return;
        }
        // Open modal to add a new plan member (replace with actual modal function)
        // openAddPlanMemberModal(planId);
    });

    addPlanBtn.addEventListener("click", function () {
        openAddPlanModal();
    });

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
    

    // Fetch list of plans from the API
    function fetchPlanList() {
        fetch("api/plans/")  // Adjust this Django API URL as needed
            .then(response => response.json())
            .then(data => {
                planContainer.innerHTML = ""; // Clear existing content
    
                if (data.plan_list.length === 0) {
                    planContainer.innerHTML = "<p>Nėra planų.</p>";
                    return;
                }
    
                plansData = data.plan_list; // Save plans for later reference
    
                // Get planId from URL
                const urlParams = new URLSearchParams(window.location.search);
                const urlPlanId = urlParams.get("planId"); // Get planId from URL query params
    
                let foundPlan = null;
    
                data.plan_list.forEach((plan) => {
                    const listElement = document.createElement("li");
                    listElement.classList.add(
                        "list-group-item",
                        "d-flex",
                        "justify-content-between",
                        "align-items-center",
                        "toggle-plan"
                    );
                    listElement.setAttribute("data-toggle", `plan-${plan.id}`);
                    listElement.textContent = plan.name;
    
                    planContainer.appendChild(listElement);
    
                    // Check if this plan is the one from the URL
                    if (urlPlanId && plan.id.toString() === urlPlanId) {
                        foundPlan = plan;
                        listElement.classList.add("active"); // Mark as active
                    }
                });
    
                addToggleFunctionality(); // Attach click events to list items
    
                // If a valid planId was found, update the display accordingly
                if (foundPlan) {
                    updatePlanDisplay(foundPlan);
                } else {
                    // Set the first plan as active by default (if no URL param exists)
                    const firstItem = planContainer.querySelector(".toggle-plan");
                    if (firstItem) {
                        firstItem.classList.add("active");
                        updatePlanDisplay(plansData[0]);
                    }
                }
            })
            .catch(error => console.error("Klaida gaunant planus:", error));
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
        if (!planDisplay) return;
        if (!plan) return; // Guard against undefined plans

        // Update background image of the plan image container
        const imageDiv = planDisplay.querySelector(".plans-image-content");
        if (imageDiv && plan.image) {
            imageDiv.style.backgroundImage = `url('${plan.image}')`;
        }

        // Update the plan name shown on the image
        const nameEl = planDisplay.querySelector(".plans-image-text");
        if (nameEl) {
            nameEl.textContent = `${plan.name} ${plan.date}`;
        }

        // Update the plan description
        const descriptionEl = planDisplay.querySelector("p");
        if (descriptionEl) {
            descriptionEl.innerHTML = plan.description.replace(/\n/g, "<br>");
        }

        // Update the list of members inside the correct #planMembersList div
        updatePlanMembers(plan);

        // Update the list items inside #listContainer
        updateListItems(plan);


        // Set the data attribute on the addPlanMemberBtn to the current plan ID
        if (addPlanMemberBtn) {
            addPlanMemberBtn.dataset.planId = plan.id;
        }
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

        plan.listitems.forEach(list => {
            const listItem = document.createElement("li");
            listItem.classList.add("list-group-item", "d-flex", "justify-content-between", "align-items-center");

            // Create wrapper div for name
            const nameDiv = document.createElement("div");
            nameDiv.textContent = list.name;

            // Create delete button
            const deleteButton = document.createElement("button");
            deleteButton.classList.add("circle-btn", "red");
            deleteButton.innerHTML = "&times;";
            deleteButton.dataset.listId = list.id;

            deleteButton.addEventListener("click", function () {
                console.log("Remove")
                //removeListItem(list.id);
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
                    deleteButton.classList.add("circle-btn", "red");
                    deleteButton.innerHTML = "&times;";
                    deleteButton.dataset.memberId = member.id; // Store member ID in dataset

                    deleteButton.addEventListener("click", function () {
                        console.log("Removed")
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

    fetchPlanList(); // Populate plans on page load
});
