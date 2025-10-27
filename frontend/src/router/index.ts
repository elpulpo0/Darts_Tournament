import { createRouter, createWebHistory } from 'vue-router'
import Users from '@/pages/Users.vue'
import Database from '@/pages/Database.vue'
import Logs from '@/pages/Logs.vue'
import TournamentManagement from '@/pages/TournamentManagement.vue';
import TournamentsListing from '@/pages/TournamentsListing.vue';
import OfficialCalendar from '../pages/OfficialCalendar.vue';
import LeaderboardClub from '@/pages/LeaderboardClub.vue';
import LeaderboardLigue from '@/pages/LeaderboardLigue.vue';
import LeaderboardComite from '@/pages/LeaderboardComite.vue';
import TournamentProjection from '@/pages/TournamentProjection.vue';
import HomePage from '@/pages/HomePage.vue';
import Inscriptions from '../pages/Inscriptions.vue';

export const routes = [
  {
    path: '/',
    component: HomePage,
  },
  {
    path: '/users',
    name: 'Users',
    component: Users
  },
  {
    path: '/tournament-management/:tournamentId',
    name: 'TournamentManagement',
    component: TournamentManagement,
  },
  {
    path: '/tournaments',
    name: 'TournamentsListing',
    component: TournamentsListing,
  },
  {
    path: '/calendar',
    name: 'OfficialCalendar',
    component: OfficialCalendar,
  },
  {
    path: '/database',
    name: 'Database',
    component: Database
  },
  {
    path: '/logs',
    name: 'Logs',
    component: Logs
  },
  {
    path: '/leaderboard/club',
    name: 'Leaderboardclub',
    component: LeaderboardClub
  },
  {
    path: '/leaderboard/ligue',
    name: 'LeaderboardLigue',
    component: LeaderboardLigue
  },
  {
    path: '/leaderboard/comite',
    name: 'LeaderboardComite',
    component: LeaderboardComite
  },
  {
    path: '/tournaments/:tournamentId/projection',
    name: 'TournamentProjection',
    component: TournamentProjection,
  },
  {
    path: '/home',
    name: 'HomePage',
    component: HomePage,
  },
  {
    path: '/inscriptions',
    name: 'Inscriptions',
    component: Inscriptions,
    props: true
  },
  {
    path: '/shop',
    name: 'Shop',
    component: () => import('../pages/Shop.vue'),
    meta: {
      title: 'Boutique Badarts',
      description: 'Découvrez le merch officiel Badarts !'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router