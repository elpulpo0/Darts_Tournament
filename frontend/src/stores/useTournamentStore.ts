import { defineStore } from 'pinia'
import { ref } from 'vue'
import backendApi from '../axios/backendApi'

export const useTournamentStore = defineStore('tournament', () => {
    const tournamentDetail = ref<TournamentFullDetailSchema | null>(null)
    const loading = ref(false)

    const fetchTournamentDetail = async (tournamentId: number) => {
        loading.value = true
        const { data } = await backendApi.get(`/tournaments/${tournamentId}/details`)
        tournamentDetail.value = data
        loading.value = false
    }

    return {
        tournamentDetail,
        loading,
        fetchTournamentDetail,
    }
})