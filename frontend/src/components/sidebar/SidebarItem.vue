<script setup>
defineProps({
  active: {
    type: Boolean,
    default: false
  },
  label: {
    type: String,
    required: true
  },
  icon: {
    type: [Object, Function],
    required: true
  },
  badge: {
    type: String,
    default: null
  }
})

defineEmits(['click'])
</script>

<template>
  <button
    @click="$emit('click')"
    :class="[
      'w-full flex items-center gap-3 px-4 py-3 rounded-2xl transition-all duration-300 group',
      active
        ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20 font-bold'
        : 'text-slate-400 hover:text-indigo-500 hover:bg-slate-800/50'
    ]"
  >
    <component
      :is="icon"
      :size="18"
      :class="[
        active ? 'text-white' : 'text-slate-400 group-hover:text-indigo-400'
      ]"
      class="transition-colors flex-shrink-0"
    />
    <span class="text-sm tracking-tight">{{ label }}</span>
    <span
      v-if="badge"
      :class="[
        'ml-auto px-2 py-0.5 rounded-lg text-[9px] font-black',
        active ? 'bg-white text-indigo-500' : 'bg-indigo-500 text-white'
      ]"
    >
      {{ badge }}
    </span>
  </button>
</template>
