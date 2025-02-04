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
                const inputLabel = document.createElement("label");
                inputLabel.textContent = field.label;
                inputLabel.setAttribute("for", field.id);

                const inputElement = document.createElement(field.type === "textarea" ? "textarea" : "input");
                inputElement.id = field.id;
                inputElement.placeholder = field.placeholder;
                inputElement.required = field.required || false;
                inputElement.classList.add("form-control");

                if (field.type !== "textarea") {
                    inputElement.type = field.type;
                }

                if (field.value !== undefined) {
                    inputElement.value = field.value;
                }

                if (field.type === "datetime-local" && field.today) {
                    inputElement.value = field.value || getCurrentDateTime(); 
                }

                modalInputs.appendChild(inputLabel);
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
        modalInputs.querySelectorAll("input, textarea").forEach(input => {
            let value = input.value;

            // **Convert datetime-local to integer (Unix timestamp in seconds)**
            if (input.type === "datetime-local" && value) {
                value = new Date(value).getTime() / 1000; // Convert to Unix timestamp (seconds)
            }

            formData[input.id] = value;
        });

        if (resolvePromise) {
            resolvePromise(formData); // Resolve with form data
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
