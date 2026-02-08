<script setup>
import { computed } from 'vue'
import { Card, CardContent, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { BookOpen, Star, MoreVertical, Edit, Trash2, Heart } from 'lucide-vue-next'
import StarRating from '@/components/ui/StarRating.vue'

const props = defineProps({
  book: {
    type: Object,
    required: true,
  },
  showActions: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['edit', 'delete', 'view', 'toggle-favorite'])

// Support both UserBook structure (book.book) and direct Book structure
const bookData = computed(() => props.book.book || props.book)

// Status badge variants
const statusConfig = {
  want_to_read: { label: 'Want to Read', variant: 'secondary', class: 'bg-sky-500/90 text-white border-0' },
  currently_reading: { label: 'Reading', variant: 'default', class: 'bg-indigo-500 text-white border-0' },
  read: { label: 'Read', variant: 'default', class: 'bg-emerald-500/90 text-white border-0' },
  abandoned: { label: 'Abandoned', variant: 'destructive', class: 'bg-slate-600 text-slate-200 border-0' },
}

const statusInfo = computed(() => statusConfig[props.book.status] || statusConfig.want_to_read)

// Cover image with fallback
const coverImage = computed(() => {
  return bookData.value?.cover_image || null
})

// Authors string
const authorsString = computed(() => {
  return bookData.value?.authors?.map((a) => a.name).join(', ') || 'Unknown Author'
})

// Reading progress percentage
const progressPercent = computed(() => {
  return props.book.reading_progress || 0
})

// No longer needed - using StarRating component
</script>

<template>
  <Card class="group hover:shadow-lg transition-all duration-200 cursor-pointer overflow-hidden">
    <!-- Book cover -->
    <div
      class="relative aspect-[2/3] bg-gradient-to-br from-slate-700 to-slate-800 overflow-hidden flex items-center justify-center"
      @click="emit('view', book)"
    >
      <img
        v-if="coverImage"
        :src="coverImage"
        :alt="bookData?.title"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
        @error="(e) => e.target.style.display = 'none'"
      />
      <BookOpen v-if="!coverImage" :size="32" class="lg:w-12 lg:h-12 text-slate-600" />

      <!-- Favorite heart -->
      <button
        v-if="book.is_favorite"
        class="absolute top-1.5 right-1.5 lg:top-2 lg:right-2 p-1.5 lg:p-2 bg-white/90 rounded-full shadow-md"
        @click.stop="emit('toggle-favorite', book)"
      >
        <Heart class="w-3 h-3 lg:w-4 lg:h-4 text-red-500 fill-red-500" />
      </button>

      <!-- Progress bar for currently reading -->
      <div v-if="book.status === 'currently_reading' && progressPercent > 0" class="absolute bottom-0 left-0 right-0 h-1 bg-black/20">
        <div 
          class="h-full bg-primary transition-all duration-300"
          :style="{ width: `${progressPercent}%` }"
        />
      </div>
    </div>

    <CardContent class="p-2 lg:p-4 space-y-1 lg:space-y-2" @click="emit('view', book)">
      <!-- Title -->
      <h3 class="font-semibold text-[11px] lg:text-sm line-clamp-2 group-hover:text-primary transition-colors leading-tight">
        {{ bookData?.title }}
      </h3>

      <!-- Authors -->
      <p class="text-[10px] lg:text-xs text-muted-foreground line-clamp-1">
        {{ authorsString }}
      </p>

      <!-- Status badge (only for UserBook items with status) -->
      <Badge v-if="book.status && showActions" :variant="statusInfo.variant" :class="['text-[9px] lg:text-xs px-1.5 lg:px-2 py-0.5', statusInfo.class]">
        {{ statusInfo.label }}
      </Badge>

      <!-- Rating -->
      <StarRating
        v-if="book.rating"
        :model-value="book.rating"
        :size="10"
        class="lg:[&>*]:w-3 lg:[&>*]:h-3"
        :readonly="true"
        :show-value="true"
      />

      <!-- Progress info -->
      <div v-if="book.status === 'currently_reading'" class="text-[9px] lg:text-xs text-muted-foreground">
        <div class="flex items-center gap-1">
          <BookOpen class="w-2.5 h-2.5 lg:w-3 lg:h-3 flex-shrink-0" />
          <span class="truncate">{{ book.current_page || 0 }}/{{ bookData?.pages || '?' }} pg</span>
        </div>
      </div>

      <!-- Quotes count -->
      <div v-if="book.quotes_count > 0" class="text-[9px] lg:text-xs text-muted-foreground">
        {{ book.quotes_count }} {{ book.quotes_count === 1 ? 'quote' : 'quotes' }}
      </div>
    </CardContent>

    <CardFooter v-if="showActions" class="p-2 lg:p-4 pt-0 flex justify-between items-center">
      <!-- View button -->
      <Button
        variant="ghost"
        size="sm"
        class="text-[10px] lg:text-sm h-7 lg:h-9 px-2 lg:px-3"
        @click="emit('view', book)"
      >
        <span class="hidden lg:inline">View Details</span>
        <span class="lg:hidden">Details</span>
      </Button>

      <!-- Actions dropdown -->
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <Button variant="ghost" size="icon" class="h-7 w-7 lg:h-9 lg:w-9" @click.stop>
            <MoreVertical class="w-3.5 h-3.5 lg:w-4 lg:h-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem @click="emit('edit', book)">
            <Edit class="w-4 h-4 mr-2" />
            Edit
          </DropdownMenuItem>
          <DropdownMenuItem @click="emit('toggle-favorite', book)">
            <Heart class="w-4 h-4 mr-2" />
            {{ book.is_favorite ? 'Remove from favorites' : 'Add to favorites' }}
          </DropdownMenuItem>
          <DropdownMenuItem
            class="text-destructive focus:text-destructive"
            @click="emit('delete', book)"
          >
            <Trash2 class="w-4 h-4 mr-2" />
            Remove
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </CardFooter>
  </Card>
</template>