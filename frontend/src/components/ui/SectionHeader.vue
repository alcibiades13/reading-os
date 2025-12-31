<script setup>
defineProps({
  title: {
    type: String,
    required: true
  }
})
</script>

<template>
  <h2 class="text-xs font-bold text-slate-500 uppercase tracking-[0.2em]">
    {{ title }}
  </h2>
</template>
