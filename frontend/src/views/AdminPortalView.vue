<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useToast } from 'vue-toastification';
import { useAuthStore } from '@/stores/authStore';
import adminService from '@/services/adminService';

const authStore = useAuthStore();
const router = useRouter();
const toast = useToast();

const users = ref([]);
const scans = ref([]);
const queuedDbScans = ref([]);
const queuedLiveScans = ref([]);
const loading = ref(false);
const creatingUser = ref(false);
const clearingQueued = ref(false);
const selectedUserProfile = ref(null);
const selectedUserId = ref(null);
const profileLoading = ref(false);
const pollIntervalId = ref(null);

const staleThresholdMinutes = 30;

const sections = ref({
  users: true,
  queued: true,
  scans: true,
});

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

const queuedCount = computed(() => queuedDbScans.value.length + queuedLiveScans.value.length);

const combinedQueuedRows = computed(() => {
  const dbRows = queuedDbScans.value.map((scan) => ({
    source: 'db',
    key: `db-${scan.ID_Mail}`,
    jobId: scan.ID_Mail,
    name: scan.Sujet,
    sender: scan.Emetteur || 'N/A',
    userId: scan.ID_Utilisateur,
    queuedMinutes: Number(scan.queued_minutes || 0),
    status: scan.Statut,
    updatedOrReceived: scan.Date_Reception,
  }));

  const liveRows = queuedLiveScans.value.map((job) => ({
    source: 'live',
    key: `live-${job.request_id}`,
    jobId: job.request_id,
    name: job.filename || 'upload.eml',
    sender: 'N/A',
    userId: 'N/A',
    queuedMinutes: Number(job.queued_minutes || 0),
    status: job.live_status || job.status || 'queued',
    updatedOrReceived: job.updated_at || 'N/A',
  }));

  return [...liveRows, ...dbRows].sort((a, b) => Number(b.queuedMinutes || 0) - Number(a.queuedMinutes || 0));
});

const sectionLabel = (isOpen) => (isOpen ? 'Collapse' : 'Expand');

const toggleSection = (name) => {
  sections.value[name] = !sections.value[name];
};

const fetchAdminData = async () => {
  loading.value = true;
  try {
    const [usersData, scansData, queuedPayload] = await Promise.all([
      adminService.getUsers(),
      adminService.getScans(),
      adminService.getQueuedScans(200)
    ]);

    users.value = usersData;
    scans.value = scansData;
    queuedDbScans.value = Array.isArray(queuedPayload?.dbQueued) ? queuedPayload.dbQueued : [];
    queuedLiveScans.value = Array.isArray(queuedPayload?.liveQueued) ? queuedPayload.liveQueued : [];
  } catch (error) {
    toast.error(error.response?.data?.message || 'Failed to load admin portal data');
  } finally {
    loading.value = false;
  }
};

const fetchQueuedScansOnly = async () => {
  try {
    const queuedPayload = await adminService.getQueuedScans(200);
    queuedDbScans.value = Array.isArray(queuedPayload?.dbQueued) ? queuedPayload.dbQueued : [];
    queuedLiveScans.value = Array.isArray(queuedPayload?.liveQueued) ? queuedPayload.liveQueued : [];
  } catch (error) {
    // Silently fail to avoid toast spam during polling
    console.error('Failed to poll queued scans:', error);
  }
};

const startQueuedScansPolling = () => {
  if (pollIntervalId.value) {
    clearInterval(pollIntervalId.value);
  }
  // Poll every 2 seconds only if there are queued jobs
  pollIntervalId.value = setInterval(async () => {
    if (queuedCount.value > 0) {
      await fetchQueuedScansOnly();
    }
  }, 2000);
};

const stopQueuedScansPolling = () => {
  if (pollIntervalId.value) {
    clearInterval(pollIntervalId.value);
    pollIntervalId.value = null;
  }
};

const clearPendingJobs = async () => {
  if (!confirm('Clear all DB pending jobs (Analyse_pending)? This will mark them as ERROR.')) {
    return;
  }

  clearingQueued.value = true;
  try {
    const result = await adminService.clearQueuedScans();
    toast.success(`Cleared ${result?.clearedCount || 0} pending job(s)`);
    await fetchQueuedScansOnly();
  } catch (error) {
    toast.error(error.response?.data?.message || 'Failed to clear pending jobs');
  } finally {
    clearingQueued.value = false;
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
  startQueuedScansPolling();
});

onUnmounted(() => {
  stopQueuedScansPolling();
});
</script>

