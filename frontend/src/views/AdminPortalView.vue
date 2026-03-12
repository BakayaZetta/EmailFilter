<script setup>
import { computed, nextTick, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useToast } from 'vue-toastification';
import { useAuthStore } from '@/stores/authStore';
import adminService from '@/services/adminService';

const authStore = useAuthStore();
const router = useRouter();
const toast = useToast();

const users = ref([]);
const logs = ref([]);
const scans = ref([]);
const queuedScans = ref([]);
const loading = ref(false);
const creatingUser = ref(false);
const selectedUserProfile = ref(null);
const selectedUserId = ref(null);
const profileLoading = ref(false);

const staleThresholdMinutes = 30;

const newUserForm = ref({
  firstName: '',
  lastName: '',
  email: '',
  password: '',
  role: 'user'
});

const currentUserId = computed(() => authStore.user?.id);

const isAdmin = computed(() => {
  const role = String(authStore.user?.role || '').toLowerCase();
  return role === 'admin' || role === 'super_admin' || role === 'superadmin';
});

const fetchAdminData = async () => {
  loading.value = true;
  try {
    const [usersData, logsData, scansData, queuedScansData] = await Promise.all([
      adminService.getUsers(),
      adminService.getLogs(200),
      adminService.getScans(),
      adminService.getQueuedScans(200)
    ]);

    users.value = usersData;
    logs.value = logsData;
    scans.value = scansData;
    queuedScans.value = queuedScansData;
  } catch (error) {
    toast.error(error.response?.data?.message || 'Failed to load admin portal data');
  } finally {
    loading.value = false;
  }
};

const formatQueuedDuration = (minutes) => {
  const total = Number(minutes || 0);
  if (!Number.isFinite(total) || total <= 0) return 'just now';
  if (total < 60) return `${total} min`;

  const hours = Math.floor(total / 60);
  const mins = total % 60;
  return mins ? `${hours}h ${mins}m` : `${hours}h`;
};

const updateRole = async (user, role) => {
  try {
    await adminService.updateUserRole(user.ID_Utilisateur, role);
    user.Role = role;
    toast.success(`Role updated for ${user.Email}`);
  } catch (error) {
    toast.error(error.response?.data?.message || 'Failed to update role');
  }
};

const createUser = async () => {
  creatingUser.value = true;
  try {
    await adminService.createUser(newUserForm.value);
    toast.success(`User ${newUserForm.value.email} created`);
    newUserForm.value = {
      firstName: '',
      lastName: '',
      email: '',
      password: '',
      role: 'user'
    };
    await fetchAdminData();
  } catch (error) {
    toast.error(error.response?.data?.message || 'Failed to create user');
  } finally {
    creatingUser.value = false;
  }
};

const deactivateUser = async (user) => {
  try {
    await adminService.deactivateUser(user.ID_Utilisateur);
    user.Role = 'disabled';
    toast.success(`User ${user.Email} deactivated`);
  } catch (error) {
    toast.error(error.response?.data?.message || 'Failed to deactivate user');
  }
};

