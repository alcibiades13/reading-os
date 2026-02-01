import { ref, watch } from 'vue'

const isOpen = ref(false)

export function useMobileSidebar() {
  const open = () => { isOpen.value = true }
  const close = () => { isOpen.value = false }
  const toggle = () => { isOpen.value = !isOpen.value }

  // Prevent body scroll when mobile sidebar is open
  watch(isOpen, (val) => {
    if (val) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  })

  return { isOpen, open, close, toggle }
}
