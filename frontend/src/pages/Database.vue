<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '../stores/useAuthStore'
import { useToast } from 'vue-toastification'
import backendApi from '../axios/backendApi'

const toast = useToast()

const authStore = useAuthStore();

const showDeleteModal = ref(false)
const backupToDelete = ref<string | null>(null)

const backupMessage = ref('')
const backupError = ref('')
const backupLoading = ref(false)
const lastBackup = ref<Backup | null>(null)
const backups = ref<Backup[]>([])
const disk = ref<{ total_bytes: number; free_bytes: number; used_bytes: number } | null>(null)

const authHeaders = () => ({
  headers: { Authorization: `Bearer ${authStore.token}` }
})

async function fetchDisk() {
  try {
    const { data } = await backendApi.get(`/admin/monitor/storage`, authHeaders())
    disk.value = data
    if (data.free_bytes / data.total_bytes < 0.1) {
      toast.warning("⚠️ Low disk space: less than 10% available")
      sendMessage(`⚠️ Warning: Disk space critically low (${(data.free_bytes / data.total_bytes * 100).toFixed(2)}% left)`)
    }

  } catch (e: any) {
    console.error('Error disk fetch', e)
  }
}

const diskUsage = computed(() => {
  if (!disk.value) return 0
  return +(disk.value.used_bytes / disk.value.total_bytes * 100)
})

function formatRelativeDate(timestamp: number): string {
  const now = new Date()
  const date = new Date(timestamp * 1000)
  const diffMs = now.getTime() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHours = Math.floor(diffMin / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffDays >= 2) return `${diffDays} days ago`
  if (diffDays === 1) return `yesterday`
  if (diffHours >= 2) return `${diffHours} hours ago`
  if (diffHours === 1) return `one hour ago`
  if (diffMin >= 2) return `${diffMin} minutes ago`
  if (diffMin === 1) return `une minute ago`
  return `few seconds ago`
}

type Backup = {
  filename: string
  created_at: number
  size_bytes?: number
}

function confirmDelete(filename: string) {
  backupToDelete.value = filename
  showDeleteModal.value = true
}

async function deleteBackupConfirmed() {
  if (!backupToDelete.value) return
  showDeleteModal.value = false

  try {
    await backendApi.delete(`/admin/backup/${backupToDelete.value}`, authHeaders())
    fetchBackups()
    backupMessage.value = ''
    toast.success(`Backup "${backupToDelete.value}" succesfully deleted`)
  } catch (e: any) {
    console.error('Errdeleting backup', e)
    toast.error(e.response?.data?.detail || 'Erreur deleting backup')
  }
  backupToDelete.value = null
}

function cancelDelete() {
  backupToDelete.value = null
  showDeleteModal.value = false
}

function formatSize(bytes: number): string {
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  if (bytes === 0) return '0 Byte'
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + sizes[i]
}

async function fetchBackups() {
  try {
    const { data } = await backendApi.get(`/admin/backups`, authHeaders())
    if (Array.isArray(data.backups) && data.backups.length > 0) {
      backups.value = data.backups as Backup[]

      // On trie et on prend le dernier backup
      const sorted = backups.value.sort((a, b) => b.created_at - a.created_at)
      lastBackup.value = sorted[0]
    } else {
      backups.value = []
      lastBackup.value = null
    }
  } catch (e) {
    console.error('Error loading backups', e)
    backups.value = []
    lastBackup.value = null
  }
}

const lastBackupDate = computed(() => {
  return lastBackup.value ? new Date(lastBackup.value.created_at * 1000) : null
})

async function doBackup() {
  backupMessage.value = ''
  backupError.value = ''
  backupLoading.value = true
  try {
    const { data } = await backendApi.post(`/admin/backup`, {}, authHeaders())
    toast.success(`✅ Backup created : ${data.filename}`)
    fetchBackups()
  } catch (e: any) {
    backupError.value = e.response?.data?.detail || '❌ Error backing up'
    toast.error(backupError.value)
  } finally {
    backupLoading.value = false
  }
}

// Monitoring tables
type TableStat = { table: string; rows: number | null }
const tables = ref<TableStat[]>([])
const tablesLoading = ref(false)
const tablesError = ref('')

async function fetchTables() {
  tablesLoading.value = true
  tablesError.value = ''
  try {
    const { data } = await backendApi.get(`/admin/monitor/tables`, authHeaders())
    tables.value = data.tables
  } catch (e: any) {
    tablesError.value = e.response?.data?.detail || 'Error loading tables'
    toast.error(tablesError.value)
  } finally {
    tablesLoading.value = false
  }
}

// Santé de la base
interface DbHealth {
  integrity_check: string
  page_count: number
  page_size: number
  calculated_size_bytes: number
  file_size_bytes: number | null
  freelist_count: number
  journal_mode: string
  synchronous: string
  sqlite_version: string
}

const health = ref<DbHealth | null>(null)
const healthLoading = ref(false)
const healthError = ref('')

async function fetchHealth() {
  healthLoading.value = true
  healthError.value = ''
  try {
    const { data } = await backendApi.get(`/admin/monitor/health`, authHeaders())
    health.value = data
  } catch (e: any) {
    healthError.value = e.response?.data?.detail || 'Error loading database health'
    toast.error(healthError.value);
  } finally {
    healthLoading.value = false
  }
}

