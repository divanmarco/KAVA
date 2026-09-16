// const form = document.querySelector("#auth");
// const outputSection = document.querySelector("#outputSection");

// const REGEX_EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
// const REGEX_NUM = /[0-9]/g;

// function isValidEmail(text) {
//     return !text ? false : REGEX_EMAIL.test(text);
// }
// function hasNum(text) {
//     return !text ? false : REGEX_NUM.test(text);
// }

// form.addEventListener("submit", (event) => {
//     clearOutputSection();

//     const inputs = form.elements;
//     let allFieldsFilled = true;
//     let invalidLogin = false;
//     let invalidPassword = false;

//     for (let input of inputs) {
//         if (input.hasAttribute('required')) {
//             if (input.value.trim() === '') {
//                 allFieldsFilled = false;
//                 input.classList.add('invalid');
//             } else {
//                 input.classList.remove('invalid');
//             }
//         }
//     }

//     let login = inputs['name'].value;
//     let password = inputs['password'].value;

//     if (login.trim() !== '' && login.trim().length < 3) {
//         invalidLogin = true;
//     }

//     if (password.trim() !== '') {
//         if (!isValidEmail(password) || !hasNum(password)) {
//             invalidPassword = true;
//         }
//     }

//     if (!allFieldsFilled) {
//         pushToOutputSection('Veuillez remplir tous les champs obligatoires.');
//     }
//     if (invalidLogin) {
//         pushToOutputSection('Veuillez entrer un login valide (3 caractères minimum).');
//     }
//     if (invalidPassword) {
//         pushToOutputSection('Le mot de passe doit être un email valide contenant au moins un chiffre.');
//     }

//     if (!allFieldsFilled || invalidLogin || invalidPassword) {
//         event.preventDefault();
//     }
// });

// function clearOutputSection() {
//     outputSection.innerHTML = '';
// }

// function pushToOutputSection(message) {
//     const p = document.createElement('p');
//     p.textContent = message;
//     outputSection.appendChild(p);
// }