import { defineStore } from 'pinia'
import { ref } from 'vue'
import backendApi from '../axios/backendApi'

export const useTournamentStore = defineStore('tournament', () => {
    const tournamentDetail = ref<any>(null)
    const loading = ref(false)

    const fetchTournamentDetail = async (tournamentId: number) => {
        loading.value = true
        const { data } = await backendApi.get(`/tournaments/${tournamentId}/details`)
        tournamentDetail.value = data
        loading.value = false
    }

    // expose all data and fetch methods
    return {
        tournamentDetail,
        loading,
        fetchTournamentDetail,
    }
})