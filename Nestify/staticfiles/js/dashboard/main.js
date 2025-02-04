document.addEventListener("DOMContentLoaded", function () {
    // Select all mini boxes
    const miniBoxes = document.querySelectorAll(".dashboard-box");

    miniBoxes.forEach(box => {
        box.addEventListener("click", function () {
            const selectedId = this.getAttribute("id"); // Get the clicked box ID
            // Remove 'selected' class from any currently selected box
            document.querySelectorAll(".dashboard-box.selected").forEach(selectedBox => {
                selectedBox.classList.remove("selected");
            });

            document.querySelectorAll(".main-box.selected").forEach(selectedBox => {
                selectedBox.classList.remove("selected");
            });

            // Add 'selected' class to the clicked box
            this.classList.add("selected");

            const matchingMainBox = document.querySelector(`.main-box[id="${selectedId}"]`);
            if (matchingMainBox) {
                matchingMainBox.classList.add("selected");
            }
        });
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const addButton = document.querySelector(".circle-btn"); // Add button
    const modal = document.getElementById("modalForm");
    const overlay = document.getElementById("modalOverlay");
    const closeModal = document.getElementById("closeModal");

    // Show Modal when "Add" button is clicked
    addButton.addEventListener("click", function () {
        modal.style.display = "block";
        overlay.style.display = "block";
    });

    // Hide Modal when "X" is clicked
    closeModal.addEventListener("click", function () {
        modal.style.display = "none";
        overlay.style.display = "none";
    });

    // Hide Modal when clicking outside it
    overlay.addEventListener("click", function () {
        modal.style.display = "none";
        overlay.style.display = "none";
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const listItems = document.querySelectorAll(".toggle-list");

    listItems.forEach(item => {
        item.addEventListener("click", function () {
            const targetId = this.getAttribute("data-toggle");
            const nestedList = document.getElementById(targetId);

            if (nestedList) {
                // Toggle active class
                if (nestedList.classList.contains("active")) {
                    nestedList.style.maxHeight = "0px"; // Collapse smoothly
                    setTimeout(() => nestedList.classList.remove("active"), 300);
                } else {
                    nestedList.classList.add("active");
                    nestedList.style.maxHeight = nestedList.scrollHeight + "px"; // Expand smoothly
                }
            }
        });
    });
});
