<script setup>
import { ref, computed, defineProps, defineEmits } from 'vue';
import api from '@/services/api';

const props = defineProps({
  rule: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['close', 'saved']);

// Form state
const senderEmail = ref(props.rule ? props.rule.Email || '' : '');
const processing = ref(false);
const errors = ref({});

// Determine if in edit mode
const isEditMode = computed(() => !!props.rule);

// Validate email
const validateEmail = (email) => {
  const re = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
  return re.test(String(email).toLowerCase());
};

// Validate form
const validateForm = () => {
  errors.value = {};

  if (!senderEmail.value.trim()) {
    errors.value.senderEmail = "Email address is required";
    return false;
  }

  if (!validateEmail(senderEmail.value)) {
    errors.value.senderEmail = "Invalid email address format";
    return false;
  }

  return true;
};

// Submit form
const submitForm = async () => {
  if (!validateForm()) return;

  processing.value = true;

  try {
    if (isEditMode.value) {
      // Edit mode
      await api.put(`/filter-rules/${props.rule.ID_Blacklist}`, {
        sender_email: senderEmail.value
      });
    } else {
      // Add mode
      await api.post('/filter-rules', {
        sender_email: senderEmail.value
      });
    }

    emit('saved');
  } catch (error) {
    console.error('Error saving filter rule:', error);
    errors.value.form = "An error occurred. Please try again.";
  } finally {
    processing.value = false;
  }
};
</script>

<template>
  <div class="flex flex-col transform transition-all duration-300 overflow-hidden">
    <!-- Form header -->
    <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
      <h3 class="text-lg font-medium text-gray-900">{{ isEditMode ? 'Edit Blocked Sender' : 'Block New Sender' }}</h3>
      <button @click="emit('close')" class="text-gray-400 hover:text-gray-500">
        <i class="pi pi-times"></i>
      </button>
    </div>

    <!-- Form body -->
    <div class="px-6 py-4 overflow-y-auto flex-grow">
      <form @submit.prevent="submitForm">
        <!-- General form error -->
        <div v-if="errors.form" class="mb-4 bg-red-50 border border-red-200 text-red-700 p-3 rounded-md text-sm">
          {{ errors.form }}
        </div>

        <!-- Email address field -->
        <div class="mb-4">
          <label for="senderEmail" class="block text-sm font-medium text-gray-700 mb-1">
            Sender Email Address
          </label>
          <input
            id="senderEmail"
            v-model="senderEmail"
            type="email"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            :class="{'border-red-500': errors.senderEmail}"
            placeholder="example@domain.com"
          />
          <p v-if="errors.senderEmail" class="mt-1 text-sm text-red-600">
            {{ errors.senderEmail }}
          </p>
          <p class="mt-1 text-xs text-gray-500">
            All emails from this address will be automatically blocked.
          </p>
        </div>
      </form>
    </div>

    <!-- Form footer -->
    <div class="px-6 py-4 border-t border-gray-200 flex justify-end space-x-2">
      <button
        type="button"
        @click="emit('close')"
        class="px-3 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 text-sm"
        :disabled="processing"
      >
        Cancel
      </button>

      <button
        type="button"
        @click="submitForm"
        class="px-3 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 flex items-center text-sm"
        :disabled="processing"
      >
        <i v-if="processing" class="pi pi-spin pi-spinner mr-1"></i>
        {{ isEditMode ? 'Update' : 'Block Sender' }}
      </button>
    </div>
  </div>
</template>
