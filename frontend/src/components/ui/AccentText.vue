<script setup>
defineProps({
  color: {
    type: String,
    default: 'indigo', // 'indigo', 'sky', 'purple', 'amber'
  }
})
</script>

<template>
  <span :class="{
    'text-indigo-500': color === 'indigo',
    'text-sky-500': color === 'sky',
    'text-purple-500': color === 'purple',
    'text-amber-500': color === 'amber'
  }">
    <slot />
  </span>
</template>
