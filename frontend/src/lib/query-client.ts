'use client'

import { QueryClient } from '@tanstack/react-query'

let client: QueryClient | null = null

export function getQueryClient(): QueryClient {
  if (!client) {
    client = new QueryClient({
      defaultOptions: {
        queries: {
          staleTime: 60 * 1000,        // 1 min
          gcTime:    5 * 60 * 1000,    // 5 min
          retry: 1,
          refetchOnWindowFocus: false,
        },
      },
    })
  }
  return client
}
