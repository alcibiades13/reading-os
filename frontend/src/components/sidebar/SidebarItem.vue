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
  },
  collapsed: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click'])
</script>

<template>
  <button
    @click="$emit('click')"
    :class="[
      'w-full flex items-center rounded-xl transition-all duration-300 group relative',
      collapsed ? 'justify-center px-2 py-2' : 'gap-2.5 px-3 py-2',
      active
        ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20 font-bold'
        : 'text-slate-400 hover:text-indigo-500 hover:bg-slate-800/50'
    ]"
    :title="collapsed ? label : ''"
  >
    <component
      :is="icon"
      :size="16"
      :class="[
        active ? 'text-white' : 'text-slate-400 group-hover:text-indigo-400'
      ]"
      class="transition-colors flex-shrink-0"
    />
    <span
      v-show="!collapsed"
      class="text-[13px] tracking-tight whitespace-nowrap overflow-hidden transition-opacity duration-200"
      :class="collapsed ? 'opacity-0 w-0' : 'opacity-100'"
    >
      {{ label }}
    </span>
    <span
      v-if="badge && !collapsed"
      :class="[
        'ml-auto px-2 py-0.5 rounded-lg text-[9px] font-black',
        active ? 'bg-white text-indigo-500' : 'bg-indigo-500 text-white'
      ]"
    >
      {{ badge }}
    </span>
    <!-- Badge indicator for collapsed mode -->
    <span
      v-if="badge && collapsed"
      class="absolute top-1 right-1 w-2 h-2 bg-indigo-500 rounded-full"
    />
  </button>
</template>
