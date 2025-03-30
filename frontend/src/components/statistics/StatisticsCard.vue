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
  },
  tooltip: {
    type: String,
    default: null
  }
});
</script>

<template>
  <div class="bg-white rounded-lg shadow-sm p-5 relative group">
    <!-- Tooltip -->
    <div v-if="tooltip" class="absolute z-10 left-1/2 transform -translate-x-1/2 -translate-y-[120%] opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-opacity duration-300 bg-gray-800 text-white text-xs rounded px-2 py-1 w-52 text-center">
      {{ tooltip }}
      <div class="absolute left-1/2 transform -translate-x-1/2 top-full w-2 h-2 bg-gray-800 rotate-45"></div>
    </div>

    <div class="flex items-center">
      <!-- Cercle avec dimensions fixes et centrage -->
      <div :class="[color, 'rounded-full w-10 h-10 flex items-center justify-center text-white']">
        <i :class="['pi', icon]"></i>
      </div>
      <div class="ml-5">
        <div class="flex items-center">
          <h3 class="text-gray-500 text-sm font-medium">{{ title }}</h3>
          <i v-if="tooltip" class="pi pi-info-circle text-gray-400 text-xs ml-1"></i>
        </div>
        <p class="text-2xl font-bold">{{ value }}</p>
      </div>
    </div>
  </div>
</template>