<template>
  <section class="py-6 bg-gray-50 min-h-screen">
    <div class="container mx-auto px-2 md:px-4">
      <div class="max-w-6xl mx-auto space-y-6">
        <div class="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <h1 class="text-2xl font-semibold mb-1">Administrator Portal</h1>
          <p class="text-sm text-gray-500">Manage users, permissions, and scan queues.</p>
        </div>

        <div class="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <div class="flex justify-between items-center mb-3">
            <h2 class="text-lg font-semibold">Users & Permissions</h2>
            <div class="flex gap-2">
              <button
                @click="toggleSection('users')"
                class="px-3 py-1.5 text-sm rounded-md border border-gray-300 hover:bg-gray-50"
              >
                {{ sectionLabel(sections.users) }}
              </button>
              <button
                @click="fetchAdminData"
                class="px-3 py-1.5 text-sm rounded-md border border-gray-300 hover:bg-gray-50"
              >
                Refresh
              </button>
            </div>
          </div>

          <template v-if="sections.users">
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
          </template>
        </div>

        <div class="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <div class="flex justify-between items-center mb-3">
            <div class="flex items-center gap-2">
              <h2 class="text-lg font-semibold">Queued Scan Jobs</h2>
              <div v-if="queuedCount > 0" class="flex items-center gap-1 text-xs px-2 py-1 rounded-full border border-green-300 bg-green-50 text-green-700">
                <span class="inline-block w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                Live
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs px-2 py-1 rounded-full border border-amber-300 bg-amber-50 text-amber-700">
                {{ queuedCount }} pending
              </span>
              <button
                @click="clearPendingJobs"
                :disabled="clearingQueued"
                class="px-3 py-1.5 text-sm rounded-md border border-red-300 text-red-600 hover:bg-red-50 disabled:opacity-60"
              >
                Clear Pending
              </button>
              <button
                @click="toggleSection('queued')"
                class="px-3 py-1.5 text-sm rounded-md border border-gray-300 hover:bg-gray-50"
              >
                {{ sectionLabel(sections.queued) }}
              </button>
            </div>
          </div>

          <div v-if="sections.queued" class="overflow-x-auto max-h-80 border border-gray-200 rounded-lg">
            <table class="min-w-full text-sm">
              <thead>
                <tr class="text-left border-b bg-gray-50">
                  <th class="py-2 px-3 font-medium">Source</th>
                  <th class="py-2 px-3 font-medium">Job ID</th>
                  <th class="py-2 px-3 font-medium">Subject / File</th>
                  <th class="py-2 px-3 font-medium">Sender</th>
                  <th class="py-2 px-3 font-medium">User ID</th>
                  <th class="py-2 px-3 font-medium">Queued For</th>
                  <th class="py-2 px-3 font-medium">Status</th>
                  <th class="py-2 px-3 font-medium">Updated / Received</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="combinedQueuedRows.length === 0">
                  <td colspan="8" class="py-4 px-3 text-center text-gray-500">No queued jobs at the moment.</td>
                </tr>
                <tr v-for="row in combinedQueuedRows" :key="row.key" class="border-b">
                  <td class="py-2 px-3">
                    <span
                      class="text-xs px-2 py-1 rounded-full border"
                      :class="row.source === 'live' ? 'border-blue-300 bg-blue-50 text-blue-700' : 'border-amber-300 bg-amber-50 text-amber-700'"
                    >
                      {{ row.source === 'live' ? 'LIVE' : 'DB' }}
                    </span>
                  </td>
                  <td class="py-2 px-3">{{ row.jobId }}</td>
                  <td class="py-2 px-3">{{ row.name }}</td>
                  <td class="py-2 px-3">{{ row.sender }}</td>
                  <td class="py-2 px-3">{{ row.userId }}</td>
                  <td class="py-2 px-3">
                    <span
                      :class="Number(row.queuedMinutes || 0) >= staleThresholdMinutes
                        ? 'text-red-600 font-semibold'
                        : 'text-gray-700'"
                    >
                      {{ formatQueuedDuration(row.queuedMinutes) }}
                    </span>
                  </td>
                  <td class="py-2 px-3">{{ row.status }}</td>
                  <td class="py-2 px-3">{{ row.updatedOrReceived }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <div class="flex justify-between items-center mb-3">
            <h2 class="text-lg font-semibold">All Scans</h2>
            <button
              @click="toggleSection('scans')"
              class="px-3 py-1.5 text-sm rounded-md border border-gray-300 hover:bg-gray-50"
            >
              {{ sectionLabel(sections.scans) }}
            </button>
          </div>

          <div v-if="sections.scans" class="overflow-x-auto max-h-96 border border-gray-200 rounded-lg">
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
