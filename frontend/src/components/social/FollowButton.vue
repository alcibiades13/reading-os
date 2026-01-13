<script setup>
import { ref, computed, watch } from 'vue'
import { UserPlus, UserCheck, UserX, Clock } from 'lucide-vue-next'

const props = defineProps({
  userId: {
    type: [Number, String],
    required: true
  },
  initialState: {
    type: String,
    default: 'not_following', // 'not_following' | 'following' | 'pending' | 'mutual'
    validator: (value) => ['not_following', 'following', 'pending', 'mutual'].includes(value)
  },
  isFollower: {
    type: Boolean,
    default: false
  },
  size: {
    type: String,
    default: 'default', // 'small' | 'default' | 'large'
    validator: (value) => ['small', 'default', 'large'].includes(value)
  },
  variant: {
    type: String,
    default: 'default', // 'default' | 'ghost'
    validator: (value) => ['default', 'ghost'].includes(value)
  }
})

const emit = defineEmits(['follow', 'unfollow', 'update'])

const followState = ref(props.initialState)
const isLoading = ref(false)

// Watch for changes to initialState prop and update internal state
watch(() => props.initialState, (newState) => {
  followState.value = newState
})

const buttonConfig = computed(() => {
  const configs = {
    not_following: {
      label: props.isFollower ? 'Follow Back' : 'Follow',
      icon: UserPlus,
      class: 'bg-indigo-500 text-white hover:bg-indigo-400 shadow-lg shadow-indigo-500/20'
    },
    following: {
      label: 'Following',
      icon: UserCheck,
      class: 'bg-white/5 text-slate-400 hover:bg-red-500/10 hover:text-red-400 border border-white/10'
    },
    pending: {
      label: 'Requested',
      icon: Clock,
      class: 'bg-amber-500/10 text-amber-400 border border-amber-500/20 cursor-not-allowed'
    },
    mutual: {
      label: 'Friends',
      icon: UserCheck,
      class: 'bg-emerald-500/10 text-emerald-400 hover:bg-red-500/10 hover:text-red-400 border border-emerald-500/20'
    }
  }
  return configs[followState.value]
})

const sizeClasses = computed(() => {
  const sizes = {
    small: 'px-3 py-1.5 text-[10px] rounded-lg',
    default: 'px-6 py-2.5 text-xs rounded-xl',
    large: 'px-8 py-3.5 text-sm rounded-2xl'
  }
  return sizes[props.size]
})

const handleClick = async () => {
  if (followState.value === 'pending') return // Can't unfollow pending request
  if (isLoading.value) return

  isLoading.value = true

  try {
    if (followState.value === 'not_following') {
      // Follow user
      await emit('follow', props.userId)
      followState.value = 'following' // or 'pending' if account is private
      emit('update', 'following')
    } else if (followState.value === 'following' || followState.value === 'mutual') {
      // Unfollow user
      await emit('unfollow', props.userId)
      followState.value = 'not_following'
      emit('update', 'not_following')
    }
  } catch (error) {
    console.error('Error toggling follow:', error)
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <button
    @click="handleClick"
    :disabled="followState === 'pending' || isLoading"
    :class="[
      'font-black uppercase tracking-widest transition-all duration-300 flex items-center gap-2 active:scale-95',
      sizeClasses,
      buttonConfig.class,
      isLoading && 'opacity-50 cursor-wait'
    ]"
  >
    <!-- Loading Spinner -->
    <div v-if="isLoading" class="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />

    <!-- Icon -->
    <component v-else :is="buttonConfig.icon" :size="size === 'small' ? 14 : size === 'large' ? 18 : 16" />

    <!-- Label -->
    <span class="hidden sm:inline">{{ buttonConfig.label }}</span>
  </button>
</template>

<style scoped>
/* Hover text change for Following button */
button:hover .following-text {
  display: none;
}
button:hover .unfollow-text {
  display: inline;
}
</style>
