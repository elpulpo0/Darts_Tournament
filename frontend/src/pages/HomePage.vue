<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterLink } from 'vue-router'

// JSON-LD pour Schema.org (stringifié pour insertion dynamique)
const jsonLd = {
  "@context": "https://schema.org",
  "@type": "SportsClub",
  "name": "Badarts - Hérault Darts Club",
  "url": "https://badarts.fr",
  "description": "Association dédiée aux fléchettes traditionnelles dans l'Hérault. Tournois, entraînements et événements pour tous niveaux.",
  "address": {
    "@type": "PostalAddress",
    "addressRegion": "Hérault",
    "addressCountry": "FR"
  },
  "email": "mhdartsclub@gmail.com",
  "sameAs": [
    "https://www.facebook.com/HeraultDartsClub",
    "https://www.instagram.com/heraultdartsclub",
  ],
  "openingHours": "We 18:00-23:00, Th 18:00-23:00, Su 10:00-14:00",
  "sportsActivityLocation": [
    {
      "@type": "Place",
      "name": "Les Bock'Ale",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "2 Rue de la République",
        "addressLocality": "Montpellier",
        "addressRegion": "Hérault",
        "postalCode": "34000",
        "addressCountry": "FR"
      }
    },
    {
      "@type": "Place",
      "name": "Salle Tchoullouyan",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "Rue des Oliviers",
        "addressLocality": "Villeveyrac",
        "addressRegion": "Hérault",
        "postalCode": "34560",
        "addressCountry": "FR"
      }
    },
    {
      "@type": "Place",
      "name": "Brasserie des Sports",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "2 Avenue de la Gare",
        "addressLocality": "Vendargues",
        "addressRegion": "Hérault",
        "postalCode": "34740",
        "addressCountry": "FR"
      }
    }
  ],
  "breadcrumb": {
    "@type": "BreadcrumbList",
    "itemListElement": [
      { "@type": "ListItem", "position": 1, "name": "Accueil" }
    ]
  }
}

onMounted(() => {
  // Évite doublons : supprime si déjà présent
  const existingScript = document.getElementById('badarts-jsonld')
  if (existingScript) existingScript.remove()

  // Crée et insère le script
  const script = document.createElement('script')
  script.id = 'badarts-jsonld'
  script.type = 'application/ld+json'
  script.text = JSON.stringify(jsonLd)
  document.head.appendChild(script)
})
</script>

