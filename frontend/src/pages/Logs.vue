<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { backend_url } from '../config/config'
import { useAuthStore } from '../stores/useAuthStore'
import { toast } from 'vue3-toastify'
const authStore = useAuthStore()

type LogFile = { filename: string; path: string; size_bytes: number }
type LogsResponse = { logs: { app: LogFile[]; debug: LogFile[]; warning: LogFile[]; error: LogFile[] } }

const logLevels = ['app', 'debug', 'warning', 'error'] as const
type LogLevel = typeof logLevels[number]

const selectedLevel = ref<LogLevel>('app')
const logFiles = ref<LogsResponse['logs'] | null>(null)
const selectedFile = ref<LogFile | null>(null)
const fileLines = ref<string[]>([])
const loading = ref(false)
const error = ref('')

async function fetchLogFiles() {
    try {
        const { data } = await axios.get(`${backend_url}/admin/monitor/logs`, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        logFiles.value = data.logs
    } catch (e: any) {
        error.value = e.response?.data?.detail || 'Error fetching logs'
        toast.error(e.response?.data?.detail || 'Error loading logs files.')
    }
}

async function loadLogFile(file: LogFile) {
    selectedFile.value = file
    fileLines.value = []
    loading.value = true
    error.value = ''

    try {
        const { data } = await axios.get(`${backend_url}/admin/monitor/logs/${selectedLevel.value}?filename=${encodeURIComponent(file.filename)}`, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        fileLines.value = data.lines || []
    } catch (e: any) {
        error.value = e.response?.data?.detail || 'Error loading file.'
    } finally {
        loading.value = false
    }
}

const currentFiles = computed(() => {
    return logFiles.value ? logFiles.value[selectedLevel.value] : []
})

onMounted(() => {
    fetchLogFiles()
})

function formatLine(line: string): string {
    if (/error|exception|fail/i.test(line)) {
        return `<span class="log-error">${line}</span>`
    } else if (/warn/i.test(line)) {
        return `<span class="log-warning">${line}</span>`
    } else if (/debug/i.test(line)) {
        return `<span class="log-debug">${line}</span>`
    }
    return `<span class="log-default">${line}</span>`
}

const formattedLines = computed(() => {
    return fileLines.value.map(formatLine).join('\n')
})

async function onLevelChange(level: LogLevel) {
    selectedLevel.value = level
    selectedFile.value = null
    fileLines.value = []
    error.value = ''

    await fetchLogFiles()

    if (logFiles.value && logFiles.value[level]?.length > 0) {
        loadLogFile(logFiles.value[level][0])
    }
}
</script>

<template>
    <div v-if="authStore.isAuthenticated">
        <div v-if="authStore.scopes.includes('admin')">
            <div class="module">
                <h2>System logs</h2>

                <div>
                    <button v-for="level in logLevels"
                        :class="['log-btn', `log-btn--${level}`, { active: selectedLevel === level }]"
                        @click="onLevelChange(level)" :key="level">
                        {{ level.toUpperCase() }}
                    </button>

                </div>

                <div v-if="currentFiles.length">
                    <h3>Available files</h3>
                    <ul>
                        <li v-for="file in currentFiles" :key="file.filename">
                            <strong style="cursor: pointer; color: #3af;" @click="loadLogFile(file)">
                                📄 {{ file.filename }}
                            </strong> — {{ (file.size_bytes / 1024).toFixed(1) }} KB
                        </li>
                    </ul>
                </div>
                <p v-else>No {{ selectedLevel }} file found.</p>

                <div v-if="selectedFile">
                    <h3>Log content : {{ selectedFile.filename }}</h3>
                    <div v-if="loading">Loading...</div>

                    <pre v-if="fileLines.length" class="log-output" v-html="formattedLines" />

                </div>
            </div>
        </div>
        <div v-if="!authStore.scopes.includes('admin')">
            <div class="module module-prel">
                <p>Vous n'avez pas les droits suffisants pour accéder à cette section</p>
            </div>
        </div>
    </div>
    <div v-else class="centered-block">
        <h2>🔒 Connexion requise</h2>
        <p>Veuillez vous connecter pour accéder aux fonctionnalités de l’application.</p>
    </div>
</template>

<style scoped>
.log-output {
    background: var(--color-bg);
    color: var(--color-bg-lighter);
    padding: 10px;
    max-height: 500px;
    overflow-y: auto;
    white-space: pre-wrap;
}

.log-error {
    color: var(--color-error);
    font-weight: bold;
}

.log-warning {
    color: var(--color-accent-bis);
}

.log-debug {
    color: var(--color-bg-lighter);
}

.log-default {
    color: var(--color-accent);
}

.log-btn {
    margin-right: 8px;
    padding: 5px 12px;
    border: none;
    cursor: pointer;
    color: var(--color-light-shadow);
    border-radius: 4px;
    transition: background-color 0.3s ease;
}

/* Couleurs basées sur les logs */
.log-btn--app {
    background-color: var(--color-accent);
    /* info color */
}

.log-btn--debug {
    background-color: var(--color-bg-lighter);
    /* debug color */
}

.log-btn--warning {
    background-color: var(--color-accent-bis);
    /* warning color */
    color: var(--color-bg);
    /* texte plus lisible sur jaune */
}

.log-btn--error {
    background-color: var(--color-error);
    /* error color */
}

.log-btn.active {
    box-shadow: 0 0 15px var(--color-light-shadow);
    font-weight: bold;
    color: var(--color-bg);
}
</style>