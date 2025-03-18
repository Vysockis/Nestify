// Global variables
let modalForm;
let closeModalBtn;
let formElement;
let modalTitle;
let modalInputs;
let resolvePromise = null;
let bootstrapModal = null;

function getCurrentDateTime() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");
    const hours = String(now.getHours()).padStart(2, "0");
    const minutes = String(now.getMinutes()).padStart(2, "0");

    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

// Define openModal globally
window.openModal = function({ title, fields }) {
    return new Promise((resolve, reject) => {
        if (!modalForm || !modalTitle || !modalInputs || !bootstrapModal) {
            console.error("Modal elements not found");
            reject(new Error("Modal elements not found"));
            return;
        }

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
                inputLabel.classList.add("form-label");
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
            } else if (field.type === "image") {
                inputElement = document.createElement("input");
                inputElement.id = field.id;
                inputElement.type = "file";
                inputElement.required = field.required || false;
                inputElement.classList.add("form-control");
                // Optionally limit to image files
                inputElement.accept = "image/*";
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

        bootstrapModal.show();
    });
};

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", function () {
    // Initialize DOM elements
    modalForm = document.getElementById("modalForm");
    closeModalBtn = document.getElementById("closeModal");
    formElement = document.getElementById("modalFormContent");
    modalTitle = document.getElementById("modalTitle");
    modalInputs = document.getElementById("modalInputs");

    // Initialize Bootstrap modal
    if (modalForm) {
        bootstrapModal = new bootstrap.Modal(modalForm, {
            backdrop: 'static',  // Prevent closing when clicking outside
            keyboard: false     // Prevent closing with keyboard
        });

        // Handle modal close events
        modalForm.addEventListener('hidden.bs.modal', function () {
            formElement.reset();
            if (resolvePromise) {
                resolvePromise(null);  // Resolve with null if closed
                resolvePromise = null;
            }
        });
    }

    if (formElement) {
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

            bootstrapModal.hide();
        });
    }
});
