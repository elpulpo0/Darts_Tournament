<script setup lang="ts">
import { isAxiosError } from 'axios';
import { ref, watch } from 'vue'
import backendApi from '../axios/backendApi'
import { useToast } from 'vue-toastification'
import { useAuthStore } from '../stores/useAuthStore'
const authStore = useAuthStore();
const toast = useToast()

type User = {
  id: number
  name: string
  email: string
  role: string
  is_active: boolean
  tokens: { created_at: string, expires_at: string, revoked: boolean }[]
}

const users = ref<User[]>([])
const loading = ref(false)
const error = ref('')
const editingUserId = ref<number | null>(null);
const editName = ref('');
const editEmail = ref('');
const editPassword = ref('');
const editRole = ref('');
const newName = ref('');
const newEmail = ref('');
const newPassword = ref('');
const newRole = ref('');
const showCreateUser = ref(false);

const toggleCreateUserForm = () => {
  showCreateUser.value = !showCreateUser.value;
}

const fetchUsers = async () => {
  loading.value = true;
  error.value = '';
  try {
    const { data } = await backendApi.get(`/users/users`, {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    });

    if (Array.isArray(data)) {
      users.value = data;
    } else {
      throw new Error('Invalid user data');
    }

    const { data: tokensData } = await backendApi.get(`/auth/refresh-tokens`, {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    });

    tokensData.forEach((tokenData: any) => {
      const user = users.value.find(user => user.id === tokenData.user_id);
      if (user) {
        if (!user.tokens) {
          user.tokens = [];
        }
        if (!tokenData.revoked) {
          user.tokens.push({
            created_at: tokenData.created_at,
            expires_at: tokenData.expires_at,
            revoked: tokenData.revoked
          });
        }
      }
    });
  } catch (err: any) {
    console.error('Error while fetching users and tokens', err);

    if (isAxiosError(err)) {
      if (err.response?.status === 403) {
        error.value = '⛔ Access denied: you do not have permission to view the users.';
        toast.error(error.value);
      } else if (err.response?.status === 401) {
        error.value = '🔐 Session expired. Please log in again.';
        toast.error(error.value);
      } else {
        error.value = 'An error occurred while fetching users and tokens.';
        toast.error(error.value);
      }
    } else {
      error.value = '	Unknown error.';
      toast.error(error.value);
    }
  } finally {
    loading.value = false;
  }
};

const startEditing = (user: User) => {
  editingUserId.value = user.id;
  editName.value = user.name;
  editRole.value = user.role;
  editEmail.value = '';
  editPassword.value = '';
};

const cancelEdit = () => {
  editingUserId.value = null;
  editName.value = '';
  editRole.value = '';
  editEmail.value = '';
  editPassword.value = '';
};

const submitEdit = async (userId: number) => {
  try {
    const updatePayload: any = {};
    if (editName.value) updatePayload.name = editName.value;
    if (editEmail.value) updatePayload.email = editEmail.value;
    if (editRole.value) updatePayload.role = editRole.value;
    if (editPassword.value) updatePayload.password = editPassword.value;

    await backendApi.patch(`/users/users/${userId}`, updatePayload, {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    });

    cancelEdit();
    fetchUsers();
    toast.success('User updated successfully.');
  } catch (err) {
    console.error('Update error', err);
    error.value = 'Error while updating the user.';
    if (isAxiosError(err) && err.response?.data?.detail) {
      error.value = `🚫 ${err.response.data.detail}`;
      toast.error(error.value);
    }
  }
};

const deleteUser = async (userId: number) => {
  try {
    await backendApi.delete(`/users/users/${userId}`, {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    })
    fetchUsers()
    toast.success('User deleted successfully 🗑️');
  } catch (err) {
    console.error('Error while deleting the user', err)
    error.value = 'Error while deleting the user'
    toast.error(error.value);
  }
}

const createUser = async () => {
  try {
    const userData: any = { name: newName.value };
    if (newEmail.value) userData.email = newEmail.value;
    if (newPassword.value) userData.password = newPassword.value;
    if (newRole.value) userData.role = newRole.value;

    await backendApi.post(`/users/users/`, userData, {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    });

    // Reset form
    newName.value = '';
    newEmail.value = '';
    newPassword.value = '';
    newRole.value = '';
    showCreateUser.value = false;

    await fetchUsers();
    toast.success('User created successfully.');
  } catch (err: any) {
    console.error('User creation error', err);
    if (isAxiosError(err) && err.response?.data?.detail) {
      error.value = `🚫 ${err.response.data.detail}`;
      toast.error(error.value);
    } else {
      error.value = 'An error occurred while creating the user.';
      toast.error(error.value);
    }
  }
};

