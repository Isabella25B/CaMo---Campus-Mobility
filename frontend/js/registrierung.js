document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const usernameInput = document.getElementById('reg-username').value;
    const passwordInput = document.getElementById('reg-password').value;
    const errorMsg = document.getElementById('register-error');
    const successMsg = document.getElementById('register-success');
    const registerBtn = document.getElementById('register-btn');

    // UI-Reset
    errorMsg.style.display = 'none';
    successMsg.style.display = 'none';
    registerBtn.disabled = true;
    registerBtn.innerText = "Wird erstellt...";

    const payload = {
        username: usernameInput,
        password: passwordInput
    };

    try {
        const response = await fetch('https://vsv-research.volkmann-webservices.de/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok) {
            // Erfolg
            successMsg.style.display = 'block';
            
            // Nach 2 Sekunden zum Login weiterleiten
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        } else {
            // Fehler vom Server (z.B. User existiert schon)
            errorMsg.innerText = data.detail || "Registrierung fehlgeschlagen.";
            errorMsg.style.display = 'block';
            registerBtn.disabled = false;
            registerBtn.innerText = "Konto erstellen";
        }
    } catch (error) {
        errorMsg.innerText = "Verbindung zum Server fehlgeschlagen.";
        errorMsg.style.display = 'block';
        registerBtn.disabled = false;
        registerBtn.innerText = "Konto erstellen";
    }
});