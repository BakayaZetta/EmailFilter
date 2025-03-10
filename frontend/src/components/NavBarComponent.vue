<script setup>
import detectish from '@/assets/img/detectish.png';
import { RouterLink, useRoute } from 'vue-router';

const isActive = (routePath) => {
  const currentRoute = useRoute();
  return currentRoute.path === routePath;
}

const links = [
  { name: 'Dashboard', path: '/' },
  { name: 'Quarantine', path: '/quarantine' },
  { name: 'Statistics', path: '/statistics' },
  { name: 'Settings', path: '/settings' },
  { name: 'Login', path: '/login' },
  { name: 'Register', path: '/register' },
];
</script>

<template>
  <nav class="bg-white border-b border-gray-200">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-20">
        <div class="flex flex-1 items-center justify-center md:items-stretch md:justify-start">
          <!-- Logo -->
          <RouterLink to="/" class="flex-shrink-0 flex items-center mr-4">
            <img class="h-10 w-auto rounded-full" :src=detectish alt="Detectish" />
            <span class="hidden md:block text-black text-2xl font-bold ml-2">Detectish</span>
          </RouterLink>

          <div class="md:ml-auto">
            <div class="flex space-x-2">
              <!-- For loop to print different links -->
              <RouterLink v-for="link in links" :key="link.name" :to="link.path" :class="[
                isActive(link.path) ? 'text-red-500' : 'hover:text-red-700',
                'text-black', 'px-2', 'py-2', 'rounded-md', 'font-medium']">
                {{ link.name }}
              </RouterLink>
            </div>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>
