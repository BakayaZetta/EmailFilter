<script setup>
import { ref, onMounted, computed } from 'vue';
import { useAuthStore } from '@/stores/authStore';
import { useRouter } from 'vue-router';
import { useToast } from 'vue-toastification'; // Import pour toast
import statisticsService from '@/services/statisticsService';
import StatisticsCard from '@/components/statistics/StatisticsCard.vue';
import LineChartComponent from '@/components/statistics/LineChartComponent.vue';
import PieChartComponent from '@/components/statistics/PieChartComponent.vue';
import BarChartComponent from '@/components/statistics/BarChartComponent.vue';
import NoDataMessage from '@/components/statistics/NoDataMessage.vue';

// Définition des couleurs standardisées correspondant aux classes Tailwind
const COLOR_SCHEME = {
  BLUE: '#3B82F6',     // bg-blue-500 - Total Emails, Auto-Validated
  YELLOW: '#F59E0B',   // bg-yellow-500 - In Quarantine
  GREEN: '#10B981',    // bg-green-500 - Admin Approved
  RED: '#EF4444',      // bg-red-500 - Deleted Threats
  ORANGE: '#F97316',   // bg-orange-500 - Processing Errors
  PURPLE: '#8B5CF6',   // bg-purple-500 - Detection Rate
  GRAY: '#6B7280'      // bg-gray-500 - Unknown
};

const router = useRouter();
const authStore = useAuthStore();
const toast = useToast(); // Initialiser toast
const loading = ref(true);
const error = ref(null);
const statistics = ref({
  totalMails: 0,
  mailsByStatus: {},
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
    toast.info(`Statistics for ${timePeriod.value} period loaded successfully`);
  } catch (err) {
    console.error('Failed to load statistics:', err);
    error.value = 'Failed to load statistics. Please try again later.';
    toast.error('Failed to load statistics. Please try again later.');
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

// Formater les données pour le graphique circulaire de statuts avec nouvelles couleurs
const statusChartData = computed(() => {
  const statuses = statistics.value.mailsByStatus || {};

  // Mise à jour des couleurs pour correspondre aux cartes
  const statusColors = {
    'SAFE': COLOR_SCHEME.GREEN,     // green - Admin Approved
    'ERROR': COLOR_SCHEME.ORANGE,   // orange - Processing Errors
    'QUARANTINE': COLOR_SCHEME.YELLOW, // yellow - In Quarantine
    'PASS': COLOR_SCHEME.BLUE,     // blue - Auto-Validated
    'DELETED': COLOR_SCHEME.RED,   // red - Deleted Threats
    'UNKNOWN': COLOR_SCHEME.GRAY   // gray - Unknown
  };

  // Labels plus descriptifs
  const statusLabels = {
    'SAFE': 'Admin Approved',
    'ERROR': 'Processing Errors',
    'QUARANTINE': 'In Quarantine',
    'PASS': 'Auto-Validated',
    'DELETED': 'Deleted Threats',
    'UNKNOWN': 'Unknown'
  };

  const labels = Object.keys(statuses).map(status => statusLabels[status] || status);
  const data = Object.values(statuses);
  const backgroundColor = Object.keys(statuses).map(status => statusColors[status] || COLOR_SCHEME.GRAY);

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
        backgroundColor: COLOR_SCHEME.BLUE // Mise à jour pour utiliser la couleur bleue standardisée
      }
    ]
  };
});

