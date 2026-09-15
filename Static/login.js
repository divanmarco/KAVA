const form = document.querySelector("#form");
const outputSection = document.querySelector("outputSection")

const REGEX_MAJ = /[A-Z]/g;
const REGEX_MIN = /[a-z]/g;
const REGEX_NUM = /[0-9]/g;
const REGEX_LEN = /^.{8,}$/;

function hasMaj(text) {
    return !text ? false : REGEX_MAJ.test(text);
}
function hasMin(text) {
    return !text ? false : REGEX_MIN.test(text);
}
function hasNum(text) {
    return !text ? false : REGEX_NUM.test(text);
}
function haslenth(text) {
    return !text ? false : REGEX_LEN.test(text);
}


form.addEventListener("submit", (event) => {
    clearOutputSection();

    const inputs = form.elements;
    let allFieldsFilled = true;
    let invalidlogin = false;
    let invalidPassword = false;

    for (let input of inputs) {
        if (input.hasAttribute('required')) {
            if (input.value.trim() === '') {
                allFieldsFilled = false;
                input.classList.add('invalid');
            } else {
                input.classList.remove('invalid')
            }

        }

    }
    let login = inputs['login'].value
    let password = inputs['password'].value

    if (login.trim() !== '' && login.trim().length < 3) {
        invalidLogin = true;
    }

    if (password.trim() !== '') {
        if (!hasMaj(password) || !hasMin(password) || !hasNum(password) || !hasLength(password)) {
            invalidPassword = true;
        }
    }

    if (!allFieldsFilled) {
        pushToOutputSection('Veuillez remplir tous les champs obligatoire.');
    }
    if (invalidlogin) {
        pushToOutputSection('Veuillez entrer un login valide')
    }
    if (invalidPassword) {
        pushToOutputSection(
            'Le mot de passe doit au moins contenir 8 caractères'
        )
    }

    if (!allFieldsFilled || invalidlogin || invalidPassword) {
        event.preventDefault()
    }
});

function clearOutputSection() {
    outputSection.innerHTML = ''
}

function pushToOutputSection(message) {
    const p = document.createElement('p');
    p.textContent = message;
    outputSection.appendChild(p);
}

//quand on veuet vérifier la validation in teste toujours l'iinvalidité