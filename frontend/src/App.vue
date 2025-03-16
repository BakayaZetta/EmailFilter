<script setup>
import { RouterView } from 'vue-router'
import NavBar from '@/components/NavBarComponent.vue';
import Footer from '@/components/FooterComponent.vue';
</script>

<template>
  <div class="flex flex-col min-h-screen">
    <NavBar />
    <main class="flex-grow">
      <RouterView />
    </main>
    <Footer />
  </div>
</template>