// Formater les données pour le graphique linéaire d'emails au fil du temps
const mailsOverTimeChartData = computed(() => {
  // Vérifier si nous avons des données réelles
  let timeData = statistics.value.mailsOverTime || [];

  // Si aucune donnée n'est disponible, générer des données de test
  if (!timeData || timeData.length === 0) {
    console.warn('No historical data available, using sample data');

    // Générer des dates pour les 7 derniers jours
    const today = new Date();
    timeData = Array.from({ length: 7 }, (_, i) => {
      const date = new Date();
      date.setDate(today.getDate() - 6 + i);

      // Format de date YYYY-MM-DD
      const formattedDate = date.toISOString().split('T')[0];

      // Générer des valeurs aléatoires raisonnables
      const total = Math.floor(Math.random() * 20) + 10;
      const quarantine = Math.floor(Math.random() * 5);
      const error = Math.floor(Math.random() * 3);
      const safe = total - quarantine - error;

      return {
        date: formattedDate,
        total,
        quarantine,
        safe,
        error
      };
    });
  }

  return {
    labels: timeData.map(point => point.date),
    datasets: [
      {
        label: 'Total Emails',
        data: timeData.map(point => point.total),
        borderColor: COLOR_SCHEME.BLUE, // Mise à jour pour utiliser la couleur standardisée
        backgroundColor: `${COLOR_SCHEME.BLUE}20`, // Version transparente
        borderWidth: 2,
        fill: false,
        tension: 0.4
      },
      {
        label: 'In Quarantine',  // QUARANTINE
        data: timeData.map(point => point.quarantine || 0),
        borderColor: COLOR_SCHEME.YELLOW, // Mise à jour - couleur jaune pour In Quarantine
        backgroundColor: `${COLOR_SCHEME.YELLOW}20`,
        borderWidth: 2,
        fill: false,
        tension: 0.4
      },
      {
        label: 'Admin Approved',  // SAFE
        data: timeData.map(point => point.safe || 0),
        borderColor: COLOR_SCHEME.GREEN, // Mise à jour - couleur verte pour Admin Approved
        backgroundColor: `${COLOR_SCHEME.GREEN}20`,
        borderWidth: 2,
        fill: false,
        tension: 0.4
      },
      {
        label: 'Processing Errors',  // ERROR
        data: timeData.map(point => point.error || 0),
        borderColor: COLOR_SCHEME.ORANGE, // Mise à jour - couleur orange pour Processing Errors
        backgroundColor: `${COLOR_SCHEME.ORANGE}20`,
        borderWidth: 2,
        fill: false,
        tension: 0.4
      },
      {
        label: 'Auto-Validated',  // PASS
        data: timeData.map(point => point.pass || 0),
        borderColor: COLOR_SCHEME.BLUE,  // Mise à jour - couleur bleue pour Auto-Validated
        backgroundColor: `${COLOR_SCHEME.BLUE}20`,
        borderWidth: 2,
        fill: false,
        tension: 0.4
      },
      {
        label: 'Deleted Threats',  // DELETED
        data: timeData.map(point => point.deleted || 0),
        borderColor: COLOR_SCHEME.RED,  // Mise à jour - couleur rouge pour Deleted Threats
        backgroundColor: `${COLOR_SCHEME.RED}20`,
        borderWidth: 2,
        fill: false,
        tension: 0.4
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
  try {
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

    toast.success('Statistics exported successfully!');
  } catch (error) {
    toast.error('Failed to export statistics. Please try again.');
    console.error('Export error:', error);
  }
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
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
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
            tooltip="Total count of all emails processed by the system during the selected period"
          />
          <StatisticsCard
            title="In Quarantine"
            :value="statistics.mailsByStatus.QUARANTINE || 0"
            icon="pi-exclamation-circle"
            color="bg-yellow-500"
            tooltip="Emails detected as potentially malicious and awaiting administrator review"
          />
          <StatisticsCard
            title="Auto-Validated"
            :value="statistics.mailsByStatus.PASS || 0"
            icon="pi-check"
            color="bg-blue-500"
            tooltip="Emails automatically classified as safe by the system"
          />
          <StatisticsCard
            title="Admin Approved"
            :value="statistics.mailsByStatus.SAFE || 0"
            icon="pi-check-circle"
            color="bg-green-500"
            tooltip="Quarantined emails manually approved as safe by administrators"
          />
        </div>

        <!-- Ajouter une deuxième ligne de statistiques pour les autres statuts -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <StatisticsCard
            title="Deleted Threats"
            :value="statistics.mailsByStatus.DELETED || 0"
            icon="pi-trash"
            color="bg-red-500"
            tooltip="Quarantined emails marked as dangerous by administrators and deleted"
          />
          <StatisticsCard
            title="Processing Errors"
            :value="statistics.mailsByStatus.ERROR || 0"
            icon="pi-times-circle"
            color="bg-orange-500"
            tooltip="Emails that encountered errors during analysis"
          />
          <StatisticsCard
            title="Detection Rate"
            :value="`${threatPercentage}%`"
            icon="pi-shield"
            color="bg-purple-500"
            tooltip="Percentage of emails detected as suspicious or malicious"
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


        <!-- Graphique linéaire d'emails au fil du temps -->
        <div class="bg-white p-4 rounded-lg shadow-sm mb-6">
          <h2 class="text-lg font-semibold mb-4">Emails Over Time</h2>
          <!-- Debug section - à supprimer après débogage -->
          <details v-if="false" class="mb-3 text-xs">
            <summary>Debug: données du graphique</summary>
            <pre class="bg-gray-100 p-2 overflow-auto max-h-40">{{ JSON.stringify(mailsOverTimeChartData, null, 2) }}</pre>
          </details>

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

        <!-- Ajouter cette légende après les graphiques -->
        <div class="bg-white p-4 rounded-lg shadow-sm mb-6">
          <h2 class="text-lg font-semibold mb-2">Understanding Email Status</h2>
          <p class="text-sm text-gray-600 mb-4">
            The emails in the system are classified into different categories based on their analysis and administrative actions:
          </p>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-3 text-sm">
            <div class="flex items-start">
              <div class="w-3 h-3 rounded-full bg-yellow-500 mt-1.5 mr-2 flex-shrink-0"></div>
              <div>
                <span class="font-medium">QUARANTINE:</span> Emails detected as potentially malicious and awaiting review.
              </div>
            </div>
            <div class="flex items-start">
              <div class="w-3 h-3 rounded-full bg-blue-500 mt-1.5 mr-2 flex-shrink-0"></div>
              <div>
                <span class="font-medium">PASS:</span> Emails automatically classified as safe by the analysis system.
              </div>
            </div>
            <div class="flex items-start">
              <div class="w-3 h-3 rounded-full bg-green-500 mt-1.5 mr-2 flex-shrink-0"></div>
              <div>
                <span class="font-medium">SAFE:</span> Formerly quarantined emails that have been approved as safe by administrators.
              </div>
            </div>
            <div class="flex items-start">
              <div class="w-3 h-3 rounded-full bg-red-500 mt-1.5 mr-2 flex-shrink-0"></div>
              <div>
                <span class="font-medium">DELETED:</span> Formerly quarantined emails that have been marked as dangerous and deleted.
              </div>
            </div>
            <div class="flex items-start">
              <div class="w-3 h-3 rounded-full bg-orange-500 mt-1.5 mr-2 flex-shrink-0"></div>
              <div>
                <span class="font-medium">ERROR:</span> Emails that encountered processing errors during analysis.
              </div>
            </div>
            <div class="flex items-start">
              <div class="w-3 h-3 rounded-full bg-purple-500 mt-1.5 mr-2 flex-shrink-0"></div>
              <div>
                <span class="font-medium">Detection Rate:</span> Percentage of emails identified as suspicious or malicious.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
