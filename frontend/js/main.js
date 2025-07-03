document.addEventListener('DOMContentLoaded', () => {

    // Logique pour le menu burger de Bulma
    const navbarBurgers = Array.prototype.slice.call(document.querySelectorAll('.navbar-burger'), 0);
    if (navbarBurgers.length > 0) {
        navbarBurgers.forEach( el => {
            el.addEventListener('click', () => {
                const targetId = el.dataset.target;
                const targetElement = document.getElementById(targetId);
                el.classList.toggle('is-active');
                targetElement.classList.toggle('is-active');
            });
        });
    }

    // La logique d'authentification (vérification de token, redirection, gestion du bouton de déconnexion,
    // mise à jour de l'email utilisateur) est gérée dans auth.js, qui a son propre
    // listener DOMContentLoaded. Il suffit de s'assurer que auth.js est inclus
    // dans les pages HTML concernées (avant main.js si main.js devait utiliser ses fonctions,
    // ou peu importe l'ordre si les deux sont auto-contenus avec leurs propres listeners).

    // Pour ce projet, auth.js est inclus et gère :
    // 1. Redirection si non authentifié (et pas sur index.html).
    // 2. Redirection si authentifié (et sur index.html).
    // 3. Initialisation du bouton de déconnexion.
    // 4. Mise à jour de l'affichage de l'email de l'utilisateur.

    // Aucune action spécifique à l'authentification n'est donc nécessaire dans main.js,
    // car auth.js est déjà complet à ce niveau.
    // main.js peut être utilisé pour d'autres initialisations globales d'UI non liées à l'auth.

    console.log("main.js loaded and DOM ready. Burger menu initialized.");
    // Si on avait d'autres initialisations globales (modales, tooltips, etc.), elles iraient ici.
});
