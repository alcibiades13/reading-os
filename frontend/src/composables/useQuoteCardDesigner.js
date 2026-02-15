import { ref, computed } from 'vue'

export function useQuoteCardDesigner() {
  const selectedTemplate = ref('classic')
  const selectedBackground = ref('grad-indigo-night')
  const selectedFont = ref('playfair')
  const selectedAspectRatio = ref('square')
  const fontSizeAdjust = ref(0) // -5 to +5 steps, each step = 15%
  const isGenerating = ref(false)

  // ── Layout Templates ──────────────────────────────────
  const templates = [
    {
      id: 'classic',
      label: 'Classic',
      description: 'Centered, elegant, timeless',
    },
    {
      id: 'editorial',
      label: 'Editorial',
      description: 'Magazine-style with accent border',
    },
    {
      id: 'minimal',
      label: 'Minimal',
      description: 'Ultra-clean, maximum whitespace',
    },
    {
      id: 'bold',
      label: 'Bold',
      description: 'Dramatic, text fills the card',
    },
  ]

  // ── Backgrounds ───────────────────────────────────────
  const backgrounds = [
    // Gradients
    { id: 'grad-indigo-night', name: 'Indigo Night', category: 'gradient', style: { background: 'linear-gradient(135deg, #0f172a 0%, #312e81 50%, #1e1b4b 100%)' }, textColor: 'white', preview: '#312e81' },
    { id: 'grad-ocean', name: 'Deep Ocean', category: 'gradient', style: { background: 'linear-gradient(135deg, #0c4a6e 0%, #0f172a 50%, #164e63 100%)' }, textColor: 'white', preview: '#0c4a6e' },
    { id: 'grad-ember', name: 'Ember', category: 'gradient', style: { background: 'linear-gradient(135deg, #1c1917 0%, #7c2d12 50%, #1c1917 100%)' }, textColor: 'white', preview: '#7c2d12' },
    { id: 'grad-forest', name: 'Forest', category: 'gradient', style: { background: 'linear-gradient(135deg, #052e16 0%, #14532d 50%, #022c22 100%)' }, textColor: 'white', preview: '#14532d' },
    { id: 'grad-aurora', name: 'Aurora', category: 'gradient', style: { background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 33%, #0f766e 66%, #1e1b4b 100%)' }, textColor: 'white', preview: '#0f766e' },
    { id: 'grad-sunset', name: 'Sunset', category: 'gradient', style: { background: 'linear-gradient(135deg, #1e1b4b 0%, #831843 50%, #9a3412 100%)' }, textColor: 'white', preview: '#831843' },
    // Solids
    { id: 'solid-midnight', name: 'Midnight', category: 'solid', style: { background: '#0f172a' }, textColor: 'white', preview: '#0f172a' },
    { id: 'solid-ink', name: 'Ink', category: 'solid', style: { background: '#02040a' }, textColor: 'white', preview: '#02040a' },
    { id: 'solid-slate', name: 'Slate', category: 'solid', style: { background: '#1e293b' }, textColor: 'white', preview: '#1e293b' },
    { id: 'solid-cream', name: 'Cream', category: 'solid', style: { background: '#fef3c7' }, textColor: 'dark', preview: '#fef3c7' },
    { id: 'solid-white', name: 'White', category: 'solid', style: { background: '#ffffff' }, textColor: 'dark', preview: '#ffffff' },
    { id: 'solid-paper', name: 'Paper', category: 'solid', style: { background: '#f5f0e8' }, textColor: 'dark', preview: '#f5f0e8' },
    // Patterns (CSS-only)
    { id: 'pattern-dots', name: 'Dotted', category: 'pattern', style: { background: '#0f172a', backgroundImage: 'radial-gradient(circle, rgba(99,102,241,0.15) 1px, transparent 1px)', backgroundSize: '24px 24px' }, textColor: 'white', preview: '#0f172a' },
    { id: 'pattern-grid', name: 'Grid', category: 'pattern', style: { background: '#0f172a', backgroundImage: 'linear-gradient(rgba(99,102,241,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(99,102,241,0.08) 1px, transparent 1px)', backgroundSize: '32px 32px' }, textColor: 'white', preview: '#0f172a' },
  ]

  // ── Fonts ─────────────────────────────────────────────
  const fonts = [
    { id: 'playfair', name: 'Playfair Display', family: '"Playfair Display", serif', preview: 'The beauty of words...' },
    { id: 'lora', name: 'Lora', family: 'Lora, serif', preview: 'The beauty of words...' },
    { id: 'crimson', name: 'Crimson Text', family: '"Crimson Text", serif', preview: 'The beauty of words...' },
    { id: 'garamond', name: 'EB Garamond', family: '"EB Garamond", serif', preview: 'The beauty of words...' },
    { id: 'inter', name: 'Inter', family: 'Inter, sans-serif', preview: 'The beauty of words...' },
  ]

  // ── Aspect Ratios ─────────────────────────────────────
  const aspectRatios = [
    { id: 'square', label: 'Square', ratio: '1:1', width: 1080, height: 1080 },
    { id: 'story', label: 'Story', ratio: '9:16', width: 1080, height: 1920 },
    { id: 'landscape', label: 'Wide', ratio: '16:9', width: 1200, height: 675 },
  ]

  // ── Computed ──────────────────────────────────────────
  const currentBackground = computed(() =>
    backgrounds.find(b => b.id === selectedBackground.value)
  )

  const currentFont = computed(() =>
    fonts.find(f => f.id === selectedFont.value)
  )

  const currentAspectRatio = computed(() =>
    aspectRatios.find(a => a.id === selectedAspectRatio.value)
  )

  const isDarkText = computed(() =>
    currentBackground.value?.textColor === 'dark'
  )

  // Dynamic font size based on text length, card dimensions, and template
  const getQuoteFontSize = (textLength, cardWidth, cardHeight) => {
    const base = cardWidth * 0.04

    // Aspect ratio adjustments
    const ratio = cardHeight / cardWidth
    // Story: massive vertical space, boost heavily so text is readable
    // Wide: keep width-based sizing
    const ratioBoost = ratio > 1.4 ? 1.6 : 1.0

    let size = base * ratioBoost
    if (selectedTemplate.value === 'bold') {
      if (textLength > 200) size *= 0.7
      else if (textLength > 100) size *= 1.0
      else size *= 1.4
    } else {
      if (textLength > 400) size *= 0.6
      else if (textLength > 250) size *= 0.75
      else if (textLength > 150) size *= 0.85
    }

    // Apply manual adjustment: each step = 15%
    size *= (1 + fontSizeAdjust.value * 0.15)

    return Math.max(size, 10)
  }

  // ── Image Generation ──────────────────────────────────
  const downloadImage = async (element, bookTitle) => {
    isGenerating.value = true
    try {
      await document.fonts.ready
      const html2canvas = (await import('html2canvas')).default

      // Clone element outside any transform context to avoid
      // html2canvas rendering artifacts from parent scale()
      const clone = element.cloneNode(true)
      clone.style.position = 'fixed'
      clone.style.left = '-9999px'
      clone.style.top = '0'
      clone.style.transform = 'none'
      document.body.appendChild(clone)

      const canvas = await html2canvas(clone, {
        scale: 2,
        useCORS: true,
        backgroundColor: null,
        logging: false,
      })

      document.body.removeChild(clone)

      const link = document.createElement('a')
      const slug = (bookTitle || 'quote').replace(/[^a-zA-Z0-9]+/g, '-').toLowerCase().slice(0, 40)
      link.download = `quote-${slug}.png`
      link.href = canvas.toDataURL('image/png')
      link.click()
    } finally {
      isGenerating.value = false
    }
  }

  return {
    selectedTemplate,
    selectedBackground,
    selectedFont,
    selectedAspectRatio,
    fontSizeAdjust,
    isGenerating,
    templates,
    backgrounds,
    fonts,
    aspectRatios,
    currentBackground,
    currentFont,
    currentAspectRatio,
    isDarkText,
    getQuoteFontSize,
    downloadImage,
  }
}
