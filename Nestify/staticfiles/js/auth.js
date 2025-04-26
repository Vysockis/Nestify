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

    // Password validation messages
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
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