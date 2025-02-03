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
