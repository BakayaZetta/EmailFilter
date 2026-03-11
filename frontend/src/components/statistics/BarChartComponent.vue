<script setup>
import { ref, onMounted, watch } from 'vue';
import Chart from 'chart.js/auto';

const props = defineProps({
  chartData: {
    type: Object,
    required: true
  },
  height: {
    type: Number,
    default: 400
  }
});

const chartRef = ref(null);
let chart = null;

const createChart = () => {
  if (!chartRef.value) return;

  const ctx = chartRef.value.getContext('2d');

  if (chart) {
    chart.destroy();
  }

  chart = new Chart(ctx, {
    type: 'bar',
    data: props.chartData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          }
        },
        y: {
          beginAtZero: true,
          ticks: {
            precision: 0
          }
        }
      }
    }
  });
};

onMounted(() => {
  createChart();
});

watch(() => props.chartData, () => {
  createChart();
}, { deep: true });
</script>

<template>
  <div class="relative">
    <canvas :ref="el => chartRef = el" :height="height"></canvas>
  </div>
</template>