async function downloadBackup(filename: string) {
  try {
    const response = await backendApi.get(`/admin/backup/${filename}`, {
      responseType: 'blob',
      headers: { Authorization: `Bearer ${authStore.token}` },
    })

    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    toast.success(`📦 Backup "${filename}" downloaded`)
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "Error downloading backup")
  }
}

const showAll = ref(false)

const visibleBackups = computed(() => {
  return showAll.value ? backups.value : backups.value.slice(0, 5)
})

const totalBackupSize = computed(() => {
  return backups.value.reduce((sum, b) => sum + (b.size_bytes || 0), 0)
})

const sendMessage = async (message: string) => {
  try {
    await backendApi.post('/notify', { message });
  } catch (error) {
    console.error(error);
  }
};

onMounted(() => {
  fetchTables()
  fetchHealth()
  fetchBackups()
  fetchDisk()
})

</script>

<template>
  <div v-if="authStore.isAuthenticated">
    <div v-if="authStore.scopes.includes('admin')">
      <div class="module">
        <div class="backup-group">
          <h2>Backups</h2>
          <button :disabled="backupLoading" @click="doBackup">
            {{ backupLoading ? 'Backing up...' : 'Create backup' }}
          </button>
          <p v-if="backupMessage" style="color: green;">{{ backupMessage }}</p>
          <p v-if="backupError" style="color: red;">{{ backupError }}</p>

          <p v-if="lastBackup && lastBackupDate">
            Last backup : {{ lastBackupDate.toLocaleString() }}
            ({{ formatRelativeDate(lastBackup.created_at) }})
          </p>
          <p v-else>No backup found</p>

          <h3>{{ backups.length }} backup(s) —
            <span v-if="!showAll">(last 5 shown)</span>
            <span v-else>(all shown)</span>
          </h3>

          <button v-if="backups.length > 5" style="margin-top: 10px;" @click="showAll = !showAll">
            {{ showAll ? 'Show less' : 'Show more' }}
          </button>

          <ul v-if="backups && backups.length">
            <li v-for="backup in visibleBackups" :key="backup.filename">
              <strong>{{ backup.filename }}</strong> — created on {{ new Date(backup.created_at * 1000).toLocaleString()
              }}
              <span v-if="backup.size_bytes"> — {{ formatSize(backup.size_bytes) }}</span>

              <span role="button" tabindex="0" style="margin-left: 10px; color: red; cursor: pointer;"
                title="Delete backup" @click="confirmDelete(backup.filename)">
                🗑
              </span>
              <span role="button" tabindex="0" style="margin-left: 10px; color: var(--color-accent); cursor: pointer;"
                title="Download backup" @click="downloadBackup(backup.filename)">
                ⬇
              </span>
            </li>
            <p>Total backup size : {{ formatSize(totalBackupSize) }}</p>
          </ul>

          <p v-else>No backups available</p>

          <div v-if="disk">
            <h4>Disk space</h4>
            <progress :value="diskUsage" max="100" :style="{
              accentColor:
                diskUsage < 70 ? 'green' : diskUsage < 90 ? 'orange' : 'red'
            }" />

            <p>{{ formatSize(disk.free_bytes) }} free out of {{ formatSize(disk.total_bytes) }} ({{
              diskUsage.toFixed(2)
            }}% used)</p>
          </div>
        </div>
      </div>

      <div v-if="showDeleteModal" class="modal-overlay">
        <div class="modal-content">
          <p>Delete backup<strong>{{ backupToDelete }}</strong> ?</p>
          <button style="color: red;" @click="deleteBackupConfirmed">Yes, delete</button>
          <button @click="cancelDelete">Cancel</button>
        </div>
      </div>

      <div class="module">
        <h2>Database Health Status</h2>
        <div v-if="healthLoading">Loading...</div>
        <div v-if="healthError" style="color: red;">{{ healthError }}</div>

        <table v-if="health && !healthLoading">
          <tbody>
            <tr>
              <th>Integrity Check</th>
              <td>{{ health.integrity_check }}</td>
            </tr>
            <tr>
              <th>Page Count</th>
              <td>{{ health.page_count }}</td>
            </tr>
            <tr>
              <th>Page Size (bytes)</th>
              <td>{{ health.page_size }}</td>
            </tr>
            <tr>
              <th>Calculated Size (bytes)</th>
              <td>{{ health.calculated_size_bytes }}</td>
            </tr>
            <tr>
              <th>File Size (bytes)</th>
              <td>{{ health.file_size_bytes ?? 'N/A' }}</td>
            </tr>
            <tr>
              <th>Free Pages (freelist_count)</th>
              <td>{{ health.freelist_count }}</td>
            </tr>
            <tr>
              <th>Journal Mode</th>
              <td>{{ health.journal_mode }}</td>
            </tr>
            <tr>
              <th>Synchronous mode</th>
              <td>{{ health.synchronous }}</td>
            </tr>
            <tr>
              <th>SQLite Version</th>
              <td>{{ health.sqlite_version }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="module">
        <h2>Tables and Number of Rows</h2>
        <div v-if="tablesLoading">Loading...</div>
        <div v-if="tablesError" style="color: red;">{{ tablesError }}</div>
        <table v-if="tables.length && !tablesLoading">
          <thead>
            <tr>
              <th>Table name</th>
              <th>Number of rows</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="table in tables" :key="table.table">
              <td>{{ table.table }}</td>
              <td>{{ table.rows !== null ? table.rows : 'Erreur' }}</td>
            </tr>
          </tbody>
        </table>
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