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
}); 