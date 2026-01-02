<script setup>
defineProps({
  title: {
    type: String,
    required: true
  }
})
</script>

<template>
  <h2 class="text-page-meta font-bold text-slate-500 uppercase tracking-[0.2em] sm:tracking-[0.3em]">
    {{ title }}
  </h2>
</template>
