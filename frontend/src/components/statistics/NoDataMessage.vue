<script setup>
const props = defineProps({
  message: {
    type: String,
    default: 'No data available for the selected period'
  },
  icon: {
    type: String,
    default: 'pi-chart-bar'
  }
});
</script>

<template>
  <div class="flex flex-col items-center justify-center py-12 text-gray-500">
    <i :class="['pi', icon, 'text-4xl mb-4']"></i>
    <p>{{ message }}</p>
  </div>
</template>
