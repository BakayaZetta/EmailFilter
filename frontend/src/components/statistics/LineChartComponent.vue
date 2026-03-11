<script setup>
import { ref, onMounted, watch } from 'vue';
import Chart from 'chart.js/auto';

const props = defineProps({
  chartData: {
    required: true
  },
  height: {
    type: [String, Number],
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
    type: 'line',
    data: props.chartData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: {
        legend: {
          position: 'top',
          labels: {
            usePointStyle: true,
            boxWidth: 6
          }
        },
        tooltip: {
          enabled: true,
          mode: 'index',
          intersect: false
        }
      },
      scales: {
        x: {
          title: {
            display: true,
            text: 'Date'
          },
          grid: {
            display: false
          }
        },
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Number of emails'
          },
          ticks: {
            precision: 0
          }
        }
      },
      elements: {
        line: {
          tension: 0.4 // Ajoute une courbure aux lignes
        },
        point: {
          radius: 3,
          hoverRadius: 5
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
  <div>
    <canvas :ref="el => chartRef = el" :height="height"></canvas>
  </div>
</template>
