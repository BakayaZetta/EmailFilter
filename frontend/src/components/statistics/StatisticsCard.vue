<script setup>
const props = defineProps({
  title: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    required: true
  },
  icon: {
    type: String,
    default: 'pi-chart-bar'
  },
  color: {
    type: String,
    default: 'bg-blue-500'
  }
});
</script>

<template>
  <div class="bg-white rounded-lg shadow-sm p-5">
    <div class="flex items-center">
      <div :class="[color, 'rounded-full p-3 text-white']">
        <i :class="['pi', icon]"></i>
      </div>
      <div class="ml-5">
        <h3 class="text-gray-500 text-sm font-medium">{{ title }}</h3>
        <p class="text-2xl font-bold">{{ value }}</p>
      </div>
    </div>
  </div>
</template>
