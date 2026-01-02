<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: ''
  },
  accentWord: {
    type: String,
    default: ''
  }
})
</script>

<template>
  <header class="mb-10">
    <h1 class="text-page-heading font-black text-white tracking-tight mb-3">
      <template v-if="accentWord">
        <span v-html="title.replace(accentWord, `<span class='text-indigo-400'>${accentWord}</span>`)"></span>
      </template>
      <template v-else>
        {{ title }}
      </template>
    </h1>
    <p v-if="subtitle" class="text-page-subtitle text-slate-400 max-w-3xl leading-relaxed">
      {{ subtitle }}
    </p>
  </header>
</template>