<template>
  <div class="homepage">
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content">
        <h1>Badarts - Hérault Darts Club</h1>
        <p>Viens partager la passion des fléchettes traditionnelles dans l'Hérault ! Participe à nos tournois locaux à
          Montpellier et environs, suis tes classements en ligue LSEF/CMER et découvres une communauté dynamique.</p>
        <router-link to="/tournaments" rel="nofollow" class="tournament-button">Voir les tournois locaux</router-link>
        <router-link to="/calendar" rel="nofollow" class="tournament-button">Consulter le calendrier
          LSEF/CMER</router-link>
      </div>
      <img src="@/assets/mascotte.png" alt="Mascotte Badarts représentant le club de fléchettes Hérault"
        class="hero-image" loading="lazy" />
    </section>

    <!-- Club Introduction -->
    <section class="section club-intro">
      <h2>À Propos du club</h2>
      <p>Le Hérault Darts Club (Badarts) est une association dédiée aux amateurs de fléchettes traditionnelles dans la
        région de l'Hérault, particulièrement autour de Montpellier. Fondé pour réunir les passionnés, notre club
        organise des tournois réguliers, des entraînements et des événements sociaux pour tous les niveaux, du débutant
        au compétiteur aguerri.</p>
      <p>Affiliations du club :</p>
      <div class="affiliations-container">
        <div class="affiliation-item">
          <img class="logo-affiliation" src="@/assets/ffd.png" alt="Logo Fédération Française de Darts FFD"
            loading="lazy" />
          <a href="https://www.ffdarts.fr/" target="_blank" class="social-link">Fédération Française de Darts</a>
          <p><a href="https://www.ffdarts.fr/classement/" target="_blank" class="cta-link">Classements nationaux FFD</a>
          </p>
        </div>
        <div class="affiliation-item">
          <img class="logo-affiliation" src="@/assets/lsef.png" alt="Logo Ligue Sud Est LSEF" loading="lazy" />
          <a href="https://lsef.fr/" target="_blank" class="social-link">Ligue Sud Est</a>
          <p><router-link to="/leaderboard/ligue" rel="nofollow" class="cta-link">Classement officiel LSEF</router-link>
          </p>
        </div>
        <div class="affiliation-item">
          <img class="logo-affiliation" src="@/assets/cmer.png" alt="Logo Comité Méridional CMER" loading="lazy" />
          <a href="https://www.facebook.com/comte.meridional.lsef/" target="_blank" class="social-link">Comité
            Méridional</a>
          <p><router-link to="/leaderboard/comite" rel="nofollow" class="cta-link">Classement officiel
              CMER</router-link></p>
        </div>
      </div>
    </section>

    <!-- Membership Section -->
    <section class="section membership">
      <h2>Rejoins-nous</h2>
      <p>Deviens membre du club Badarts et profite de nos événements exclusifs, d'un accès à nos installations et d'une
        communauté accueillante. Pour adhérer, plusieurs options s'offrent à toi :</p>
      <ul>
        <li>Contacte-nous (voir ci-dessous)</li>
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
      <div class="membership-footer">
        <a href="#contact" class="cta-link">En savoir plus</a>
        <div class="logo-container">
          <img class="logo-footer" src="@/assets/bockale.png" alt="Logo Les Bock'Ale" loading="lazy" />
          <img class="logo-footer" src="@/assets/brasserie.png" alt="Logo Brasserie des Sports" loading="lazy" />
        </div>
      </div>
    </section>

    <!-- Upcoming Events Section -->
    <section class="section events">
      <h2>Événements à venir</h2>
      <p>Participe à nos tournois de fléchettes en simple ou double dans l'Hérault. Consulte la liste complète des
        tournois, inscris-toi dès maintenant et suis les classements en direct !</p>
      <router-link to="/tournaments" rel="nofollow" class="cta-link">Découvrir les tournois</router-link>
      <router-link to="/leaderboard/club" rel="nofollow" class="cta-link">Voir le classement des tournois
        locaux</router-link>
    </section>

    <!-- Contact Section -->
    <section id="contact" class="section contact">
      <h2>Contacte-nous</h2>
      <p>Pour toute question, contacte-nous par email à <a href="mailto:mhdartsclub@gmail.com">mhdartsclub@gmail.com</a>
        ou suis-nous sur nos réseaux sociaux :</p>
      <div class="social-links">
        <a href="https://www.facebook.com/HeraultDartsClub" target="_blank" class="social-link" rel="noopener">
          <img class="icon" src="@/assets/fb.png" alt="Facebook Hérault Darts Club" loading="lazy" />
        </a>
        <a href="https://www.instagram.com/heraultdartsclub" target="_blank" class="social-link" rel="noopener">
          <img class="icon" src="@/assets/in.png" alt="Instagram Hérault Darts Club" loading="lazy" />
        </a>
        <a href="https://discord.gg/PrgQ2FCCUd" target="_blank" class="social-link" rel="noopener">
          <img class="icon" src="@/assets/dc.png" alt="Discord Badarts" loading="lazy" />
        </a>
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
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 3rem 1rem;
  background: var(--color-light-shadow);
  border-radius: var(--radius);
  margin-bottom: 2rem;
  width: 100%;
}

.hero-content {
  flex: 1;
  padding-right: 1rem;
}

.hero-image {
  max-height: 250px;
  object-fit: contain;
  border-radius: var(--radius);
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
  color: var(--color-mascot);
}

p {
  font-size: 1.2rem;
  margin-bottom: 1.5rem;
  line-height: 1.6;
}

.tournament-button {
  display: inline-block;
  padding: 1rem 2rem;
  margin: 0.2rem;
  background: var(--color-mascot);
  color: var(--color-bg);
  text-decoration: none;
  border-radius: var(--radius);
  font-size: 1.1rem;
  font-weight: 600;
  transition: background 0.3s, transform 0.2s;
}

.tournament-button:hover {
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

.icon {
  max-height: 30px;
}

.affiliations-container {
  display: flex;
  justify-content: center;
  gap: 80px;
  flex-wrap: wrap;
}

.affiliation-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.affiliation-item p {
  margin: 0.5rem 0 0 0;
  font-size: 0.9rem;
  text-align: center;
}

.logo-affiliation {
  max-height: 125px;
  height: auto;
  margin-bottom: 10px;
}

.membership-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
}

.logo-container {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.logo-footer {
  max-width: 120px;
  height: auto;
}

.cta-link {
  display: inline-block;
  margin: 0.2rem;
  padding: 0.5rem 1rem;
  background: transparent;
  color: var(--color-accent);
  text-decoration: none;
  border: 1px solid var(--color-accent);
  border-radius: var(--radius);
  transition: all 0.3s;
}

.cta-link:hover {
  background: var(--color-accent);
  color: var(--color-bg);
}

@media (max-width: 768px) {
  .homepage {
    padding: 1rem;
  }

  .logo-footer {
    max-width: 70px;
    height: auto;
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

  .tournament-button {
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
  }

  .section {
    padding: 1rem;
    margin: 1rem 0;
  }

  .cta-link {
    display: block;
    text-align: center;
    margin: 1rem auto;
  }

  .affiliations-container {
    gap: 40px;
    /* Réduit pour mobile */
  }
}
</style>