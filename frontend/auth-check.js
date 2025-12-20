/**
 * Zentrale Authentifizierungsprüfung für CaMo
 */
async function checkAuth() {
    const token = sessionStorage.getItem('camo_token');
    const pageContent = document.querySelector('.page-content');
    const headline = document.querySelector('.headline-title');

    // 1. Grundprüfung: Ist überhaupt ein Token da?
    if (!token) {
        showLoginMessage(headline, pageContent);
        return false;
    }

    try {
        // 2. Server-Prüfung: Ist das Token noch gültig?
        const response = await fetch(`https://vsv-research.volkmann-webservices.de/auth/verify?token=${token}`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });

        if (response.ok) {
            updateTopbar(); 
            return true; 
        } else {
            // Token abgelaufen oder manipuliert
            sessionStorage.clear();
            showLoginMessage(headline, pageContent, "Deine Sitzung ist abgelaufen. Bitte melde dich erneut an.");
            return false;
        }
    } catch (error) {
        console.error("Auth-Server Fehler:", error);
        // Fallback: Wenn der Auth-Server down ist, lassen wir den User 
        // basierend auf dem lokalen Token rein (optional)
        updateTopbar();
        return true; 
    }
}

function showLoginMessage(headline, pageContent, customMsg) {
    if (headline) headline.innerText = "Zugriff beschränkt";
    if (pageContent) {
        pageContent.innerHTML = `
            <div class="card" style="text-align: center; padding: 40px; margin-top: 20px;">
                <h2 style="color: var(--color-accent); margin-bottom: 10px;">🔒 Anmeldung erforderlich</h2>
                <p style="color: var(--color-muted);">${customMsg || "Logge dich ein, um deinen persönlichen Bereich zu sehen."}</p>
                <div style="margin-top: 25px;">
                    <a href="login.html" class="sign-in-button" style="text-decoration: none; padding: 10px 25px;">Jetzt zum Login</a>
                </div>
            </div>
        `;
    }
}

function updateTopbar() {
    const username = sessionStorage.getItem('camo_username');
    const authButton = document.querySelector('.sign-in-button');
    
    // Verhindere doppeltes Hinzufügen des Namens
    if (username && authButton && !document.querySelector('.user-welcome-msg')) {
        authButton.innerText = "Abmelden";
        authButton.onclick = (e) => {
            e.preventDefault();
            sessionStorage.clear();
            window.location.href = 'login.html';
        };
        
        const userDisplay = document.createElement('span');
        userDisplay.className = 'user-welcome-msg'; // Klasse zum Identifizieren
        userDisplay.innerText = `Hallo, ${username} `;
        userDisplay.style.marginRight = "10px";
        authButton.parentNode.insertBefore(userDisplay, authButton);
    }
}