watch(
  () => authStore.token,
  (newToken) => {
    if (newToken) {
      fetchUsers();
    } else {
      users.value = [];
    }
  },
  { immediate: true }
);
</script>

<template>
  <div v-if="authStore.scopes.includes('admin')">
    <div v-if="loading">Loading users...</div>

    <div v-if="users.length" class="module">
      <h2>Users</h2>
      <table>
        <thead>
          <tr>
            <th class="recoltes small" data-label="Name">Name</th>
            <th class="recoltes small" data-label="Email">Email</th>
            <th class="recoltes small" data-label="Role">Role</th>
            <th class="recoltes small" data-label="Active">Active</th>
            <th class="recoltes small" data-label="Last Session">Last Session</th>
            <th class="recoltes small" data-label="Actions"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td data-label="Name">{{ user.name.charAt(0).toUpperCase() + user.name.slice(1) }}</td>
            <td data-label="Email">{{ user.email }}</td>
            <td data-label="Role">{{ user.role }}</td>
            <td data-label="Active">
              <span v-if="user.is_active">✔️</span>
              <span v-else>❌</span>
            </td>
            <td data-label="Last Session">
              <ul v-if="user.tokens && user.tokens.length" class="token-list">
                <li v-for="token in user.tokens" :key="token.created_at">
                  <strong>{{ new Date(token.created_at).toLocaleDateString() }}</strong>
                </li>
              </ul>
              <span v-else>-</span> <!-- Fallback for empty tokens -->
            </td>
            <td v-if="editingUserId !== user.id" data-label="Actions">
              <button class="delete-btn" @click="deleteUser(user.id)">&#10060;</button>
              <button class="edit-btn" @click="startEditing(user)">&#9998;</button>
            </td>
            <td v-if="editingUserId == user.id" data-label="Edit">
              <form class="form-section" @submit.prevent>
                <input v-model="editName" placeholder="Name" class="form-input" />
                <input v-model="editEmail" placeholder="Email" class="form-input" />
                <input v-model="editPassword" placeholder="Password" class="form-input" />
                <select v-model="editRole" class="form-input">
                  <option value="admin">Admin</option>
                  <option value="editor">Editor</option>
                  <option value="player">Player</option>
                </select>
              </form>
              <button @click="submitEdit(user.id)">Save</button>
              <button @click="cancelEdit">Cancel</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <button @click="toggleCreateUserForm">
      {{ showCreateUser ? 'Cancel' : 'Add User' }}
    </button>

    <div v-if="showCreateUser" class="module">
      <h3>Add User</h3>
      <div class="input-group">
        <input v-model="newName" placeholder="Name" class="form-input" required />
        <select v-model="newRole" class="form-input">
          <option value="">Select Role</option>
          <option value="admin">Admin</option>
          <option value="editor">Editor</option>
          <option value="player">Player</option>
        </select>
        <input v-model="newEmail" type="email" placeholder="Email (optional)" class="form-input" />
        <input v-model="newPassword" type="password" placeholder="Password (optional)" class="form-input" />
        <button class="add-btn" @click="createUser">Add</button>
      </div>
    </div>

  </div>

  <div v-if="authStore.isAuthenticated && !authStore.scopes.includes('admin')">
    <div class="module module-prel">
      <p>You do not have sufficient rights to access this section</p>
    </div>
  </div>

  <div v-if="!authStore.isAuthenticated" class="centered-block">
    <h2>🔒 Login required</h2>
    <p>Please log in to access the application's features.</p>
  </div>
</template>

<style scoped>
.token-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 8px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

@media screen and (max-width: 600px) {
  thead {
    display: none;
    /* Hide table headers on mobile */
  }

  tr {
    display: block;
    margin-bottom: 1rem;
    border-bottom: 2px solid #ddd;
  }

  td {
    display: block;
    text-align: right;
    position: relative;
    padding-left: 50%;
  }

  td::before {
    content: attr(data-label);
    /* Use data-label as pseudo-header */
    position: absolute;
    left: 8px;
    width: 45%;
    font-weight: bold;
    text-align: left;
  }

  td[data-label="Actions"] {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    padding-left: 8px;
    /* Reset padding to avoid label overlap */
  }

  td[data-label="Actions"]::before {
    display: none;
    /* Remove pseudo-element for actions cell */
  }

  .delete-btn,
  .edit-btn {
    margin-left: 8px;
    /* Space between buttons */
  }

  /* Adjust edit form for mobile */
  td[data-label="Edit"] {
    display: block;
    padding-left: 50%;
  }

  .form-section,
  .token-list {
    display: block;
    width: 100%;
  }

  .form-input,
  button {
    width: 100%;
    margin-bottom: 8px;
  }
}
</style>
