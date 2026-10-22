<script setup>
import { ref, nextTick } from 'vue'
import { StickyNote, Plus, Pencil, Trash2, Check, X, Play } from 'lucide-vue-next'

/**
 * Stickers = named reading positions, for reading several parts of a book in parallel.
 * mode 'manage': add / rename / delete / jump.  mode 'continue': pick where to resume on open.
 */
const props = defineProps({
  mode: { type: String, default: 'manage' }, // 'manage' | 'continue'
  bookmarks: { type: Array, required: true },
  activeId: { type: Number, default: null },
  currentLabel: { type: String, default: '' },
  lastProgress: { type: Number, default: null },
  totalPages: { type: Number, default: null },
  format: { type: String, required: true },
  theme: { type: Object, required: true },
  busy: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'go', 'add', 'rename', 'delete', 'continue-last', 'unfollow'])

const COLORS = ['#f59e0b', '#38bdf8', '#34d399', '#f472b6', '#a78bfa', '#fb7185', '#facc15', '#2dd4bf']
const colorFor = (index) => COLORS[index % COLORS.length]

const newLabel = ref(props.currentLabel)
const adding = ref(props.mode === 'manage' && props.bookmarks.length === 0)
const editingId = ref(null)
const editLabel = ref('')
const addInput = ref(null)

const where = (bookmark) => {
  if (props.format === 'pdf') return `p. ${bookmark.position}`
  if (bookmark.progress == null) return ''
  const percent = `${Math.round(bookmark.progress * 100)}%`
  return props.totalPages ? `${percent} · p. ${Math.max(1, Math.round(bookmark.progress * props.totalPages))}` : percent
}

const startAdd = async () => {
  newLabel.value = props.currentLabel
  adding.value = true
  await nextTick()
  addInput.value?.focus()
  addInput.value?.select()
}

const submitAdd = () => {
  if (!newLabel.value.trim()) return
  emit('add', newLabel.value.trim())
  adding.value = false
}

const startEdit = (bookmark) => {
  editingId.value = bookmark.id
  editLabel.value = bookmark.label
}

const submitEdit = (bookmark) => {
  const label = editLabel.value.trim()
  if (label && label !== bookmark.label) emit('rename', bookmark, label)
  editingId.value = null
}

const confirmDelete = (bookmark) => {
  if (confirm(`Remove sticker "${bookmark.label}"?`)) emit('delete', bookmark)
}

const inputStyle = {
  background: `${props.theme.muted}1a`,
  borderColor: `${props.theme.muted}40`,
  color: props.theme.fg,
}
</script>

<template>
  <div
    class="rounded-t-2xl sm:rounded-2xl border shadow-2xl p-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] sm:pb-5 space-y-4 max-h-[80vh] overflow-y-auto"
    :style="{ background: theme.bg, color: theme.fg, borderColor: `${theme.muted}40` }"
    @click.stop
  >
    <div class="flex items-center gap-3">
      <div class="w-9 h-9 shrink-0 rounded-xl flex items-center justify-center bg-amber-500/15 text-amber-400">
        <StickyNote :size="18" />
      </div>
      <div class="flex-1 min-w-0">
        <p class="font-bold">{{ mode === 'continue' ? 'Where do you want to continue?' : 'Stickers' }}</p>
        <p v-if="mode === 'manage'" class="text-[11px]" :style="{ color: theme.muted }">
          Mark the places you're reading. The sticker you read from moves along with you.
        </p>
      </div>
      <button class="p-2 rounded-lg hover:opacity-70" @click="emit('close')"><X :size="18" /></button>
    </div>

    <ul class="space-y-2">
      <li
        v-for="(bookmark, index) in bookmarks"
        :key="bookmark.id"
        class="flex items-center gap-3 p-2.5 rounded-xl border"
        :style="{ borderColor: bookmark.id === activeId ? '#6366f1' : `${theme.muted}33`, background: bookmark.id === activeId ? 'rgba(99,102,241,0.08)' : 'transparent' }"
      >
        <span class="w-2.5 self-stretch rounded-full shrink-0" :style="{ background: colorFor(index) }" />

        <div v-if="editingId === bookmark.id" class="flex-1 flex gap-2">
          <input
            v-model="editLabel"
            maxlength="200"
            class="flex-1 min-w-0 rounded-lg px-2.5 py-1.5 text-sm outline-none border focus:border-indigo-500"
            :style="inputStyle"
            @keydown.enter="submitEdit(bookmark)"
            @keydown.esc.stop="editingId = null"
          />
          <button class="p-2 rounded-lg bg-indigo-500 text-white" @click="submitEdit(bookmark)"><Check :size="14" /></button>
        </div>

        <template v-else>
          <button class="flex-1 min-w-0 text-left" :disabled="busy" @click="emit('go', bookmark)">
            <p class="text-sm font-semibold truncate">{{ bookmark.label }}</p>
            <p class="text-[11px]" :style="{ color: theme.muted }">
              {{ where(bookmark) }}<template v-if="bookmark.id === activeId"> · reading here</template>
            </p>
          </button>
          <template v-if="mode === 'manage'">
            <button v-if="bookmark.id === activeId" class="px-2 py-1 rounded-lg text-[11px] font-bold hover:opacity-70" :style="{ color: theme.muted }" title="Keep this sticker where it is" @click="emit('unfollow')">
              Unpin
            </button>
            <button class="p-2 rounded-lg hover:opacity-70" title="Rename" @click="startEdit(bookmark)"><Pencil :size="14" /></button>
            <button class="p-2 rounded-lg hover:text-red-400" title="Remove" @click="confirmDelete(bookmark)"><Trash2 :size="14" /></button>
          </template>
          <button
            v-else
            class="shrink-0 flex items-center gap-1 px-3 py-2 rounded-lg bg-indigo-500 text-white text-xs font-bold"
            :disabled="busy"
            @click="emit('go', bookmark)"
          >
            <Play :size="12" /> Read
          </button>
        </template>
      </li>
    </ul>

    <!-- Continue: or just the last place read -->
    <button
      v-if="mode === 'continue'"
      class="w-full py-2.5 rounded-xl text-sm font-bold border"
      :style="{ borderColor: `${theme.muted}40` }"
      @click="emit('continue-last')"
    >
      Last position<template v-if="lastProgress != null"> ({{ Math.round(lastProgress * 100) }}%)</template>
    </button>

    <!-- Add a sticker here -->
    <template v-else>
      <div v-if="adding" class="space-y-2">
        <p class="text-[10px] font-black uppercase tracking-widest" :style="{ color: theme.muted }">New sticker at this page</p>
        <div class="flex gap-2">
          <input
            ref="addInput"
            v-model="newLabel"
            maxlength="200"
            placeholder="e.g. Old Testament, Matej 7"
            class="flex-1 min-w-0 rounded-xl px-3 py-2 text-sm outline-none border focus:border-indigo-500"
            :style="inputStyle"
            @keydown.enter="submitAdd"
          />
          <button class="px-4 rounded-xl bg-indigo-500 text-white text-sm font-bold disabled:opacity-40" :disabled="!newLabel.trim() || busy" @click="submitAdd">
            Add
          </button>
        </div>
      </div>
      <button
        v-else
        class="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-bold bg-indigo-500 text-white disabled:opacity-50"
        :disabled="busy"
        @click="startAdd"
      >
        <Plus :size="16" /> Add sticker here
      </button>
      <p v-if="bookmarks.length > 1" class="text-[11px]" :style="{ color: theme.muted }">
        Book progress counts from your earliest sticker.
      </p>
    </template>
  </div>
</template>
