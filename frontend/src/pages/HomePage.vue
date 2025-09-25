<template>
    <div class="homepage">
        <!-- Hero Section -->
        <section class="hero">
            <h1>Badarts - Hérault Darts Club</h1>
            <p>Viens partager la passion des fléchettes dans l'Hérault ! Participes à nos tournois, suis tes classements
                et découvres une communauté dynamique.</p>
        </section>

        <!-- Club Introduction -->
        <section class="section club-intro">
            <h2>À Propos du Club</h2>
            <p>Le Hérault Darts Club (Badarts) est une association dédiée aux amateurs de fléchettes traditionnelles
                dans la région de
                l'Hérault. Fondé pour réunir les passionnés, notre club organise des tournois réguliers, des
                entraînements et des événements sociaux pour tous les niveaux, du débutant au compétiteur aguerri.</p>
            <p>
                Affiliations du club :
            <ul>
                <li><a href="https://www.ffdarts.fr/" target="_blank" class="social-link">Fédération Française de
                        Darts</a>
                </li>
                <li><a href="https://lsef.fr/" target="_blank" class="social-link">Ligue Sud Est</a></li>
                <li><a href="https://www.facebook.com/comte.meridional.lsef/" target=" _blank"
                        class="social-link">Comité
                        Méridionnal</a></li>
            </ul>
            </p>
        </section>

        <!-- Membership Section -->
        <section class="section membership">
            <h2>Rejoins-nous</h2>
            <p>Deviens membre du club Badarts et profites de nos événements exclusifs, d'un accès à nos installations et
                d'une communauté accueillante. Pour adhérer, plusieurs options s'offrent à toi :</p>
            <ul>
                <li>Contactes-nous (voir ci-dessous)</li>
                <li>Rejoins notre serveur Discord</li>
                <li>
                    Viens nous rencontrer lors de nos sessions hebdomadaires :
                    <ul>
                        <li>Mercredis soir aux Bock'ale à Montpellier</li>
                        <li>Jeudis soir à Villeveyrac</li>
                        <li>Dimanches matin à La Brasserie des Sports à Vendargues</li>
                    </ul>
                </li>
            </ul>
            <a href="#contact" class="action-button">En savoir plus</a>
        </section>

        <!-- Upcoming Events Section -->
        <section class="section events">
            <h2>Événements à Venir</h2>
            <p>Participes à nos tournois, que tu sois en simple ou en double. Consultes la liste complète
                des tournois et inscris-toi dès maintenant !</p>
            <router-link to="/tournaments" class="tournament-button">Découvrir les Tournois</router-link>
        </section>

        <!-- Contact Section -->
        <section id="contact" class="section contact">
            <h2>Contactes-nous</h2>
            <p>Pour toute question, contactes-nous par email à <a
                    href="mailto:mhdartsclub@gmail.com">mhdartsclub@gmail.com</a> ou suis-nous sur nos réseaux sociaux
                :</p>
            <div class="social-links">
                <a href="https://www.facebook.com/HeraultDartsClub" target="_blank" class="social-link">Facebook</a>
                <a href="https://www.instagram.com/heraultdartsclub" target="_blank" class="social-link">Instagram</a>
                <a href="https://discord.gg/PrgQ2FCCUd" target="_blank" class="social-link">Discord</a>
            </div>
        </section>
    </div>
</template>

<style scoped>
.homepage {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-height: 100vh;
    padding: 2rem;
    background: var(--color-bg);
    color: var(--color-fg);
}

.hero {
    text-align: center;
    padding: 3rem 1rem;
    background: var(--color-light-shadow);
    border-radius: var(--radius);
    margin-bottom: 2rem;
    width: 100%;
    max-width: 800px;
}

.section {
    max-width: 800px;
    margin: 2rem 0;
    padding: 1.5rem;
    background: var(--color-bg);
    border-radius: var(--radius);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

h1 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
}

h2 {
    font-size: 1.8rem;
    margin-bottom: 1rem;
    color: var(--color-accent);
}

p {
    font-size: 1.2rem;
    margin-bottom: 1.5rem;
    line-height: 1.6;
}

.tournament-button,
.action-button {
    display: inline-block;
    padding: 1rem 2rem;
    background: var(--color-accent);
    color: var(--color-bg);
    text-decoration: none;
    border-radius: var(--radius);
    font-size: 1.1rem;
    font-weight: 600;
    transition: background 0.3s, transform 0.2s;
}

.tournament-button:hover,
.action-button:hover {
    background: var(--color-success);
    transform: translateY(-2px);
}

.social-links {
    display: flex;
    gap: 1rem;
}

.social-link {
    color: var(--color-accent);
    text-decoration: none;
    font-size: 1rem;
    transition: color 0.3s;
}

.social-link:hover {
    color: var(--color-success);
}

@media (max-width: 768px) {
    .homepage {
        padding: 1rem;
    }

    .hero {
        padding: 2rem 1rem;
    }

    h1 {
        font-size: 2rem;
    }

    h2 {
        font-size: 1.5rem;
    }

    p {
        font-size: 1rem;
    }

    .tournament-button,
    .action-button {
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
    }

    .section {
        padding: 1rem;
        margin: 1rem 0;
    }
}
</style>