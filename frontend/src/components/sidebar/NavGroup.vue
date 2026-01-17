<script setup>
defineProps({
  label: {
    type: String,
    required: true
  }
})
</script>

<template>
  <div class="py-4">
    <h3 class="px-4 text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-3">
      {{ label }}
    </h3>
    <div class="space-y-1">
      <slot />
    </div>
  </div>
</template>
