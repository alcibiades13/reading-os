import { Shield, Hexagon } from 'lucide-vue-next'

export const TIERS = {
  reader: {
    label: 'Reader',
    bg: 'bg-slate-500/10',
    text: 'text-slate-400',
    fill: 'fill-slate-400',
    border: 'border-slate-500/20',
    borderStrong: 'border-slate-500/30',
    icon: Hexagon,
    color: '#94a3b8',
  },
  contributor: {
    label: 'Contributor',
    bg: 'bg-indigo-500/10',
    text: 'text-indigo-400',
    fill: 'fill-indigo-400',
    border: 'border-indigo-500/20',
    borderStrong: 'border-indigo-500/30',
    icon: Hexagon,
    color: '#818cf8',
  },
  curator: {
    label: 'Curator',
    bg: 'bg-purple-500/10',
    text: 'text-purple-400',
    fill: 'fill-purple-400',
    border: 'border-purple-500/20',
    borderStrong: 'border-purple-500/30',
    icon: Shield,
    color: '#a78bfa',
  },
  moderator: {
    label: 'Moderator',
    bg: 'bg-rose-500/10',
    text: 'text-rose-400',
    fill: 'fill-rose-400',
    border: 'border-rose-500/20',
    borderStrong: 'border-rose-500/30',
    icon: Shield,
    color: '#fb7185',
  },
}

export const DEFAULT_TIER = TIERS.reader

export function getTier(tierKey) {
  return TIERS[tierKey] || DEFAULT_TIER
}

export function tierClasses(tierKey) {
  const t = getTier(tierKey)
  return `${t.bg} ${t.borderStrong} ${t.text}`
}
