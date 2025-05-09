document.addEventListener('DOMContentLoaded', function() {
    const joinFamilyBtn = document.querySelector('.join-family');
    const createFamilyBtn = document.querySelector('.create-family');

    if (joinFamilyBtn) {
        joinFamilyBtn.addEventListener('click', function() {
            alert('Prisijungimas prie šeimos bus įgyvendintas netrukus!');
        });
    }

    if (createFamilyBtn) {
        createFamilyBtn.addEventListener('click', function() {
            alert('Šeimos sukūrimas bus įgyvendintas netrukus!');
        });
    }

    // Password validation
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        input.addEventListener('input', function() {
            const password = this.value;
            const hasUpperCase = /[A-Z]/.test(password);
            const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);
            const isLongEnough = password.length >= 8;

            let errorMessage = '';
            if (!isLongEnough) {
                errorMessage = 'Slaptažodis turi būti bent 8 simbolių ilgio';
            } else if (!hasUpperCase) {
                errorMessage = 'Slaptažodis turi turėti bent vieną didžiąją raidę';
            } else if (!hasSpecialChar) {
                errorMessage = 'Slaptažodis turi turėti bent vieną specialų simbolį';
            }

            this.setCustomValidity(errorMessage);
        });

        input.addEventListener('invalid', function() {
            if (this.validity.valueMissing) {
                this.setCustomValidity('Slaptažodis yra privalomas');
            } else if (this.validity.tooShort) {
                this.setCustomValidity('Slaptažodis per trumpas');
            } else {
                this.setCustomValidity('');
            }
        });
    });
});