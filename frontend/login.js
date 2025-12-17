// >>> HIER die Base-URL von eurem Professor/Backend eintragen <<<
const API_BASE = "http://localhost:8000"; // Beispiel!

const form = document.getElementById("login-form");
const emailEl = document.getElementById("email");
const pwEl = document.getElementById("password");
const errEl = document.getElementById("login-error");
const btnEl = document.getElementById("login-btn");

function showError(msg) {
  errEl.textContent = msg;
  errEl.style.display = "block";
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  errEl.style.display = "none";
  btnEl.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      // Swagger Screenshot: body hat username + password
      body: JSON.stringify({
        username: emailEl.value.trim(),
        password: pwEl.value,
      }),
    });

    if (!res.ok) {
      // oft kommt bei FastAPI 422 wenn body falsch ist
      const text = await res.text();
      throw new Error(`Login fehlgeschlagen (${res.status}). ${text}`);
    }

    // Swagger zeigt "string" als Response -> also Token als Text
    const token = await res.text();

    // speichern (nur für Session/Tab)
    sessionStorage.setItem("camo_token", token);

    // optional: zurück auf Startseite
    window.location.href = "index.html";
  } catch (err) {
    showError(err.message || "Login fehlgeschlagen.");
  } finally {
    btnEl.disabled = false;
  }
});
