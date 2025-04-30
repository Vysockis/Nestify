document.addEventListener("DOMContentLoaded", function () {
    const listContainer = document.getElementById("listContainer");
    const recipeDisplay = document.getElementById("recipeDetails"); // Main recipe display container
    const addListItemBtn = document.getElementById("addListItemBtn");
    const editListBtn = document.getElementById("editListBtn");
    const addListBtn = document.getElementById("addListBtn");

    let recipesData = []; // Global storage for fetched recipes

    // Get list_id from URL parameters
    function getListIdFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get("list_id"); // Ensure correct parameter name
    }

    editListBtn.addEventListener("click", function () {
        const recipeId = editListBtn.dataset.listId;
        if (!recipeId) {
            console.error("No recipe found.");
            return;
        }
        const recipe = recipesData.find(r => r.id.toString() === recipeId);
        if (!recipe) {
            console.error("Recipe not found in data.");
            return;
        }
        openEditRecipeModal(recipe);
    });

    addListItemBtn.addEventListener("click", function () {
        const listId = addListItemBtn.dataset.listId;
        if (!listId) {
            console.error("No list id found.");
            return;
        }
        openAddListItemModal(listId);
    });

    addListBtn.addEventListener("click", function () {
        openAddListModal();
    });

    async function openAddListModal() {
        const fields = [
            { id: "name", label: "Pavadinimas", type: "text", placeholder: "Įveskite pavadinimą", required: true },
            { id: "description", label: "Aprašymas", type: "textarea", placeholder: "Aprašymas...", required: false },
            { id: "list_type", type: "hidden", required: true, value: "MEAL", visible: false },
            { id: "image", label: "Nuotrauka", type: "image", required: false },
            { id: "datetime", label: "Data ir laikas", type: "datetime-local", required: true, today: true, visible: false }
        ];
        
        const formData = await openModal({
            title: `Pridėti įrašą`,
            fields: fields
        });

        if (formData) {
            const fd = new FormData();
            for (const key in formData) {
                fd.append(key, formData[key]);
            }
            
            fetch("../api/list/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: fd
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const newListId = data.list_id; // Get new list ID from response
                    if (newListId) {
                        const newUrl = new URL(window.location.href);
                        newUrl.searchParams.set("list_id", newListId);
                        window.history.pushState({}, "", newUrl); // Update URL without reloading
                    }
                    fetchFamilyList(); // Update list dynamically
                } else {
                    alert("Klaida: " + JSON.stringify(data.error));
                }
            })
            .catch(error => console.error("Klaida pridedant įrašą:", error));
        }
    }

    async function openAddListItemModal(listId) {
        const fields = [
            { id: "name", label: "Pavadinimas", type: "text", placeholder: "Įveskite pavadinimą", required: true },
            { id: "qty", label: "Kiekis", type: "number", placeholder: "Įveskite kiekį", required: true, min: 1, value: 1 }
        ];

        const formData = await openModal({
            title: `Pridėti įrašą`,
            fields: fields
        });

        if (formData) {
            fetch("../api/item/", {
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
                    fetchFamilyList(); // Update list dynamically
                } else {
                    alert("Klaida: " + JSON.stringify(data.error));
                }
            })
            .catch(error => console.error("Klaida pridedant įrašą:", error));
        }
    }

    async function openEditRecipeModal(recipe) {
        const fields = [
            { id: "name", label: "Pavadinimas", type: "text", placeholder: "Įveskite pavadinimą", required: true, value: recipe.name, visible: false },
            { id: "description", label: "Aprašymas", type: "textarea", placeholder: "Aprašymas...", required: false, value: recipe.description },
            { id: "list_type", type: "hidden", required: true, value: "MEAL", visible: false },
            { id: "image", label: "Nuotrauka", type: "image", required: false },
            { id: "datetime", label: "Data ir laikas", type: "datetime-local", required: true, today: true, visible: false }
        ];
        
        const formData = await openModal({
            title: `Redaguoti receptą`,
            fields: fields
        });

        if (formData) {
            const fd = new FormData();
            for (const key in formData) {
                fd.append(key, formData[key]);
            }
            
            fetch("../api/list/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: fd
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    fetchFamilyList(); // Update list dynamically
                } else {
                    alert("Klaida: " + JSON.stringify(data.error));
                }
            })
            .catch(error => console.error("Klaida atnaujinant receptą:", error));
        }
    }

    function fetchFamilyList() {
        fetch("../api/recipes/")
            .then(response => response.json())
            .then(data => {
                if (!data || !data.recipe_list) {
                    console.error("Invalid data received from API");
                    return;
                }

                recipesData = data.recipe_list;
                listContainer.innerHTML = ""; // Clear existing content

                if (recipesData.length === 0) {
                    listContainer.innerHTML = "<p>Nėra receptų.</p>";
                    return;
                }

                const urlListId = getListIdFromURL();
                let foundList = false;

                recipesData.forEach((recipe) => {
                    const listElement = document.createElement("li");
                    listElement.classList.add(
                        "list-group-item",
                        "d-flex",
                        "justify-content-between",
                        "align-items-center",
                        "toggle-list"
                    );
                    listElement.setAttribute("data-toggle", `list-${recipe.id}`);
                    
                    // Create text span for recipe name
                    const nameSpan = document.createElement("span");
                    nameSpan.textContent = recipe.name;
                    listElement.appendChild(nameSpan);
                    
                    // Create delete button
                    const deleteBtn = document.createElement("button");
                    deleteBtn.classList.add("btn", "btn-sm", "btn-outline-danger");
                    deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
                    // Hide delete button for kid users
                    if (window.isKid) {
                        deleteBtn.style.display = 'none';
                    }
                    deleteBtn.addEventListener("click", function(event) {
                        event.stopPropagation();
                        if (confirm("Ar tikrai norite ištrinti šį receptą?")) {
                            fetch("../api/list/", {
                                method: "DELETE",
                                headers: {
                                    "Content-Type": "application/json",
                                    "X-CSRFToken": csrfToken
                                },
                                body: JSON.stringify({ list_id: recipe.id })
                            })
                            .then(response => response.json())
                            .then(data => {
                                if (data.success) {
                                    fetchFamilyList();
                                } else {
                                    alert("Klaida: " + JSON.stringify(data.error));
                                }
                            })
                            .catch(error => console.error("Klaida trinant receptą:", error));
                        }
                    });
                    
                    listElement.appendChild(deleteBtn);
                    listContainer.appendChild(listElement);

                    // Add click event to show recipe details
                    listElement.addEventListener("click", function(event) {
                        event.preventDefault();
                        event.stopPropagation();
                        
                        // Remove active class from all items
                        document.querySelectorAll('.toggle-list').forEach(item => {
                            item.classList.remove('active');
                        });
                        
                        // Add active class to clicked item
                        this.classList.add('active');
                        
                        // Update URL without reloading
                        const newUrl = new URL(window.location.href);
                        newUrl.searchParams.set("list_id", recipe.id);
                        window.history.pushState({}, "", newUrl);
                        
                        // Update recipe display
                        updateRecipeDisplay(recipe);
                    });
    
                    // Check if this list should be active based on URL
                    if (urlListId && recipe.id.toString() === urlListId) {
                        listElement.classList.add("active");
                        updateRecipeDisplay(recipe);
                        foundList = true;
                    }
                });

                if (!foundList && recipesData.length > 0) {
                    const firstItem = listContainer.querySelector(".toggle-list");
                    if (firstItem) {
                        firstItem.classList.add("active");
                        updateRecipeDisplay(recipesData[0]);
                    }
                }
            })
            .catch(error => console.error("Error fetching lists:", error));
    }

    function updateRecipeDisplay(recipe) {
        if (!recipeDisplay) return;
        if (!recipe) return;

        const imageDiv = recipeDisplay.querySelector(".recipes-image-content");
        if (imageDiv && recipe.image) {
            imageDiv.style.backgroundImage = `url('${recipe.image}')`;
        }

        const nameEl = recipeDisplay.querySelector(".recipe-image-text");
        if (nameEl) {
            nameEl.textContent = recipe.name;
        }

        const descriptionEl = recipeDisplay.querySelector("p");
        if (descriptionEl) {
            descriptionEl.innerHTML = recipe.description.replace(/\n/g, "<br>");
        }

        const ingredientsList = document.getElementById("ingredientsList");
        if (ingredientsList) {
            ingredientsList.innerHTML = "";
            recipe.items.forEach(item => {
                const li = document.createElement("li");
                li.className = "list-group-item d-flex justify-content-between align-items-center";
                li.setAttribute("data-item-id", item.id);
                
                // Create text content
                const textSpan = document.createElement("span");
                textSpan.textContent = item.qty && item.qty != 1 ? `${item.qty}x ${item.name}` : item.name;
                
                li.appendChild(textSpan);
                
                // Create delete button
                const deleteBtn = document.createElement("button");
                deleteBtn.classList.add("btn", "btn-sm", "btn-outline-danger");
                deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
                // Hide delete button for kid users
                if (window.isKid) {
                    deleteBtn.style.display = 'none';
                }
                deleteBtn.addEventListener("click", function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    if (confirm("Ar tikrai norite ištrinti šį ingredientą?")) {
                        const itemId = this.closest('li').getAttribute('data-item-id');
                        fetch("../api/item/", {
                            method: "DELETE",
                            headers: {
                                "Content-Type": "application/json",
                                "X-CSRFToken": csrfToken
                            },
                            body: JSON.stringify({ item_id: itemId })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                // Remove only this item from the list
                                this.closest('li').remove();
                            } else {
                                alert("Klaida: " + JSON.stringify(data.error));
                            }
                        })
                        .catch(error => console.error("Klaida trinant ingredientą:", error));
                    }
                });
                
                li.appendChild(deleteBtn);
                ingredientsList.appendChild(li);
            });
        }

        if (addListItemBtn) {
            addListItemBtn.dataset.listId = recipe.id;
            editListBtn.dataset.listId = recipe.id;
        }
    }

    fetchFamilyList(); // Populate list on page load
});
