<script setup>
import { ref, reactive, watch, computed } from 'vue';

const props = defineProps({
  statusOptions: {
    type: Array,
    default: () => []
  },
  initialQuery: {
    type: Object,
    default: () => ({
      status: '',
      sender: '',
      recipient: '',
      subject: '',
      dateFrom: '',
      dateTo: ''
    })
  }
});

const emit = defineEmits(['search', 'reset']);

const showAdvanced = ref(false);
const searchForm = reactive({ ...props.initialQuery });
const searchTimeout = ref(null);

// Surveiller les changements dans les critères de recherche initiaux
watch(() => props.initialQuery, (newQuery) => {
  Object.assign(searchForm, newQuery);
}, { deep: true });

// Exécuter la recherche avec un délai pour éviter trop de requêtes pendant la saisie
const debounceSearch = () => {
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value);
  }

  searchTimeout.value = setTimeout(() => {
    emit('search', { ...searchForm });
  }, 300); // 300ms de délai
};

// Exécuter la recherche immédiatement
const executeSearch = () => {
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value);
  }
  emit('search', { ...searchForm });
};

// Réinitialiser la recherche
const resetSearch = () => {
  Object.keys(searchForm).forEach(key => {
    searchForm[key] = '';
  });
  emit('reset');
};

// Observer les changements sur les champs pour recherche automatique
watch(
  () => searchForm.status,
  () => executeSearch()
);

// Ajouter des observateurs avec délai sur les champs textuels
watch(
  () => searchForm.subject,
  () => debounceSearch()
);

watch(
  () => searchForm.sender,
  () => debounceSearch()
);

watch(
  () => searchForm.recipient,
  () => debounceSearch()
);

watch(
  [() => searchForm.dateFrom, () => searchForm.dateTo],
  () => executeSearch(),
  { deep: true }
);

// Computed pour vérifier s'il y a des filtres actifs
const hasActiveFilters = computed(() => {
  return Object.values(searchForm).some(value => value !== '');
});

// Computed pour compter le nombre de filtres actifs
const activeFilterCount = computed(() => {
  return Object.values(searchForm).filter(value => value !== '').length;
});
</script>

<template>
  <div class="bg-white border rounded-lg p-3 mb-4 shadow-sm">
    <div class="flex flex-col space-y-3">
      <!-- Recherche simple -->
      <div class="flex items-center">
        <div class="flex-1">
          <div class="relative">
            <input
              v-model="searchForm.subject"
              type="text"
              placeholder="Search by subject..."
              class="block w-full border border-gray-300 rounded-md pl-10 pr-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              @keyup.enter="executeSearch"
            />
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <i class="pi pi-search text-gray-400"></i>
            </div>
          </div>
        </div>
        <div class="ml-2">
          <button
            type="button"
            @click="showAdvanced = !showAdvanced"
            class="px-3 py-2 bg-gray-100 text-gray-700 hover:bg-gray-200 rounded-md text-sm flex items-center relative"
            :class="{ 'bg-blue-50 text-blue-700': hasActiveFilters }"
          >
            <i class="pi" :class="showAdvanced ? 'pi-angle-up' : 'pi-angle-down'"></i>
            <span class="ml-2">{{ showAdvanced ? 'Hide filters' : 'More filters' }}</span>
            <span
              v-if="hasActiveFilters && !showAdvanced"
              class="absolute top-0 right-0 transform -translate-y-1/2 translate-x-1/2 bg-blue-500 text-white rounded-full w-4 h-4 flex items-center justify-center text-xs"
            >
              {{ activeFilterCount }}
            </span>
          </button>
        </div>
      </div>

      <!-- Recherche avancée -->
      <div v-if="showAdvanced" class="space-y-3 border-t pt-3">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <!-- Statut -->
          <div>
            <label for="status" class="block text-xs font-medium text-gray-700 mb-1">Status</label>
            <select
              id="status"
              v-model="searchForm.status"
              class="block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Any status</option>
              <option v-for="status in props.statusOptions" :key="status" :value="status">
                {{ status }}
              </option>
            </select>
          </div>

          <!-- Expéditeur -->
          <div>
            <label for="sender" class="block text-xs font-medium text-gray-700 mb-1">Sender</label>
            <input
              id="sender"
              v-model="searchForm.sender"
              type="text"
              placeholder="Email address"
              class="block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <!-- Destinataire -->
          <div>
            <label for="recipient" class="text-xs font-medium text-gray-700 mb-1 flex items-center">
              Recipient
              <span class="ml-1 group relative">
                <i class="pi pi-question-circle text-gray-400 text-xs cursor-help"></i>
                <span class="absolute bottom-full left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded py-1 px-2 w-48 hidden group-hover:block z-10">
                  Search by recipient's user ID or email address
                </span>
              </span>
            </label>
            <input
              id="recipient"
              v-model="searchForm.recipient"
              type="text"
              placeholder="User ID or email address"
              class="block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <!-- Sujet (déjà présent dans la recherche simple) -->
          <div>
            <label for="subject" class="block text-xs font-medium text-gray-700 mb-1">Subject</label>
            <input
              id="subject"
              v-model="searchForm.subject"
              type="text"
              placeholder="Email subject"
              class="block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <!-- Date (de) -->
          <div>
            <label for="dateFrom" class="block text-xs font-medium text-gray-700 mb-1">From date</label>
            <input
              id="dateFrom"
              v-model="searchForm.dateFrom"
              type="date"
              class="block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <!-- Date (à) -->
          <div>
            <label for="dateTo" class="block text-xs font-medium text-gray-700 mb-1">To date</label>
            <input
              id="dateTo"
              v-model="searchForm.dateTo"
              type="date"
              class="block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        <div class="flex justify-end space-x-2">
          <button
            type="button"
            @click="resetSearch"
            class="px-4 py-2 border border-gray-300 text-gray-700 hover:bg-gray-50 rounded-md text-sm"
          >
            Clear filters
          </button>
          <button
            type="button"
            @click="executeSearch"
            class="px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded-md text-sm"
          >
            Apply filters
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
