<script setup>
import { ref, computed } from 'vue'
import { Calendar as CalendarIcon } from 'lucide-vue-next'
import { Calendar } from '@/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { DateFormatter, parseDate, getLocalTimeZone } from '@internationalized/date'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Pick a date'
  }
})

const emit = defineEmits(['update:modelValue'])

const open = ref(false)

const df = new DateFormatter('en-US', {
  dateStyle: 'medium',
})

// Convert string date to CalendarDate object for Calendar component
const date = computed({
  get: () => {
    if (!props.modelValue) return undefined
    try {
      // Parse YYYY-MM-DD format to CalendarDate
      return parseDate(props.modelValue)
    } catch (e) {
      return undefined
    }
  },
  set: (val) => {
    if (val) {
      // CalendarDate object has toString() that returns YYYY-MM-DD
      emit('update:modelValue', val.toString())
      open.value = false
    } else if (val === null || val === undefined) {
      emit('update:modelValue', '')
      open.value = false
    }
  }
})

const formattedDate = computed(() => {
  if (!props.modelValue) return props.placeholder
  try {
    const calDate = parseDate(props.modelValue)
    return df.format(calDate.toDate(getLocalTimeZone()))
  } catch (e) {
    return props.placeholder
  }
})
</script>

<template>
  <Popover v-model:open="open">
    <PopoverTrigger as-child>
      <Button
        variant="outline"
        :class="cn(
          'w-full justify-start text-left font-normal',
          !date && 'text-muted-foreground'
        )"
        class="bg-slate-950/50 border-slate-700 text-slate-200 hover:bg-slate-900 hover:border-indigo-600 hover:text-slate-100"
      >
        <CalendarIcon class="mr-2 h-4 w-4 text-slate-500" />
        <span>{{ formattedDate }}</span>
      </Button>
    </PopoverTrigger>
    <PopoverContent class="w-auto p-0 bg-slate-900 border-slate-700" align="start">
      <Calendar
        v-model="date"
        initial-focus
        :fixed-weeks="true"
        class="bg-slate-900 rounded-md"
      />
    </PopoverContent>
  </Popover>
</template>
