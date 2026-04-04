import { useQuery } from '@tanstack/react-query'
import { fetchSignals, type ApiSignal } from '@/lib/api'
import {
  SIGNALS,
  COMMAND_SIGNALS,
  TRIGGER_RULES,
  type IntelSignal,
  type CommandSignal,
  type TriggerRule,
} from '@/data/mockData'

/** Map event_type to a human-readable signal type label. */
function signalTypeLabel(eventType: string): string {
  if (eventType.includes('cluster')) return 'OWNER CLUSTER'
  if (eventType.includes('subdivision')) return 'SUBDIVISION REMNANT'
  if (eventType.includes('price') || eventType.includes('reduction')) return 'PRICE REDUCTION'
  if (eventType.includes('municipal')) return 'MUNICIPAL EVENT'
  if (eventType.includes('bbo') || eventType.includes('remarks')) return 'PACKAGE LANGUAGE'
  if (eventType.includes('stall')) return 'STALLED SUBDIVISION'
  if (eventType.includes('listing')) return 'LISTING SIGNAL'
  return eventType.replace(/_/g, ' ').toUpperCase()
}

/** Relative time from ISO string. */
function timeAgo(isoStr: string): string {
  const diff = Date.now() - new Date(isoStr).getTime()
  const mins = Math.floor(diff / 60_000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

function toIntelSignal(s: ApiSignal): IntelSignal {
  const rules = s.fired_rules ? JSON.parse(s.fired_rules) : []
  return {
    type: signalTypeLabel(s.event_type),
    timestamp: timeAgo(s.created_at),
    title: s.entity_ref_summary || s.event_type.replace(/_/g, ' '),
    description: rules.length > 0
      ? `Fired rules: ${rules.join(', ')}. ${s.payload_summary || ''}`
      : s.payload_summary || s.event_type,
    tier: rules.length >= 2 ? 1 : 2,
  }
}

function toCommandSignal(s: ApiSignal): CommandSignal {
  const rules = s.fired_rules ? JSON.parse(s.fired_rules) : []
  const typeLabel = signalTypeLabel(s.event_type)
  return {
    type: typeLabel,
    typeColor: typeLabel.includes('CLUSTER') || typeLabel.includes('PRICE')
      ? 'bg-primary/10 text-primary'
      : 'bg-[#059669]/10 text-[#059669]',
    timestamp: timeAgo(s.created_at),
    title: s.entity_ref_summary || s.event_type.replace(/_/g, ' '),
    description: s.payload_summary || `${rules.length} rules fired`,
    action: 'View Detail',
  }
}

export function useSignals() {
  return useQuery({
    queryKey: ['signals'],
    queryFn: async () => {
      const res = await fetchSignals(20)
      if (res.signals.length > 0) {
        return res.signals.slice(0, 8).map(toIntelSignal)
      }
      return SIGNALS
    },
    staleTime: 30_000,
    refetchInterval: 30_000,
  })
}

export function useCommandSignals() {
  return useQuery({
    queryKey: ['signals', 'command'],
    queryFn: async () => {
      const res = await fetchSignals(10)
      if (res.signals.length > 0) {
        return res.signals.slice(0, 5).map(toCommandSignal)
      }
      return COMMAND_SIGNALS
    },
    staleTime: 30_000,
    refetchInterval: 30_000,
  })
}

export function useTriggerRules() {
  return useQuery({
    queryKey: ['trigger-rules'],
    queryFn: async () => TRIGGER_RULES as TriggerRule[],
    staleTime: 30_000,
  })
}
