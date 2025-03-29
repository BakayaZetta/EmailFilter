<script setup>
import { ref, onMounted, computed } from 'vue';
import { useAuthStore } from '@/stores/authStore';
import { useRouter } from 'vue-router';
import statisticsService from '@/services/statisticsService';
import StatisticsCard from '@/components/statistics/StatisticsCard.vue';
import LineChartComponent from '@/components/statistics/LineChartComponent.vue';
import PieChartComponent from '@/components/statistics/PieChartComponent.vue';
import BarChartComponent from '@/components/statistics/BarChartComponent.vue';
import NoDataMessage from '@/components/statistics/NoDataMessage.vue';

const router = useRouter();
const authStore = useAuthStore();
const loading = ref(true);
const error = ref(null);
const statistics = ref({
  totalMails: 0,
  mailsByStatus: {},
  threatsByCategory: {},
  mailsOverTime: [],
  topSenders: [],
  detectRatio: 0
});

// Période de temps sélectionnée
const timePeriod = ref('month'); // 'week', 'month', 'year', 'all'

// Charger les statistiques depuis l'API
const loadStatistics = async () => {
  loading.value = true;
  error.value = null;

  try {
    // Utiliser le service dédié au lieu de l'API directement
    statistics.value = await statisticsService.getStatistics(timePeriod.value);
  } catch (err) {
    console.error('Failed to load statistics:', err);
    error.value = 'Failed to load statistics. Please try again later.';
  } finally {
    loading.value = false;
  }
};

// Calculer le pourcentage de menaces
const threatPercentage = computed(() => {
  const total = statistics.value.totalMails;
  if (!total) return 0;

  const threats = (statistics.value.mailsByStatus?.QUARANTINE || 0) +
                  (statistics.value.mailsByStatus?.ERROR || 0);

  return Math.round((threats / total) * 100);
});

// Formater les données pour le graphique circulaire de statuts
const statusChartData = computed(() => {
  const statuses = statistics.value.mailsByStatus || {};
  const statusColors = {
    'SAFE': '#10B981',     // green
    'ERROR': '#EF4444',    // red
    'QUARANTINE': '#F59E0B', // yellow
    'PASS': '#6366F1',     // indigo
    'DELETED': '#9CA3AF',  // gray
    'UNKNOWN': '#6B7280'   // gray-500
  };

  const labels = Object.keys(statuses).map(status => status.charAt(0) + status.slice(1).toLowerCase());
  const data = Object.values(statuses);
  const backgroundColor = Object.keys(statuses).map(status => statusColors[status] || '#6B7280');

  return {
    labels: labels,
    datasets: [{
      data: data,
      backgroundColor: backgroundColor
    }]
  };
});

// Formater les données pour le graphique à barres des principaux expéditeurs
const topSendersChartData = computed(() => {
  const senders = statistics.value.topSenders || [];
  return {
    labels: senders.map(sender => sender.email),
    datasets: [
      {
        label: 'Number of emails',
        data: senders.map(sender => sender.count),
        backgroundColor: '#3B82F6'
      }
    ]
  };
});

// Formater les données pour le graphique linéaire d'emails au fil du temps
const mailsOverTimeChartData = computed(() => {
  const timeData = statistics.value.mailsOverTime || [];
  return {
    labels: timeData.map(point => point.date),
    datasets: [
      {
        label: 'All emails',
        data: timeData.map(point => point.total),
        borderColor: '#3B82F6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2
      },
      {
        label: 'Quarantine',
        data: timeData.map(point => point.quarantine || 0),
        borderColor: '#F59E0B',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        borderWidth: 2
      },
      {
        label: 'Safe',
        data: timeData.map(point => point.safe || 0),
        borderColor: '#10B981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        borderWidth: 2
      },
      {
        label: 'Error',
        data: timeData.map(point => point.error || 0),
        borderColor: '#EF4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        borderWidth: 2
      }
    ]
  };
});

// Changement de période
const changePeriod = (period) => {
  timePeriod.value = period;
  loadStatistics();
};

// Exporter les statistiques en CSV
const exportStatistics = () => {
  // Préparer les données
  const data = [];

  // En-têtes
  data.push(['Category', 'Value']);

  // Données générales
  data.push(['Total Emails', statistics.value.totalMails]);
  data.push(['Threat Percentage', `${threatPercentage.value}%`]);

  // Statuts
  Object.entries(statistics.value.mailsByStatus || {}).forEach(([status, count]) => {
    data.push([`Status: ${status}`, count]);
  });

  // Catégories de menaces
  Object.entries(statistics.value.threatsByCategory || {}).forEach(([category, count]) => {
    data.push([`Threat: ${category}`, count]);
  });

  // Convertir en CSV
  const csvContent = data.map(row => row.join(',')).join('\n');

  // Créer un lien de téléchargement
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);

  link.setAttribute('href', url);
  link.setAttribute('download', `email-statistics-${timePeriod.value}-${new Date().toISOString().split('T')[0]}.csv`);
  link.style.visibility = 'hidden';

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// Initialiser la page
onMounted(async () => {
  authStore.initialize();

  if (authStore.isLoggedIn) {
    await loadStatistics();
  } else {
    router.push('/login');
  }
});
</script>

