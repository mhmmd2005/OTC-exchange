import type { PaginatedResult, PaginationParams } from '@/types'

let sequence = 10_000

export function createMockId(prefix: string): string {
  sequence += 1
  return `${prefix}_${Date.now().toString(36)}_${sequence.toString(36)}`
}

export function nowIso(): string {
  return new Date().toISOString()
}

export function futureIso(seconds: number): string {
  return new Date(Date.now() + seconds * 1_000).toISOString()
}

export function normalizedSearch(value?: string): string {
  return (value ?? '').trim().toLocaleLowerCase('fa')
}

export function paginate<T>(items: T[], params: PaginationParams = {}): PaginatedResult<T> {
  const pageSize = Math.max(1, Math.min(100, Math.trunc(params.pageSize ?? 10)))
  const total = items.length
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const page = Math.max(1, Math.min(totalPages, Math.trunc(params.page ?? 1)))
  const start = (page - 1) * pageSize

  return {
    items: items.slice(start, start + pageSize),
    page,
    pageSize,
    total,
    totalPages,
  }
}

