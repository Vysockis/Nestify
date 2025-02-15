document.addEventListener("DOMContentLoaded", function () {
    const listContainer = document.getElementById("listContainer");
    const listAdd = document.getElementById("addListBtn");
    const recipeDisplay = document.getElementById("list"); // Main recipe display container
    const addListItemBtn = document.getElementById("addListItemBtn");
    const addListBtn = document.getElementById("addListBtn");
  
    let recipesData = []; // Global storage for fetched recipes

    addListItemBtn.addEventListener("click", function () {
        // Retrieve the current list id from the button's data attribute
        const listId = addListItemBtn.dataset.listId;
        if (!listId) {
            console.error("No list id found.");
            return;
        }
        // Open the modal for adding a new list item, passing the listId if needed.
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
            // Create a new FormData instance
            const fd = new FormData();
            // Append all keys from formData to the FormData instance.
            for (const key in formData) {
                fd.append(key, formData[key]);
            }
            
            // Now send the FormData object without manually setting the Content-Type header.
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
            .catch(error => console.error("Klaida pridedant įrašą:", error));
        }
    }
     
    async function openAddListItemModal(listId) {
        fields = [
            { id: "name", label: "Pavadinimas", type: "text", placeholder: "Įveskite pavadinimą", required: true },
            { id: "qty", label: "Kiekis", type: "number", placeholder: "Įveskite kiekį", required: true, min: 1, value: 1}
        ]
        const formData = await openModal({
            title: `Pridėti įrašą prie ${list.name}`,
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

    // Fetch family list (recipes) from the API
    function fetchFamilyList() {
      fetch("../api/recipes/")  // Adjust this Django API URL as needed
        .then(response => response.json())
        .then(data => {
          listContainer.innerHTML = "";  // Clear existing content
  
          if (data.recipe_list.length === 0) {
            listContainer.innerHTML = "<p>No lists found.</p>";
            return;
          }
  
          recipesData = data.recipe_list; // Save recipes for later reference
  
          data.recipe_list.forEach((recipe) => {
            const listElement = document.createElement("li");
            listElement.classList.add(
              "list-group-item",
              "d-flex",
              "justify-content-between",
              "align-items-center",
              "toggle-list"
            );
            // Store the recipe id in a data attribute for later retrieval
            listElement.setAttribute("data-toggle", `list-${recipe.id}`);
            listElement.textContent = recipe.name;
            listContainer.appendChild(listElement);
          });
  
          addToggleFunctionality(); // Attach click events to list items
  
          // Make the first list item active by default
          const firstItem = listContainer.querySelector(".toggle-list");
          if (firstItem) {
            firstItem.classList.add("active");
          }
  
          // Optionally, load the first recipe by default
          updateRecipeDisplay(recipesData[0]);
        })
        .catch(error => console.error("Error fetching lists:", error));
    }
  
    // Attach click events to each list item so that clicking updates the main display
    function addToggleFunctionality() {
      const toggleListItems = document.querySelectorAll(".toggle-list");
      toggleListItems.forEach(item => {
        item.addEventListener("click", function () {
          // Remove active class from all list items
          toggleListItems.forEach(el => el.classList.remove("active"));
          // Add active class to the clicked element
          this.classList.add("active");
  
          // Extract the recipe id from the data attribute
          const recipeId = this.getAttribute("data-toggle").split("-")[1];
          // Find the corresponding recipe from our global recipesData
          const recipe = recipesData.find(r => r.id.toString() === recipeId);
          if (recipe) {
            updateRecipeDisplay(recipe);
          }
        });
      });
    }

    function updateRecipeDisplay(recipe) {
        if (!recipeDisplay) return;
        if (!recipe) return; // Guard against undefined recipes
    
        // Update background image of the recipe image container
        const imageDiv = recipeDisplay.querySelector(".recipes-image-content");
        if (imageDiv && recipe.image) {
            imageDiv.style.backgroundImage = `url('${recipe.image}')`;
        }
    
        // Update the recipe name shown on the image
        const nameEl = recipeDisplay.querySelector(".recipe-image-text");
        if (nameEl) {
            nameEl.textContent = recipe.name;
        }
    
        // Update the recipe description (assumes the first <p> is used for description)
        const descriptionEl = recipeDisplay.querySelector("p");
        if (descriptionEl) {
            const formattedDescription = recipe.description.replace(/\n/g, "<br>");
            descriptionEl.innerHTML = formattedDescription;
        }
    
        // Update the list of ingredients (assumes the <ul> exists for ingredients)
        const ingredientsList = recipeDisplay.querySelector("ul");
        if (ingredientsList) {
            ingredientsList.innerHTML = ""; // Clear previous ingredients
            recipe.items.forEach(item => {
                const li = document.createElement("li");
                li.className = "list-group-item";
                li.textContent = item.qty && item.qty != 1 ? `${item.qty}x ${item.name}` : item.name;
                ingredientsList.appendChild(li);
            });
        }
    
        // Set the data attribute on the addListItemBtn to the current recipe/list id
        if (addListItemBtn) {
            addListItemBtn.dataset.listId = recipe.id;
        }
    }    
  
    fetchFamilyList(); // Populate list on page load
});
