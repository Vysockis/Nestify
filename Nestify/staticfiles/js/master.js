document.addEventListener("DOMContentLoaded", async function () {
    try {
        const response = await fetch("/family/api/members/", {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken // Include CSRF token if needed
            }
        });

        if (!response.ok) {
            throw new Error(`Klaida: ${response.statusText}`);
        }

        const responseBody = await response.json();
        family_members = responseBody.family_members
    } catch (error) {
        console.error("Klaida gaunant šeimos narius:", error);
        family_members = []
    }

    try {
        const response = await fetch("/finance/api/categories/", {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken // Include CSRF token if needed
            }
        });

        if (!response.ok) {
            throw new Error(`Klaida: ${response.statusText}`);
        }

        const responseBody = await response.json();
        finance_categories = responseBody.finance_categories
    } catch (error) {
        console.error("Klaida gaunant kategorijas:", error);
        finance_categories = []
    }
});