// Configuration de l'API
const API_BASE_URL = 'http://localhost:8000/api/v1'; // Adapter si nécessaire

/**
 * Stocke le token JWT dans localStorage.
 * @param {string} token Le token JWT.
 */
function storeToken(token) {
    localStorage.setItem('accessToken', token);
}

/**
 * Récupère le token JWT depuis localStorage.
 * @returns {string|null} Le token JWT ou null s'il n'existe pas.
 */
function getToken() {
    return localStorage.getItem('accessToken');
}

/**
 * Supprime le token JWT et l'email de l'utilisateur de localStorage.
 */
function removeToken() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('userEmail');
}

/**
 * Gère la déconnexion de l'utilisateur.
 */
function logout() {
    removeToken();
    // S'assurer que la redirection se fait vers la racine du site pour index.html
    if (!window.location.pathname.endsWith('/') && !window.location.pathname.endsWith('index.html')) {
        window.location.href = 'index.html';
    } else if (window.location.pathname.endsWith('/') && window.location.href.includes('dashboard.html')) {
        // Cas où on est sur dashboard.html à la racine (ex: via live server)
        window.location.href = 'index.html';
    }
    // Si déjà sur index.html, pas besoin de rediriger.
}

/**
 * Met à jour l'affichage de l'email de l'utilisateur dans la navbar.
 */
function updateUserEmailDisplay() {
    const userEmailDisplay = document.getElementById('userEmailDisplay');
    if (userEmailDisplay) {
        const storedEmail = localStorage.getItem('userEmail');
        if (storedEmail) {
            userEmailDisplay.textContent = storedEmail;
        } else {
            userEmailDisplay.textContent = 'Utilisateur'; // Valeur par défaut
        }
    }
}


document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const loginError = document.getElementById('loginError');
    const logoutButton = document.getElementById('logoutButton');

    // --- Gestion de la page de connexion (index.html) ---
    if (loginForm) {
        // Si un token existe et qu'on est sur index.html, rediriger vers dashboard
        if (getToken()) {
            window.location.href = 'dashboard.html';
            return; // Arrêter l'exécution pour éviter d'attacher le listener du formulaire
        }

        loginForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            if (loginError) {
                loginError.style.display = 'none';
                loginError.textContent = '';
            }

            const emailInput = document.getElementById('email');
            const passwordInput = document.getElementById('password');
            const email = emailInput.value;
            const password = passwordInput.value;

            const formData = new URLSearchParams();
            formData.append('username', email); // L'API attend 'username'
            formData.append('password', password);

            try {
                const response = await fetch(`${API_BASE_URL}/auth/login/access-token`, {
                    method: 'POST',
                    body: formData,
                });

                if (response.ok) {
                    const data = await response.json();
                    storeToken(data.access_token);
                    localStorage.setItem('userEmail', email); // Stocker l'email pour affichage
                    window.location.href = 'dashboard.html';
                } else {
                    const errorData = await response.json().catch(() => ({ detail: "Erreur inconnue ou réponse non-JSON." }));
                    let errorMessage = `Échec de la connexion (Code: ${response.status}). `;
                    if (typeof errorData.detail === 'string') {
                        errorMessage += errorData.detail;
                    } else if (Array.isArray(errorData.detail)) { // Erreurs de validation Pydantic
                        errorMessage += errorData.detail.map(err => err.msg).join(', ');
                    } else {
                        errorMessage += "Veuillez vérifier vos identifiants.";
                    }
                    if (loginError) {
                        loginError.textContent = errorMessage;
                        loginError.style.display = 'block';
                    } else {
                        alert(errorMessage); // Fallback si loginError n'existe pas
                    }
                }
            } catch (error) {
                console.error('Erreur réseau ou autre lors de la connexion:', error);
                if (loginError) {
                    loginError.textContent = 'Une erreur réseau est survenue. Veuillez réessayer plus tard.';
                    loginError.style.display = 'block';
                } else {
                    alert('Une erreur réseau est survenue.');
                }
            }
        });
    }

    // --- Logique commune à toutes les pages (doit être après DOMContentLoaded) ---
    // Vérifier l'authentification sur les pages autres que index.html
    if (!window.location.pathname.endsWith('/') && !window.location.pathname.endsWith('index.html')) {
        if (!getToken()) {
            window.location.href = 'index.html'; // Rediriger si pas de token
            return; // Arrêter l'exécution pour éviter d'autres actions sur la page non autorisée
        }
    }

    // Gestion du bouton de déconnexion (s'il existe sur la page)
    if (logoutButton) {
        logoutButton.addEventListener('click', (event) => {
            event.preventDefault();
            logout();
        });
    }

    // Mettre à jour l'email de l'utilisateur dans la navbar (s'il existe sur la page)
    updateUserEmailDisplay();
});

// Exporter pour d'autres scripts si nécessaire (si on passe à des modules JS)
// export { getToken, logout, API_BASE_URL };