const openUserProfile = async (user) => {
  if (Number(selectedUserId.value) === Number(user.ID_Utilisateur) && selectedUserProfile.value) {
    selectedUserId.value = null;
    selectedUserProfile.value = null;
    return;
  }

  selectedUserId.value = user.ID_Utilisateur;
  profileLoading.value = true;
  try {
    selectedUserProfile.value = await adminService.getUserProfile(user.ID_Utilisateur);
    await nextTick();
    const rowElement = document.getElementById(`user-profile-row-${user.ID_Utilisateur}`);
    if (rowElement) {
      rowElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  } catch (error) {
    toast.error(error.response?.data?.message || 'Failed to load user profile');
    selectedUserId.value = null;
  } finally {
    profileLoading.value = false;
  }
};

onMounted(async () => {
  authStore.initialize();

  if (!authStore.isLoggedIn) {
    router.push('/login');
    return;
  }

  if (!isAdmin.value) {
    toast.error('Administrator access required');
    router.push('/');
    return;
  }

  await fetchAdminData();
});
</script>

<template>
  <section class="py-6 bg-gray-50 min-h-screen">
    <div class="container mx-auto px-2 md:px-4">
      <div class="max-w-6xl mx-auto space-y-6">
        <div class="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <h1 class="text-2xl font-semibold mb-1">Administrator Portal</h1>
          <p class="text-sm text-gray-500">Manage users, permissions, request logs and all scans.</p>
        </div>

        <div class="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <div class="flex justify-between items-center mb-3">
            <h2 class="text-lg font-semibold">Users & Permissions</h2>
            <button
              @click="fetchAdminData"
              class="px-3 py-1.5 text-sm rounded-md border border-gray-300 hover:bg-gray-50"
            >
              Refresh
            </button>
          </div>

          <form class="grid grid-cols-1 md:grid-cols-5 gap-2 mb-4" @submit.prevent="createUser">
            <input v-model="newUserForm.firstName" type="text" placeholder="First name" class="border border-gray-300 rounded-md px-3 py-2 text-sm" required />
            <input v-model="newUserForm.lastName" type="text" placeholder="Last name" class="border border-gray-300 rounded-md px-3 py-2 text-sm" required />
            <input v-model="newUserForm.email" type="email" placeholder="Email" class="border border-gray-300 rounded-md px-3 py-2 text-sm" required />
            <input v-model="newUserForm.password" type="password" placeholder="Password" class="border border-gray-300 rounded-md px-3 py-2 text-sm" required />
            <div class="flex gap-2">
              <select v-model="newUserForm.role" class="border border-gray-300 rounded-md px-3 py-2 text-sm w-full">
                <option value="user">user</option>
                <option value="admin">admin</option>
                <option value="super_admin">super_admin</option>
              </select>
              <button type="submit" class="px-3 py-1.5 text-sm rounded-md border border-gray-300 hover:bg-gray-50" :disabled="creatingUser">
                Create
              </button>
            </div>
          </form>

          <div class="overflow-x-auto border border-gray-200 rounded-lg">
            <table class="min-w-full text-sm bg-white">
              <thead>
                <tr class="text-left border-b bg-gray-50">
                  <th class="py-2 px-3 font-medium">ID</th>
                  <th class="py-2 px-3 font-medium">Name</th>
                  <th class="py-2 px-3 font-medium">Email</th>
                  <th class="py-2 px-3 font-medium">Role</th>
                  <th class="py-2 px-3 font-medium">Profile</th>
                  <th class="py-2 px-3 font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                <template v-for="user in users" :key="user.ID_Utilisateur">
                  <tr class="border-b">
                    <td class="py-2 px-3">{{ user.ID_Utilisateur }}</td>
                    <td class="py-2 px-3">{{ user.Prenom }} {{ user.Nom }}</td>
                    <td class="py-2 px-3">{{ user.Email }}</td>
                    <td class="py-2 px-3">
                      <select
                        class="border border-gray-300 rounded-md px-2 py-1"
                        :value="user.Role"
                        @change="updateRole(user, $event.target.value)"
                        :disabled="Number(user.ID_Utilisateur) === Number(currentUserId)"
                      >
                        <option value="user">user</option>
                        <option value="admin">admin</option>
                        <option value="super_admin">super_admin</option>
                        <option value="disabled">disabled</option>
                      </select>
                    </td>
                    <td class="py-2 px-3">
                      <button
                        @click="openUserProfile(user)"
                        class="px-2 py-1 text-xs rounded-md border border-gray-300 hover:bg-gray-50"
                      >
                        {{ Number(selectedUserId) === Number(user.ID_Utilisateur) ? 'Hide profile' : 'View profile' }}
                      </button>
                    </td>
                    <td class="py-2 px-3 text-gray-500 flex items-center gap-2">
                      <span v-if="Number(user.ID_Utilisateur) === Number(currentUserId)">Current account</span>
                      <button
                        v-else
                        @click="deactivateUser(user)"
                        class="px-2 py-1 text-xs rounded-md border border-red-300 text-red-600 hover:bg-red-50"
                      >
                        Deactivate
                      </button>
                    </td>
                  </tr>
                  <tr
                    v-if="Number(selectedUserId) === Number(user.ID_Utilisateur)"
                    :id="`user-profile-row-${user.ID_Utilisateur}`"
                    class="bg-gray-50 border-b"
                  >
                    <td colspan="6" class="py-3 px-3">
                      <p v-if="profileLoading" class="text-sm text-gray-500">Loading profile...</p>
                      <div v-else-if="selectedUserProfile" class="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                        <p><strong>Name:</strong> {{ selectedUserProfile.Prenom }} {{ selectedUserProfile.Nom }}</p>
                        <p><strong>Email:</strong> {{ selectedUserProfile.Email }}</p>
                        <p><strong>Role:</strong> {{ selectedUserProfile.Role }}</p>
                        <p><strong>Created At:</strong> {{ selectedUserProfile.created_at || 'N/A' }}</p>
                        <p><strong>Last Login:</strong> {{ selectedUserProfile.last_login_at || 'Never' }}</p>
                        <p><strong>Scans Done:</strong> {{ selectedUserProfile.scan_count }}</p>
                        <p><strong>Last Scan:</strong> {{ selectedUserProfile.last_scan_at || 'N/A' }}</p>
                      </div>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
        </div>

        <div class="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <div class="flex justify-between items-center mb-3">
            <h2 class="text-lg font-semibold">Queued Scan Jobs</h2>
            <span class="text-xs px-2 py-1 rounded-full border border-amber-300 bg-amber-50 text-amber-700">
              {{ queuedScans.length }} pending
            </span>
          </div>
          <div class="overflow-x-auto max-h-80 border border-gray-200 rounded-lg">
            <table class="min-w-full text-sm">
              <thead>
                <tr class="text-left border-b bg-gray-50">
                  <th class="py-2 px-3 font-medium">Mail ID</th>
                  <th class="py-2 px-3 font-medium">Subject</th>
                  <th class="py-2 px-3 font-medium">Sender</th>
                  <th class="py-2 px-3 font-medium">User ID</th>
                  <th class="py-2 px-3 font-medium">Queued For</th>
                  <th class="py-2 px-3 font-medium">Received</th>
                  <th class="py-2 px-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="queuedScans.length === 0">
                  <td colspan="7" class="py-4 px-3 text-center text-gray-500">No queued jobs at the moment.</td>
                </tr>
                <tr v-for="scan in queuedScans" :key="`queued-${scan.ID_Mail}`" class="border-b">
                  <td class="py-2 px-3">{{ scan.ID_Mail }}</td>
                  <td class="py-2 px-3">{{ scan.Sujet }}</td>
                  <td class="py-2 px-3">{{ scan.Emetteur || 'N/A' }}</td>
                  <td class="py-2 px-3">{{ scan.ID_Utilisateur }}</td>
                  <td class="py-2 px-3">
                    <span
                      :class="Number(scan.queued_minutes || 0) >= staleThresholdMinutes
                        ? 'text-red-600 font-semibold'
                        : 'text-gray-700'"
                    >
                      {{ formatQueuedDuration(scan.queued_minutes) }}
                    </span>
                  </td>
                  <td class="py-2 px-3">{{ scan.Date_Reception }}</td>
                  <td class="py-2 px-3">
                    <span class="text-xs px-2 py-1 rounded-full border border-amber-300 bg-amber-50 text-amber-700">
                      {{ scan.Statut }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <h2 class="text-lg font-semibold mb-3">Recent Request Logs</h2>
          <div class="overflow-x-auto max-h-72 border border-gray-200 rounded-lg">
            <table class="min-w-full text-sm">
              <thead>
                <tr class="text-left border-b bg-gray-50">
                  <th class="py-2 px-3 font-medium">Time</th>
                  <th class="py-2 px-3 font-medium">Level</th>
                  <th class="py-2 px-3 font-medium">Method</th>
                  <th class="py-2 px-3 font-medium">URL</th>
                  <th class="py-2 px-3 font-medium">Status</th>
                  <th class="py-2 px-3 font-medium">Duration</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(entry, index) in logs" :key="`${entry.timestamp}-${index}`" class="border-b">
                  <td class="py-2 px-3">{{ entry.timestamp }}</td>
                  <td class="py-2 px-3">{{ entry.level }}</td>
                  <td class="py-2 px-3">{{ entry.method }}</td>
                  <td class="py-2 px-3">{{ entry.url }}</td>
                  <td class="py-2 px-3">{{ entry.statusCode }}</td>
                  <td class="py-2 px-3">{{ entry.duration }}ms</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <h2 class="text-lg font-semibold mb-3">All Scans</h2>
          <div class="overflow-x-auto max-h-96 border border-gray-200 rounded-lg">
            <table class="min-w-full text-sm">
              <thead>
                <tr class="text-left border-b bg-gray-50">
                  <th class="py-2 px-3 font-medium">Mail ID</th>
                  <th class="py-2 px-3 font-medium">Subject</th>
                  <th class="py-2 px-3 font-medium">Sender</th>
                  <th class="py-2 px-3 font-medium">User ID</th>
                  <th class="py-2 px-3 font-medium">Status</th>
                  <th class="py-2 px-3 font-medium">Received</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="scan in scans" :key="scan.ID_Mail" class="border-b">
                  <td class="py-2 px-3">{{ scan.ID_Mail }}</td>
                  <td class="py-2 px-3">{{ scan.Sujet }}</td>
                  <td class="py-2 px-3">{{ scan.Emetteur }}</td>
                  <td class="py-2 px-3">{{ scan.ID_Utilisateur }}</td>
                  <td class="py-2 px-3">{{ scan.Statut }}</td>
                  <td class="py-2 px-3">{{ scan.Date_Reception }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <p v-if="loading" class="text-sm text-gray-500">Loading portal data...</p>
      </div>
    </div>
  </section>
</template>
