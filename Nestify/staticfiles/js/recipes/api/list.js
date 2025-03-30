document.addEventListener("DOMContentLoaded", function () {
    const listContainer = document.getElementById("listContainer");
    const recipeDisplay = document.getElementById("list"); // Main recipe display container
    const addListItemBtn = document.getElementById("addListItemBtn");
    const addListBtn = document.getElementById("addListBtn");

    let recipesData = []; // Global storage for fetched recipes

    // Get list_id from URL parameters
    function getListIdFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get("list_id"); // Ensure correct parameter name
    }

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
            { id: "quantity", label: "Kiekis", type: "number", placeholder: "Įveskite kiekį", required: true, min: 1, value: 1 }
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

    function fetchFamilyList() {
        fetch("../api/recipes/")
            .then(response => response.json())
            .then(data => {
                listContainer.innerHTML = ""; // Clear existing content
                if (data.recipe_list.length === 0) {
                    listContainer.innerHTML = "<p>No lists found.</p>";
                    return;
                }

                recipesData = data.recipe_list;

                const urlListId = getListIdFromURL(); // Get list_id from URL
                let foundList = false;

                data.recipe_list.forEach((recipe) => {
                    const listElement = document.createElement("li");
                    listElement.classList.add(
                        "list-group-item",
                        "d-flex",
                        "justify-content-between",
                        "align-items-center",
                        "toggle-list"
                    );
                    listElement.setAttribute("data-toggle", `list-${recipe.id}`);
                    listElement.textContent = recipe.name;
                    listContainer.appendChild(listElement);

                    // Check if this list should be active based on URL
                    if (urlListId && recipe.id.toString() === urlListId) {
                        listElement.classList.add("active");
                        updateRecipeDisplay(recipe);
                        foundList = true;
                    }

                    listElement.addEventListener("click", function () {
                        const newUrl = new URL(window.location.href);
                        newUrl.searchParams.set("list_id", recipe.id);
                        window.history.pushState({}, "", newUrl);
                        fetchFamilyList(); // Refresh to ensure active state updates
                    });
                });

                if (!foundList) {
                    // If no matching list_id was found, make the first item active
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

        const ingredientsList = recipeDisplay.querySelector("ul");
        if (ingredientsList) {
            ingredientsList.innerHTML = "";
            recipe.items.forEach(item => {
                const li = document.createElement("li");
                li.className = "list-group-item";
                li.textContent = item.qty && item.qty != 1 ? `${item.qty}x ${item.name}` : item.name;
                ingredientsList.appendChild(li);
            });
        }

        if (addListItemBtn) {
            addListItemBtn.dataset.listId = recipe.id;
        }
    }

    fetchFamilyList(); // Populate list on page load
});
