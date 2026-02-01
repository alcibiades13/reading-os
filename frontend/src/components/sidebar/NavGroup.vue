<script setup>
defineProps({
  label: {
    type: String,
    required: true
  },
  collapsed: {
    type: Boolean,
    default: false
  }
})
</script>

<template>
  <div :class="['transition-all duration-300', collapsed ? 'py-1' : 'py-2']">
    <h3
      v-show="!collapsed"
      class="px-3 text-[9px] font-black text-slate-500 uppercase tracking-[0.2em] mb-1.5 whitespace-nowrap overflow-hidden transition-opacity duration-200"
      :class="collapsed ? 'opacity-0 h-0 mb-0' : 'opacity-100'"
    >
      {{ label }}
    </h3>
    <!-- Divider line when collapsed -->
    <div
      v-if="collapsed"
      class="mx-2 mb-1 border-t border-slate-800/50"
    />
    <div class="space-y-0.5">
      <slot />
    </div>
  </div>
</template>
