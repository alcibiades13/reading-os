<script setup>
import { ref, computed } from 'vue'
import { Star } from 'lucide-vue-next'

const props = defineProps({
  modelValue: {
    type: [Number, String],
    default: 0
  },
  maxStars: {
    type: Number,
    default: 10
  },
  readonly: {
    type: Boolean,
    default: false
  },
  size: {
    type: Number,
    default: 20
  },
  showValue: {
    type: Boolean,
    default: false
  }
})

// Convert modelValue to number if it's a string
const ratingValue = computed(() => {
  return typeof props.modelValue === 'string' ? parseFloat(props.modelValue) : props.modelValue
})

const emit = defineEmits(['update:modelValue'])

const clickTimeout = ref(null)
const clickCount = ref(0)
const hoveredStar = ref(0)

const stars = computed(() => {
  const result = []
  for (let i = 1; i <= props.maxStars; i++) {
    const fillPercentage = calculateFillPercentage(i)
    result.push({
      id: i,
      fill: fillPercentage
    })
  }
  return result
})

const calculateFillPercentage = (starIndex) => {
  const rating = ratingValue.value

  // If hovering and not readonly, show current value (preserve half stars)
  if (!props.readonly && hoveredStar.value > 0) {
    // If hovering over current star, show current value
    if (hoveredStar.value === starIndex) {
      // Show half or full based on current value
      if (rating >= starIndex) {
        return 100 // Full star
      } else if (rating >= starIndex - 0.5) {
        return 50 // Half star
      }
    } else if (hoveredStar.value > starIndex) {
      return 100 // Stars before hovered star are full
    }
  }

  // Normal rendering when not hovering
  if (rating >= starIndex) {
    return 100 // Full star
  } else if (rating >= starIndex - 0.5) {
    return 50 // Half star
  }
  return 0 // Empty star
}

const handleMouseEnter = (starIndex) => {
  if (!props.readonly) {
    hoveredStar.value = starIndex
  }
}

const handleMouseLeave = () => {
  hoveredStar.value = 0
}

const handleStarClick = (starIndex) => {
  if (props.readonly) return

  clickCount.value++

  if (clickTimeout.value) {
    clearTimeout(clickTimeout.value)
  }

  clickTimeout.value = setTimeout(() => {
    if (clickCount.value >= 2) {
      // Double click - half star
      const newValue = starIndex - 0.5
      emit('update:modelValue', newValue)
    } else {
      // Single click - full star
      const newValue = starIndex
      emit('update:modelValue', newValue)
    }
    clickCount.value = 0
  }, 250) // 250ms delay to detect double click
}

const getStarColor = (fillPercentage) => {
  if (fillPercentage > 0) {
    return 'text-amber-400'
  }
  return props.readonly ? 'text-slate-700' : 'text-slate-600 hover:text-amber-400'
}
</script>

<template>
  <div class="flex items-center gap-1">
    <div class="flex items-center gap-0.5" @mouseleave="handleMouseLeave">
      <button
        v-for="star in stars"
        :key="star.id"
        type="button"
        @click="handleStarClick(star.id)"
        @mouseenter="handleMouseEnter(star.id)"
        :class="[
          'relative transition-colors',
          readonly ? 'cursor-default' : 'cursor-pointer'
        ]"
        :disabled="readonly"
      >
        <!-- Background (empty) star -->
        <Star
          :size="size"
          :class="getStarColor(0)"
          :fill="star.fill === 0 ? 'none' : 'transparent'"
        />

        <!-- Overlay for filled portion -->
        <div
          v-if="star.fill > 0"
          class="absolute inset-0 overflow-hidden"
          :style="{ width: `${star.fill}%` }"
        >
          <Star
            :size="size"
            class="text-amber-400"
            fill="currentColor"
          />
        </div>
      </button>
    </div>

    <span
      v-if="showValue && ratingValue > 0"
      class="text-sm font-bold text-amber-400 ml-1 min-w-[2rem]"
    >
      {{ ratingValue.toFixed(1) }}
    </span>
  </div>
</template>
