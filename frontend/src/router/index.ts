import { createRouter, createWebHistory } from 'vue-router'
import Users from '@/pages/Users.vue'
import Database from '@/pages/Database.vue'
import Logs from '@/pages/Logs.vue'
import TournamentManagement from '@/pages/TournamentManagement.vue';
import TournamentsListing from '@/pages/TournamentsListing.vue';
import Leaderboard from '@/pages/Leaderboard.vue';
import TournamentProjection from '@/pages/TournamentProjection.vue';
import HomePage from '@/pages/HomePage.vue';

const routes = [
  {
    path: '/',
    component: HomePage,
  },
  {
    path: '/users',
    component: Users
  },
  {
    path: '/tournament-management/:tournamentId',
    component: TournamentManagement,
  },
  {
    path: '/tournaments',
    component: TournamentsListing,
  },
  {
    path: '/database',
    component: Database
  },
  {
    path: '/logs',
    component: Logs
  },
  {
    path: '/leaderboard',
    component: Leaderboard
  },
  {
    path: '/tournaments/:tournamentId/projection',
    component: TournamentProjection,
  },
  {
    path: '/home',
    component: HomePage,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
