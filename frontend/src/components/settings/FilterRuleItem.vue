<script setup>
import { defineProps, defineEmits } from 'vue';

const props = defineProps({
  rule: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(['edit', 'delete']);

// Format date in local format
const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleString();
};

// Determine blocked address (priority: email, domain, IP)
const blockedAddress = () => {
  if (props.rule.Email && props.rule.Email.trim()) {
    return props.rule.Email;
  } else if (props.rule.Domain && props.rule.Domain.trim()) {
    return props.rule.Domain + ' (domain)';
  } else if (props.rule.IP && props.rule.IP.trim()) {
    return props.rule.IP + ' (IP)';
  } else {
    return 'Invalid rule';
  }
};
</script>

<template>
  <li class="hover:bg-gray-50 transition-colors border-b border-gray-200 last:border-b-0">
    <div class="p-4 sm:px-6 flex justify-between items-center">
      <div>
        <!-- Blocked address -->
        <div class="font-medium text-gray-900">{{ blockedAddress() }}</div>

        <!-- Date added -->
        <div class="text-sm text-gray-500 mt-1">
          Added on {{ formatDate(rule.created_at) }}
        </div>
      </div>

      <!-- Action buttons -->
      <div class="flex space-x-2">
        <button
          @click="emit('edit', rule)"
          class="p-1.5 text-blue-600 hover:bg-blue-50 rounded transition-colors"
          title="Edit"
        >
          <i class="pi pi-pencil"></i>
        </button>

        <button
          @click="emit('delete', rule.ID_Blacklist)"
          class="p-1.5 text-red-600 hover:bg-red-50 rounded transition-colors"
          title="Delete"
        >
          <i class="pi pi-trash"></i>
        </button>
      </div>
    </div>
  </li>
</template>