<template>
  <section class="py-6">
    <div class="container mx-auto px-4">
      <div class="mb-6">
        <h1 class="text-3xl font-bold">Statistics Dashboard</h1>
        <p class="text-gray-600">Overview of email security monitoring data</p>
      </div>

      <!-- Période -->
      <div class="flex mb-6 bg-white p-3 rounded-lg shadow-sm justify-between">
        <div class="flex space-x-2">
          <button
            v-for="period in ['week', 'month', 'year', 'all']"
            :key="period"
            @click="changePeriod(period)"
            class="px-4 py-2 rounded-md text-sm"
            :class="timePeriod === period ?
              'bg-blue-600 text-white' :
              'bg-gray-100 text-gray-700 hover:bg-gray-200'"
          >
            {{ period.charAt(0).toUpperCase() + period.slice(1) }}
          </button>
        </div>
        <button
          @click="exportStatistics"
          class="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md text-sm flex items-center"
          :disabled="loading"
        >
          <i class="pi pi-download mr-2"></i> Export CSV
        </button>
      </div>

      <!-- Loading et error states -->
      <div v-if="loading" class="flex justify-center py-8">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-700"></div>
      </div>

      <div v-else-if="error" class="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
        <div class="flex">
          <div class="flex-shrink-0">
            <i class="pi pi-exclamation-triangle text-red-400"></i>
          </div>
          <div class="ml-3">
            <p class="text-sm text-red-700">{{ error }}</p>
          </div>
        </div>
      </div>

      <div v-else>
        <!-- Cartes de statistiques -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <StatisticsCard
            title="Total Emails"
            :value="statistics.totalMails"
            icon="pi-envelope"
            color="bg-blue-500"
          />
          <StatisticsCard
            title="Detected Threats"
            :value="`${threatPercentage}%`"
            icon="pi-shield"
            color="bg-red-500"
          />
          <StatisticsCard
            title="Safe Emails"
            :value="statistics.mailsByStatus.SAFE || 0"
            icon="pi-check-circle"
            color="bg-green-500"
          />
          <StatisticsCard
            title="In Quarantine"
            :value="statistics.mailsByStatus.QUARANTINE || 0"
            icon="pi-exclamation-circle"
            color="bg-yellow-500"
          />
        </div>

        <!-- Graphiques -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <!-- Graphique circulaire des statuts -->
          <div class="bg-white p-4 rounded-lg shadow-sm">
            <h2 class="text-lg font-semibold mb-4">Email Status Distribution</h2>
            <div v-if="Object.keys(statistics.mailsByStatus).length > 0">
              <PieChartComponent
                :chart-data="statusChartData"
                :height="300"
              />
            </div>
            <NoDataMessage
              v-else
              message="No email status data for this period"
              icon="pi-pie-chart"
            />
          </div>

          <!-- Graphique à barres des principaux expéditeurs -->
          <div class="bg-white p-4 rounded-lg shadow-sm">
            <h2 class="text-lg font-semibold mb-4">Top Email Senders</h2>
            <div v-if="statistics.topSenders && statistics.topSenders.length > 0">
              <BarChartComponent
                :chart-data="topSendersChartData"
                :height="300"
              />
            </div>
            <NoDataMessage
              v-else
              message="No sender data for this period"
              icon="pi-users"
            />
          </div>
        </div>

        <!-- Tableau récapitulatif des menaces -->
        <div class="bg-white p-4 rounded-lg shadow-sm mb-6">
          <h2 class="text-lg font-semibold mb-4">Threat Categories</h2>
          <div v-if="Object.values(statistics.threatsByCategory || {}).some(v => v > 0)">
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div
                v-for="(count, category) in statistics.threatsByCategory"
                :key="category"
                class="bg-gray-50 p-4 rounded-lg border flex flex-col items-center"
              >
                <div class="text-xl font-bold">{{ count }}</div>
                <div class="text-sm text-gray-500">{{ category }}</div>
              </div>
            </div>
          </div>
          <NoDataMessage
            v-else
            message="No threat data for this period"
            icon="pi-shield"
          />
        </div>

        <!-- Graphique linéaire d'emails au fil du temps -->
        <div class="bg-white p-4 rounded-lg shadow-sm mb-6">
          <h2 class="text-lg font-semibold mb-4">Emails Over Time</h2>
          <div v-if="statistics.mailsOverTime && statistics.mailsOverTime.length > 0">
            <LineChartComponent
              :chart-data="mailsOverTimeChartData"
              :height="300"
            />
          </div>
          <NoDataMessage
            v-else
            message="No historical data for this period"
            icon="pi-calendar"
          />
        </div>
      </div>
    </div>
  </section>
</template>
