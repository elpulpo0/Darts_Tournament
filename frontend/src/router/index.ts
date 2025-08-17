import { createRouter, createWebHistory } from 'vue-router'
import Users from '../pages/Users.vue'
import Database from '../pages/Database.vue'
import Logs from '../pages/Logs.vue'
import TournamentManagement from '../pages/TournamentManagement.vue';
import TournamentsListing from '../pages/TournamentsListing.vue';
import Leaderboard from '../pages/Leaderboard.vue';
import TournamentProjection from '../pages/TournamentProjection.vue';

const routes = [
  {
    path: '/',
    redirect: '/tournaments',
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
    path: '/leaderboard',
    name: 'Leaderboard',
    component: Leaderboard
  },
  {
    path: '/tournaments/:tournamentId/projection',
    name: 'TournamentProjection',
    component: TournamentProjection,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
