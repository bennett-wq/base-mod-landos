import { useQuery } from '@tanstack/react-query'
import { SIGNALS, COMMAND_SIGNALS, TRIGGER_RULES } from '@/data/mockData'

export function useSignals() {
  return useQuery({
    queryKey: ['signals'],
    queryFn: async () => SIGNALS,
    staleTime: 30_000,
    refetchInterval: 10_000,
  })
}

export function useCommandSignals() {
  return useQuery({
    queryKey: ['signals', 'command'],
    queryFn: async () => COMMAND_SIGNALS,
    staleTime: 30_000,
    refetchInterval: 10_000,
  })
}

export function useTriggerRules() {
  return useQuery({
    queryKey: ['trigger-rules'],
    queryFn: async () => TRIGGER_RULES,
    staleTime: 30_000,
  })
}
