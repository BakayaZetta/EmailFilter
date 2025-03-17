<script setup>
import { computed } from 'vue';

const props = defineProps({
  analyses: {
    type: Array,
    default: () => []
  },
  links: {
    type: Array,
    default: () => []
  },
  attachments: {
    type: Array,
    default: () => []
  }
});

// Catégoriser les analyses par type
const categorizedAnalyses = computed(() => {
  if (!props.analyses) return { SPF: [], DKIM: [], DMARC: [], AI: [] };

  const result = {
    SPF: props.analyses.filter(a => a.type === 'SPF'),
    DKIM: props.analyses.filter(a => a.type === 'DKIM'),
    DMARC: props.analyses.filter(a => a.type === 'DMARC'),
    AI: props.analyses.filter(a => a.type === 'AI')
  };
  return result;
});

// Parseur pour les résultats d'analyse AI
const parseAIResult = (resultText) => {
  try {
    if (!resultText) return null;

    // Extract the JSON part if prefixed with a type label
    const jsonRegex = /(?:\w+:)?\s*({.*})/;
    const match = resultText.match(jsonRegex);
    const jsonText = match ? match[1].trim() : resultText.trim();

    // Convert Python-style dict to JSON
    let processedText = jsonText
      // Replace single quotes with double quotes
      .replace(/'/g, '"')
      // Make sure property names are quoted properly
      .replace(/([{,]\s*)(\w+)(\s*:)/g, '$1"$2"$3');

    // Parse the JSON
    const result = JSON.parse(processedText);

    // Normalize the result with expected properties
    return {
      phishing_count: result.phishing_count || 0,
      benign_count: result.benign_count || 0,
      phishing_avg_score: result.phishing_avg_score || 0,
      benign_avg_score: result.benign_avg_score || 0
    };
  } catch (e) {
    console.error('Error parsing AI result', e);

    // Return default structure to avoid UI errors
    return {
      phishing_count: 0,
      benign_count: 0,
      phishing_avg_score: 0,
      benign_avg_score: 0,
      error: 'Format error'
    };
  }
};

// Obtenir une icône et une couleur basées sur le résultat de l'analyse
const getAnalysisIndicator = (analysis) => {
  const result = analysis.result.toLowerCase();

  if (result.includes(' valid') || result.includes('pass')) {
    return { icon: 'pi-check-circle', color: 'text-green-500' };
  } else if (result.includes('invalid') || result.includes('fail')) {
    return { icon: 'pi-times-circle', color: 'text-red-500' };
  } else if (result.includes('warning') || result.includes('soft')) {
    return { icon: 'pi-exclamation-triangle', color: 'text-yellow-500' };
  } else {
    return { icon: 'pi-info-circle', color: 'text-gray-500' };
  }
};

// Déterminer si un email est globalement suspect en fonction des analyses
const isEmailSuspicious = computed(() => {
  // Vérifier les analyses SPF et DKIM
  const hasSPFFailure = categorizedAnalyses.value.SPF.some(a =>
    a.result.toLowerCase().includes('invalid') ||
    a.result.toLowerCase().includes('fail')
  );

  const hasDKIMFailure = categorizedAnalyses.value.DKIM.some(a => {
    const result = a.result.toLowerCase();
    return result.includes('invalid') ||
           result.includes('no dkim signature found') ||
           result.includes('dns error') ||
           result.includes('error during');
  });

  // Vérifier l'analyse AI
  const aiAnalyses = categorizedAnalyses.value.AI;
  let aiSuspicious = false;

  if (aiAnalyses.length > 0) {
    for (const analysis of aiAnalyses) {
      const aiResult = parseAIResult(analysis.result);
      if (aiResult && aiResult.phishing_count > aiResult.benign_count) {
        aiSuspicious = true;
        break;
      }
    }
  }

  // Vérifier si des liens suspects ont été détectés
  const hasSuspiciousLinks = props.links?.some(link =>
    link.status?.toLowerCase().includes('suspicious') ||
    link.status?.toLowerCase().includes('malicious')
  );

  // Vérifier si des pièces jointes suspectes ont été détectées
  const hasSuspiciousAttachments = props.attachments?.some(attachment =>
    attachment.status?.toLowerCase().includes('suspicious') ||
    attachment.status?.toLowerCase().includes('malicious')
  );

  return hasSPFFailure || hasDKIMFailure || aiSuspicious || hasSuspiciousLinks || hasSuspiciousAttachments;
});

// Obtenir la classe de couleur pour le statut d'analyse
const getStatusColor = (status) => {
  if (!status) return 'text-gray-500';

  const lowerStatus = status.toLowerCase();
  if (lowerStatus.includes('malicious') || lowerStatus.includes('dangerous')) {
    return 'text-red-600';
  }
  if (lowerStatus.includes('suspicious')) {
    return 'text-yellow-600';
  }
  if (lowerStatus.includes('safe') || lowerStatus.includes('clean')) {
    return 'text-green-600';
  }

  return 'text-gray-500';
};

// Obtenir l'icône pour un type de fichier
const getFileIcon = (fileType) => {
  if (!fileType) return 'pi-file';

  const type = fileType.toLowerCase();
  if (type.includes('pdf')) return 'pi-file-pdf';
  if (type.includes('word') || type.includes('doc')) return 'pi-file-word';
  if (type.includes('excel') || type.includes('xls')) return 'pi-file-excel';
  if (type.includes('image') || type.includes('png') || type.includes('jpg')) return 'pi-image';
  if (type.includes('zip') || type.includes('archive') || type.includes('rar')) return 'pi-box';
  if (type.includes('exe') || type.includes('application')) return 'pi-cog';

  return 'pi-file';
};

// Formatage de la taille de pièce jointe
const formatFileSize = (sizeInBytes) => {
  if (!sizeInBytes) return 'Unknown';

  if (sizeInBytes < 1024) {
    return `${sizeInBytes} B`;
  } else if (sizeInBytes < 1024 * 1024) {
    return `${(sizeInBytes / 1024).toFixed(1)} KB`;
  } else {
    return `${(sizeInBytes / (1024 * 1024)).toFixed(1)} MB`;
  }
};
</script>

<template>
  <div>
    <!-- Barre de statut globale -->
    <div
      :class="[
        'mb-3 p-2 rounded-lg text-white font-medium flex items-center',
        isEmailSuspicious ? 'bg-red-500' : 'bg-green-500'
      ]"
    >
      <i :class="`pi ${isEmailSuspicious ? 'pi-shield' : 'pi-check-circle'} mr-2`"></i>
      <span>{{ isEmailSuspicious ? 'This email shows suspicious signs' : 'This email appears secure' }}</span>
    </div>

    <!-- Section des analyses -->
    <div class="mb-5">
      <h3 class="text-lg font-semibold mb-2">Security Analyses</h3>
      <div v-if="!props.analyses || props.analyses.length === 0" class="text-sm text-gray-500 italic">
        No analysis available for this message
      </div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <!-- Résultats SPF -->
        <div v-if="categorizedAnalyses.SPF.length > 0" class="bg-gray-50 p-2 rounded border">
          <div class="flex items-center mb-1">
            <i class="pi pi-shield mr-1"></i>
            <span class="font-medium">SPF (Sender Policy Framework)</span>
          </div>
          <div v-for="analysis in categorizedAnalyses.SPF" :key="analysis.id" class="text-sm">
            <div class="flex items-center mt-1">
              <i :class="`pi ${getAnalysisIndicator(analysis).icon} ${getAnalysisIndicator(analysis).color} mr-1`"></i>
              <span>{{ analysis.result.replace('SPF: ', '') }}</span>
            </div>
            <div class="text-xs text-gray-500 mt-1">
              Analyzed on {{ new Date(analysis.date).toLocaleString() }}
            </div>
          </div>
        </div>

        <!-- Résultats DKIM -->
        <div v-if="categorizedAnalyses.DKIM.length > 0" class="bg-gray-50 p-2 rounded border">
          <div class="flex items-center mb-1">
            <i class="pi pi-lock mr-1"></i>
            <span class="font-medium">DKIM (DomainKeys Identified Mail)</span>
          </div>
          <div v-for="analysis in categorizedAnalyses.DKIM" :key="analysis.id" class="text-sm">
            <div class="flex items-center mt-1">
              <i :class="`pi ${getAnalysisIndicator(analysis).icon} ${getAnalysisIndicator(analysis).color} mr-1`"></i>
              <span>{{ analysis.result.replace('DKIM: ', '') }}</span>
            </div>
            <div class="text-xs text-gray-500 mt-1">
              Analyzed on {{ new Date(analysis.date).toLocaleString() }}
            </div>
          </div>
        </div>

        <!-- Résultats DMARC -->
        <div v-if="categorizedAnalyses.DMARC.length > 0" class="bg-gray-50 p-2 rounded border">
          <div class="flex items-center mb-1">
            <i class="pi pi-verified mr-1"></i>
            <span class="font-medium">DMARC (Domain-based Message Authentication)</span>
          </div>
          <div v-for="analysis in categorizedAnalyses.DMARC" :key="analysis.id" class="text-sm">
            <div class="flex items-center mt-1">
              <i :class="`pi ${getAnalysisIndicator(analysis).icon} ${getAnalysisIndicator(analysis).color} mr-1`"></i>
              <span>{{ analysis.result.replace('DMARC: ', '') }}</span>
            </div>
            <div class="text-xs text-gray-500 mt-1">
              Analyzed on {{ new Date(analysis.date).toLocaleString() }}
            </div>
          </div>
        </div>

        <!-- Résultats AI -->
        <div v-if="categorizedAnalyses.AI.length > 0" class="bg-gray-50 p-2 rounded border">
          <div class="flex items-center mb-1">
            <i class="pi pi-chart-bar mr-1"></i>
            <span class="font-medium">Artificial Intelligence Analysis</span>
          </div>
          <div v-for="analysis in categorizedAnalyses.AI" :key="analysis.id" class="text-sm">
            <template v-if="parseAIResult(analysis.result) &&
                           parseAIResult(analysis.result).phishing_count !== undefined &&
                           parseAIResult(analysis.result).benign_count !== undefined">
              <div class="mt-1">
                <div class="grid grid-cols-2 gap-2">
                  <div class="p-1 rounded bg-red-50">
                    <div class="font-medium text-red-700">Phishing</div>
                    <div class="text-xs">Instances: {{ parseAIResult(analysis.result).phishing_count }}</div>
                    <div class="text-xs">Average score: {{ (parseAIResult(analysis.result).phishing_avg_score * 100 || 0).toFixed(2) }}%</div>
                  </div>
                  <div class="p-1 rounded bg-green-50">
                    <div class="font-medium text-green-700">Legitimate</div>
                    <div class="text-xs">Instances: {{ parseAIResult(analysis.result).benign_count }}</div>
                    <div class="text-xs">Average score: {{ (parseAIResult(analysis.result).benign_avg_score * 100 || 0).toFixed(2) }}%</div>
                  </div>
                </div>
              </div>
              <div class="mt-1 text-sm">
                <span :class="parseAIResult(analysis.result).phishing_count > parseAIResult(analysis.result).benign_count ? 'text-red-600 font-medium' : 'text-green-600 font-medium'">
                  Verdict: {{ parseAIResult(analysis.result).phishing_count > parseAIResult(analysis.result).benign_count ? 'Potentially malicious' : 'Probably legitimate' }}
                </span>
              </div>
            </template>
            <div v-else class="text-xs text-gray-500 mt-1">
              Analysis data unavailable or in incorrect format
              <div v-if="parseAIResult(analysis.result)?.error" class="text-red-500">
                ({{ parseAIResult(analysis.result).error }})
              </div>
            </div>
            <div class="text-xs text-gray-500 mt-1">
              Analyzed on {{ new Date(analysis.date).toLocaleString() }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Section des pièces jointes -->
    <div v-if="props.attachments && props.attachments.length > 0" class="mb-5">
      <h3 class="text-lg font-semibold mb-2">Attachments ({{ props.attachments.length }})</h3>
      <div class="bg-gray-50 p-3 rounded">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
          <div v-for="attachment in props.attachments" :key="attachment.id"
               class="flex items-center border p-2 rounded bg-white">
            <div class="mr-3">
              <i :class="`pi ${getFileIcon(attachment.type)} text-xl`"></i>
            </div>
            <div class="flex-grow">
              <div class="text-sm font-medium truncate" :title="attachment.name">
                {{ attachment.name }}
              </div>
              <div class="text-xs text-gray-500">
                {{ formatFileSize(attachment.size) }} - {{ attachment.type || 'Unknown type' }}
              </div>
            </div>
            <div :class="`ml-2 text-xs font-medium ${getStatusColor(attachment.status)}`">
              {{ attachment.status || 'Not analyzed' }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Section des liens -->
    <div v-if="props.links && props.links.length > 0" class="mb-5">
      <h3 class="text-lg font-semibold mb-2">Detected Links ({{ props.links.length }})</h3>
      <div class="bg-gray-50 p-3 rounded">
        <div class="space-y-1">
          <div v-for="link in props.links" :key="link.id"
               class="flex items-center border p-2 rounded bg-white">
            <div class="mr-2">
              <i class="pi pi-link text-blue-500"></i>
            </div>
            <div class="flex-grow">
              <div class="text-sm truncate" :title="link.url">
                {{ link.url }}
              </div>
            </div>
            <div :class="`ml-2 text-xs font-medium ${getStatusColor(link.status)}`">
              {{ link.status || 'Not analyzed' }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
