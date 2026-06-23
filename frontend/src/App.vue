<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import NavBar from '@/components/NavBar.vue'

const route = useRoute()
const hideNavBar = computed(() => route.path.startsWith('/backend'))
</script>

<template>
  <div class="app" :class="{ 'app--fullscreen': hideNavBar }">
    <NavBar v-if="!hideNavBar" />
    <main class="main-content" :class="{ 'main-content--fullscreen': hideNavBar }">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app--fullscreen {
  height: 100vh;
  overflow: hidden;
}

.main-content {
  flex: 1;
  padding: var(--space-lg);
}

.main-content--fullscreen {
  padding: 0;
  overflow: hidden;
}
</style>
