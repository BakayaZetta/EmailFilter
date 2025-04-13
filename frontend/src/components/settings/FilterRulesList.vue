<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import FilterRuleItem from './FilterRuleItem.vue';
import FilterRulesForm from './FilterRulesForm.vue';
import api from '@/services/api';

// Définir les émissions pour communiquer avec le parent
const emit = defineEmits(['rule-added', 'rule-updated', 'rule-deleted', 'rule-error']);

// States
const filterRules = ref([]);
const loading = ref(false);
const error = ref(null);

// Form states
const showForm = ref(false);
const editingRule = ref(null);
const modalRef = ref(null);

// Load filtering rules
const loadFilterRules = async () => {
  try {
    loading.value = true;
    error.value = null;
    const response = await api.get('/filter-rules');
    filterRules.value = response.data;
  } catch (err) {
    console.error('Failed to load filter rules:', err);
    error.value = "Error loading filtering rules";
    emit('rule-error', "Error loading filtering rules");
  } finally {
    loading.value = false;
  }
};

// Delete a rule
const deleteRule = async (ruleId) => {
  if (!confirm('Are you sure you want to delete this filtering rule?')) {
    return;
  }

  try {
    await api.delete(`/filter-rules/${ruleId}`);
    // Update the list
    filterRules.value = filterRules.value.filter(rule => rule.ID_Blacklist !== ruleId);
    // Émettre l'événement de suppression
    emit('rule-deleted');
  } catch (err) {
    console.error('Failed to delete rule:', err);
    const errorMessage = err.response?.data?.message || "Error deleting rule";
    emit('rule-error', errorMessage);
  }
};

// Open add form
const openAddForm = () => {
  editingRule.value = null;
  showForm.value = true;
};

// Open edit form
const openEditForm = (rule) => {
  editingRule.value = { ...rule };
  showForm.value = true;
};

// Close form
const closeForm = () => {
  showForm.value = false;
  setTimeout(() => {
    editingRule.value = null;
  }, 200);
};

// After form save
const handleSaved = (isEdit) => {
  loadFilterRules();
  closeForm();

  // Émettre l'événement approprié
  if (isEdit) {
    emit('rule-updated');
  } else {
    emit('rule-added');
  }
};

// Handle Escape key press
const handleEscape = (e) => {
  if (e.key === 'Escape' && showForm.value) {
    closeForm();
  }
};

// Handle click outside modal
const handleOutsideClick = (e) => {
  if (modalRef.value && showForm.value && !modalRef.value.contains(e.target)) {
    closeForm();
  }
};

// Setup event listeners
onMounted(() => {
  // Add global event listeners
  document.addEventListener('keydown', handleEscape);
  document.addEventListener('mousedown', handleOutsideClick);

  // Load data
  loadFilterRules();
});

// Cleanup event listeners
onUnmounted(() => {
  document.removeEventListener('keydown', handleEscape);
  document.removeEventListener('mousedown', handleOutsideClick);
});
</script>

<template>
  <div class="bg-white rounded-lg shadow-md overflow-hidden">
    <!-- Header with add button -->
    <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
      <h3 class="text-lg font-medium text-gray-900">Blocked Senders</h3>
      <button
        @click="openAddForm"
        class="px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-md flex items-center text-sm"
      >
        <i class="pi pi-plus mr-1"></i>
        Block Sender
      </button>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="p-8 flex justify-center">
      <div class="flex flex-col items-center">
        <i class="pi pi-spin pi-spinner text-2xl text-gray-400 mb-2"></i>
        <p class="text-gray-500 text-sm">Loading rules...</p>
      </div>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="p-6">
      <div class="bg-red-50 border border-red-200 text-red-600 p-4 rounded-md text-sm">
        <div class="flex">
          <i class="pi pi-exclamation-circle text-xl mr-2"></i>
          <div>
            <p class="font-medium">An error occurred</p>
            <p class="mt-1">{{ error }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else-if="filterRules.length === 0" class="p-8 text-center">
      <div class="flex flex-col items-center">
        <i class="pi pi-shield text-3xl text-gray-300 mb-2"></i>
        <p class="text-base font-medium text-gray-700 mb-1">No blocked senders</p>
        <p class="text-sm text-gray-500 mb-4">Add email addresses to block unwanted messages.</p>
        <button
          @click="openAddForm"
          class="px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-md flex items-center"
        >
          <i class="pi pi-plus mr-1"></i>
          Block Sender
        </button>
      </div>
    </div>

    <!-- List of rules -->
    <div v-else>
      <ul class="divide-y divide-gray-200">
        <FilterRuleItem
          v-for="rule in filterRules"
          :key="rule.ID_Blacklist"
          :rule="rule"
          @edit="openEditForm"
          @delete="deleteRule"
        />
      </ul>
    </div>

    <!-- Modal with form - Updated to match FileDropZone style -->
    <div
      v-if="showForm"
      class="fixed inset-0 bg-opacity-20 backdrop-blur-sm z-50 flex items-center justify-center p-4 transition-opacity duration-300"
    >
      <div
        ref="modalRef"
        class="bg-white rounded-lg shadow-2xl w-full max-w-md overflow-hidden flex flex-col transform transition-all duration-300 scale-in-center border border-gray-100"
        style="box-shadow: rgba(17, 12, 46, 0.15) 0px 48px 100px 0px;"
      >
        <FilterRulesForm
          :rule="editingRule"
          @close="closeForm"
          @saved="handleSaved(!!editingRule)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Animation d'entrée pour la modal */
.scale-in-center {
  animation: scale-in-center 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
}

@keyframes scale-in-center {
  0% {
    transform: scale(0.9);
    opacity: 0.8;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
