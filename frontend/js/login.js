document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const usernameInput = document.getElementById('username').value;
    const passwordInput = document.getElementById('password').value;
    const errorMsg = document.getElementById('login-error');
    const loginBtn = document.getElementById('login-btn');

    // UI-Feedback
    loginBtn.disabled = true;
    loginBtn.innerText = "Wird angemeldet...";
    errorMsg.style.display = 'none';

    // Das JSON-Objekt laut deiner Doku
    const payload = {
        username: usernameInput,
        password: passwordInput
    };

    try {
        const response = await fetch('https://vsv-research.volkmann-webservices.de/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json', // Wir senden JSON
                'Accept': 'application/json'
            },
            body: JSON.stringify(payload) // Umwandlung des Objekts in einen String
        });

        const data = await response.json();

        if (response.ok) {
            // Erfolg: Token speichern
            // data.access_token ist der Standardname, schau ggf. in die Response-Doku
            sessionStorage.setItem('camo_token', data.access_token);
            sessionStorage.setItem('camo_username', usernameInput);

            window.location.href = '/';
        } else {
            // Fehlerbehandlung
            errorMsg.innerText = data.detail || "Anmeldung fehlgeschlagen.";
            errorMsg.style.display = 'block';
        }
    } catch (error) {
        errorMsg.innerText = "Verbindung zum Auth-Server fehlgeschlagen.";
        errorMsg.style.display = 'block';
    } finally {
        loginBtn.disabled = false;
        loginBtn.innerText = "Anmelden";
    }
});