<script setup>
import { ref, watch, onMounted } from 'vue'
import { BookOpen } from 'lucide-vue-next'
import { ebooksAPI } from '@/services/api'

// Covers are private files (need the auth header), so they're fetched as blobs.
// Object URLs are cached for the whole session.
const coverUrls = new Map()

const props = defineProps({
  ebook: { type: Object, required: true },
})

const src = ref(null)

const load = async () => {
  const { ebook } = props
  if (ebook.has_cover) {
    if (!coverUrls.has(ebook.id)) {
      coverUrls.set(ebook.id, ebooksAPI.cover(ebook.id)
        .then(({ data }) => URL.createObjectURL(data))
        .catch(() => null))
    }
    src.value = await coverUrls.get(ebook.id)
  }
  if (!src.value) src.value = ebook.book_detail?.cover_image || null
}

onMounted(load)
watch(() => [props.ebook.id, props.ebook.has_cover], load)
</script>

<template>
  <img v-if="src" :src="src" :alt="ebook.title" class="w-full h-full object-cover" />
  <div
    v-else
    class="w-full h-full flex flex-col items-center justify-center gap-2 p-3 text-center bg-gradient-to-br from-indigo-950 via-zinc-900 to-zinc-950"
  >
    <BookOpen :size="20" class="text-indigo-400/60" />
    <p class="text-[11px] font-serif font-bold text-zinc-300 line-clamp-4 leading-snug">{{ ebook.title }}</p>
  </div>
</template>
