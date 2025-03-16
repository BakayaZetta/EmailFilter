<script setup>
import { ref } from 'vue';
import detectish from '@/assets/img/detectish.png';

const currentYear = ref(new Date().getFullYear());
</script>

<template>
  <footer class="bg-white/65 backdrop-blur border-t border-gray-200 mt-auto">
    <div class="mx-auto max-w-7xl px-4 py-4">
      <div class="flex flex-col items-center">
        <!-- Logo and description - centered -->
        <div class="flex flex-col items-center mb-3">
          <div class="flex items-center">
            <img class="h-7 w-auto rounded-full" :src="detectish" alt="Detectish" />
            <span class="text-black text-lg font-bold ml-2">Detectish</span>
          </div>
          <p class="text-gray-600 text-xs mt-1 max-w-xl text-center">
            Advanced email phishing detection system powered by machine learning and security technologies.
          </p>
        </div>

        <!-- Links section -->
        <!-- <div class="grid grid-cols-2 gap-x-12 gap-y-4 text-sm">
          <div>
            <h3 class="font-semibold text-gray-900 mb-2">Resources</h3>
            <ul class="space-y-2">
              <li><a href="#" class="text-gray-600 hover:text-red-500">Documentation</a></li>
              <li><a href="#" class="text-gray-600 hover:text-red-500">API Reference</a></li>
              <li><a href="#" class="text-gray-600 hover:text-red-500">Security</a></li>
            </ul>
          </div>
          <div>
            <h3 class="font-semibold text-gray-900 mb-2">About</h3>
            <ul class="space-y-2">
              <li><a href="#" class="text-gray-600 hover:text-red-500">Team</a></li>
              <li><a href="#" class="text-gray-600 hover:text-red-500">Privacy</a></li>
              <li><a href="#" class="text-gray-600 hover:text-red-500">Terms</a></li>
            </ul>
          </div>
        </div> -->
      </div>

      <!-- Copyright and GitHub link - centered -->
      <div class="pt-2 border-t border-gray-200 flex flex-col items-center text-sm">
        <p class="text-gray-500 mb-2">
          &copy; {{ currentYear }} Detectish. All rights reserved.
        </p>
        <div>
          <a href="https://github.com/Matth-L/detectish" class="text-gray-500 hover:text-red-500">
            <i class="pi pi-github"></i>
          </a>
          <!-- <a href="#" class="text-gray-500 hover:text-red-500">
            <i class="pi pi-twitter"></i>
          </a>
          <a href="#" class="text-gray-500 hover:text-red-500">
            <i class="pi pi-linkedin"></i>
          </a> -->
        </div>
      </div>
    </div>
  </footer>
</template>
