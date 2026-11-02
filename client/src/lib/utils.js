import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

// Merge conditional class lists, letting later Tailwind classes win over
// earlier conflicting ones (e.g. a caller's `px-2` replaces a default `px-4`).
export function cn(...inputs) {
  return twMerge(clsx(inputs))
}
