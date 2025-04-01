                    listElement.setAttribute("data-toggle", `list-${recipe.id}`);
                    
                    // Create text container for name
                    const textContainer = document.createElement("div");
                    textContainer.classList.add("plan-text-container");
                    
                    // Create name span
                    const nameSpan = document.createElement("div");
                    nameSpan.classList.add("plan-name");
                    nameSpan.textContent = recipe.name;
                    
                    // Append name to container
                    textContainer.appendChild(nameSpan);
                    listElement.appendChild(textContainer);
                    
                    // Create delete button 