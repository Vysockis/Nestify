document.addEventListener("DOMContentLoaded", function () {
    const modalOverlay = document.getElementById("modalOverlay");
    const modalForm = document.getElementById("modalForm");
    const closeModal = document.getElementById("closeModal");
    const formElement = document.getElementById("modalFormContent");
    const modalTitle = document.getElementById("modalTitle");
    const modalInputs = document.getElementById("modalInputs");

    let resolvePromise = null;

    function openModal({ title, fields }) {
        return new Promise((resolve, reject) => {
            resolvePromise = resolve;  // Store the resolve function

            modalTitle.textContent = title;
            modalInputs.innerHTML = ""; // Clear previous inputs

            fields.forEach(field => {
                let inputLabel = null;
                // Create a label if the field has a label defined
                if (field.label) {
                    inputLabel = document.createElement("label");
                    inputLabel.textContent = field.label;
                    inputLabel.setAttribute("for", field.id);
                    modalInputs.appendChild(inputLabel);
                }

                let inputElement;

                // Handle Dropdown Fields (select)
                if (field.type === "select") {
                    inputElement = document.createElement("select");
                    inputElement.id = field.id;
                    inputElement.required = field.required || false;
                    inputElement.classList.add("form-control");

                    // Add dropdown options
                    field.options.forEach(option => {
                        const optionElement = document.createElement("option");
                        optionElement.value = option.value;
                        optionElement.textContent = option.label;
                        inputElement.appendChild(optionElement);
                    });

                // Handle Image Fields - use file input for images
                } else if (field.type === "image") {
                    inputElement = document.createElement("input");
                    inputElement.id = field.id;
                    inputElement.type = "file";
                    inputElement.required = field.required || false;
                    inputElement.classList.add("form-control");
                    // Optionally limit to image files
                    inputElement.accept = "image/*";

                // Handle other input types (text, textarea, number, datetime-local, etc.)
                } else {
                    inputElement = document.createElement(field.type === "textarea" ? "textarea" : "input");
                    inputElement.id = field.id;
                    inputElement.placeholder = field.placeholder || "";
                    inputElement.required = field.required || false;
                    inputElement.classList.add("form-control");

                    if (field.type !== "textarea") {
                        inputElement.type = field.type;
                    }

                    // Set default value for datetime-local fields if needed
                    if (field.type === "datetime-local" && field.today) {
                        inputElement.value = getCurrentDateTime();
                    }

                    // If there's a default value provided, set it
                    if (field.value) {
                        inputElement.value = field.value;
                    }
                }

                // If field.visible is explicitly false, hide the label and input
                if (field.visible === false) {
                    if (inputLabel) {
                        inputLabel.style.display = "none";
                    }
                    inputElement.style.display = "none";
                }

                modalInputs.appendChild(inputElement);
            });

            modalOverlay.style.display = "block";
            modalForm.style.display = "block";
        });
    }

    function closeModalFunction() {
        modalOverlay.style.display = "none";
        modalForm.style.display = "none";
        formElement.reset();

        if (resolvePromise) {
            resolvePromise(null);  // Resolve with null if closed
            resolvePromise = null;
        }
    }

    closeModal.addEventListener("click", closeModalFunction);
    modalOverlay.addEventListener("click", closeModalFunction);

    formElement.addEventListener("submit", function (event) {
        event.preventDefault();

        const formData = {};

        // Process all input, textarea, and select elements
        modalInputs.querySelectorAll("input, textarea, select").forEach(input => {
            let value;

            // Handle checkboxes properly
            if (input.type === "checkbox") {
                value = input.checked ? 1 : 0; // Convert checkbox to boolean (1/0)
            
            // Handle datetime-local conversion to Unix timestamp
            } else if (input.type === "datetime-local" && input.value) {
                value = Math.floor(new Date(input.value).getTime() / 1000); // Convert to Unix timestamp (seconds)
            
            // Handle file inputs separately
            } else if (input.type === "file") {
                // For file inputs, you might want to handle file uploading via FormData instead of JSON.
                // For now, we'll just assign the file object if selected.
                value = input.files[0] || null;
            
            // Process normal text, number, and select fields
            } else {
                value = input.value;
            }

            formData[input.id] = value; // Store processed value
        });

        if (resolvePromise) {
            resolvePromise(formData); // Resolve with processed form data
            resolvePromise = null;
        }

        closeModalFunction();
    });

    function getCurrentDateTime() {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, "0");
        const day = String(now.getDate()).padStart(2, "0");
        const hours = String(now.getHours()).padStart(2, "0");
        const minutes = String(now.getMinutes()).padStart(2, "0");

        return `${year}-${month}-${day}T${hours}:${minutes}`;
    }

    window.openModal = openModal; // Expose openModal globally
});
