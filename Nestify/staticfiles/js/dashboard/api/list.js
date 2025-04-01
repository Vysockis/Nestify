document.addEventListener("DOMContentLoaded", function () {
    const listContainer = document.getElementById("listContainer");
    const listAdd = document.getElementById("addListBtn");

    listAdd.addEventListener("click", async function () {
        fields = [
            { id: "name", label: "Pavadinimas", type: "text", placeholder: "Įveskite pavadinimą", required: true },
            { 
                id: "list_type", label: "Tipas", type: "select", required: true, 
                options: [
                    { value: "GROCERY", label: "Pirkinių sąrašas" },
                    { value: "TASK", label: "Namų ruoša" }
                ] 
            },
            { id: "datetime", label: "Data ir laikas", type: "datetime-local", required: true, today: true }
        ]  
        const formData = await openModal({
            title: `Pridėti įrašą`,
            fields: fields
        });

        if (formData) {
            fetch("../list/api/list/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({...formData })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    fetchFamilyList(); // Update list dynamically
                } else {
                    alert("Klaida: " + JSON.stringify(data.error));
                }
            })
            .catch(error => console.error("Klaida pridedant įrašą:", error));
        }
    });

    // Fetch family list from the API
    function fetchFamilyList() {
        fetch("../list/api/family-list/")  // Django API URL
            .then(response => response.json())
            .then(data => {
                listContainer.innerHTML = "";  // Clear existing content

                if (data.family_list.length === 0) {
                    listContainer.innerHTML = "<p>No lists found.</p>";
                    return;
                }

                data.family_list.forEach((list, index) => {
                    if (list.type == "MEAL" || list.type == "OTHER" || list.type == "FINANCE") {
                        return
                    }
                    const listElement = document.createElement("li");
                    listElement.classList.add("list-group-item", "d-flex", "justify-content-between", "align-items-center", "toggle-list");
                    listElement.setAttribute("data-toggle", `list-${list.id}`);

                    const actionButton = document.createElement("button");
                    actionButton.classList.add("btn", "btn-sm", "btn-outline-danger");
                    actionButton.innerHTML = '<i class="fas fa-trash"></i>';
                    actionButton.dataset.type = "delete";
                    actionButton.addEventListener("click", function (event) {
                        event.stopPropagation(); // Prevent clicking the whole list
                        if (actionButton.dataset.type === "delete") {
                            confirmAndDeleteList(list.id);
                        } else {
                            confirmAndAddItem(list);
                        }
                    });

                    // Calculate completion status
                    const totalItems = list.items.length;
                    const completedItems = list.items.filter(item => item.completed).length;
                    
                    listElement.innerHTML = `
                        <div>
                            <span>${list.name}</span>
                            <span class="badge bg-secondary ms-2">${completedItems}/${totalItems}</span>
                        </div>
                        <span class="text-muted">${list.date}</span>
                    `;
                    listElement.appendChild(actionButton); // Append delete button

                    // Create nested <ul> for list items
                    const nestedList = document.createElement("ul");
                    nestedList.id = `list-${list.id}`;
                    nestedList.classList.add("nested-list");

                    list.items.forEach(item => {
                        const itemElement = document.createElement("li");
                        itemElement.classList.add("nested-item", "d-flex", "justify-content-between", "align-items-center");
                    
                        // Create a wrapper div for the left content (Completion + Text)
                        const leftContent = document.createElement("div");
                        leftContent.classList.add("d-flex", "align-items-center");
                    
                        // Create the completion button
                        const completionButton = document.createElement("span");
                        completionButton.classList.add("completion-button");
                        completionButton.textContent = item.completed ? "✅" : "⚪";
                        completionButton.style.cursor = "pointer";
                        completionButton.style.marginRight = "8px"; // Space between button and text
                    
                        // Toggle completed status on click
                        completionButton.addEventListener("click", function () {
                            item.completed = !item.completed;
                            completionButton.textContent = item.completed ? "✅" : "⚪";
                            
                            // Get the parent list element to update its badge
                            const listId = list.id;
                            const listElement = document.querySelector(`li[data-toggle="list-${listId}"]`);
                            
                            // Update the counter in the UI
                            const totalItems = list.items.length;
                            const completedItems = list.items.filter(i => 
                                i.id === item.id ? i.completed = item.completed : i.completed
                            ).length;
                            
                            // Update the badge text
                            const badgeElement = listElement.querySelector('.badge');
                            if (badgeElement) {
                                badgeElement.textContent = `${completedItems}/${totalItems}`;
                            }
                            
                            updateCompletionStatus(item.id, item.completed);
                        });
                    
                        // Create text container (Item name)
                        const textElement = document.createElement("span");
                        textElement.textContent = `${item.name}`;
                    
                        // Append Completion Button + Text inside leftContent
                        if (list.type == "GROCERY" || list.type == "TASK") {
                            leftContent.appendChild(completionButton);
                        }
                        leftContent.appendChild(textElement);
                    
                        // Create the delete button (Right)
                        const deleteButton = document.createElement("button");
                        deleteButton.classList.add("btn", "btn-sm", "btn-outline-danger");
                        deleteButton.innerHTML = '<i class="fas fa-trash"></i>';
                        deleteButton.addEventListener("click", function () {
                            confirmAndDeleteItem(item.id);
                        });
                    
                        // Append elements in correct order
                        itemElement.appendChild(leftContent); // Left: Completion + Text
                        itemElement.appendChild(deleteButton); // Right: Delete Button
                    
                        nestedList.appendChild(itemElement);
                    });
                    

                    listContainer.appendChild(listElement);
                    listContainer.appendChild(nestedList);
                });

                addToggleFunctionality(); // Attach click event to newly created elements
            })
            .catch(error => console.error("Error fetching lists:", error));
    }

    // Function to toggle nested lists
    function addToggleFunctionality() {
        const listItems = document.querySelectorAll(".toggle-list");

        listItems.forEach(item => {
            item.addEventListener("click", function () {
                const targetId = this.getAttribute("data-toggle");
                const nestedList = document.getElementById(targetId);
                const actionButton = this.querySelector(".btn"); // Find the button inside the clicked `<li>`

                if (nestedList) {
                    nestedList.classList.toggle("active");
                }

                if (actionButton) {
                    if (actionButton.dataset.type === "delete") {
                        actionButton.innerHTML = '<i class="fas fa-plus"></i>'; // Change to add button
                        actionButton.classList.remove("btn-outline-danger");
                        actionButton.classList.add("btn-outline-success");
                        actionButton.dataset.type = "add";
                    } else {
                        actionButton.innerHTML = '<i class="fas fa-trash"></i>'; // Change back to delete button
                        actionButton.classList.remove("btn-outline-success");
                        actionButton.classList.add("btn-outline-danger");
                        actionButton.dataset.type = "delete";
                    }
                }
            });
        });
    }

      // API Call to Update Completed Status
    function updateCompletionStatus(itemId, completed) {
        fetch("../list/api/update-item-status/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken // Ensure CSRF token is included
            },
            body: JSON.stringify({
                item_id: itemId,
                completed: completed
            })
        })
        .then(response => response.json())
        .then(data => console.log("Updated successfully:", data))
        .catch(error => console.error("Error updating item:", error));
    }

    function confirmAndDeleteList(listId) {
        if (confirm("Ar tikrai norite tai ištrinti?")) {
            fetch("../list/api/list/", {
                method: "DELETE",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({
                    list_id: listId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    fetchFamilyList();
                } else {
                    console.log("Error: " + data.error);
                }
            })
            .catch(error => console.error("Error deleting list:", error));
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
                    fetchFamilyList(); // Reload the list after deletion
                } else {
                    console.log("Error: " + data.error);
                }
            })
            .catch(error => console.error("Error deleting list:", error));
        }
    }

    async function confirmAndAddItem(list) {
        fields = []
        switch (list.type) {
            case "MEAL":
            case "GROCERY":
                fields = [
                    { id: "name", label: "Pavadinimas", type: "text", placeholder: "Įveskite pavadinimą", required: true },
                    { id: "qty", label: "Kiekis", type: "number", placeholder: "Įveskite kiekį", required: true, min: 1, value: 1}
                ]
                break;
            case "TASK":
                let memberOption = [];
                console.log(family_members)
                family_members.forEach(element => {
                    memberOption.push({
                        value: element.id,
                        label: element.name
                    });
                });

                fields = [
                    { id: "name", label: "Pavadinimas", type: "text", placeholder: "Įveskite pavadinimą", required: true },
                    { 
                        id: "assigned_to", label: "Atsakingas žmogus", type: "select", required: true, 
                        options: memberOption
                    }
                ];
                break;
            case "OTHER":  
                fields = [
                    { id: "name", label: "Pavadinimas", type: "text", placeholder: "Įveskite pavadinimą", required: true }
                ]  
                break;
        }

        const formData = await openModal({
            title: `Pridėti įrašą prie ${list.name}`,
            fields: fields
        });

        if (formData) {
            fetch("../list/api/item/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({ list_id: list.id, ...formData })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    fetchFamilyList(); // Update list dynamically
                } else {
                    alert("Klaida: " + JSON.stringify(data.error));
                }
            })
            .catch(error => console.error("Klaida pridedant įrašą:", error));
        }
    }

    fetchFamilyList(); // Initial API call to populate data
});
