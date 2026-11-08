import { computed, ref, watch, type ComputedRef, type Ref } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'system'
export type ResolvedTheme = 'light' | 'dark'

const STORAGE_KEY = 'ri:theme'
const ORDER: ThemeMode[] = ['light', 'dark', 'system']

function readStored(): ThemeMode {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    if (value === 'light' || value === 'dark' || value === 'system') return value
  } catch {
    // Storage unavailable (private window, blocked site data): use the default.
  }
  return 'system'
}

function writeStored(value: ThemeMode): void {
  try {
    localStorage.setItem(STORAGE_KEY, value)
  } catch {
    // Not persisted; the choice still applies for this page view.
  }
}

const media =
  typeof window !== 'undefined' && typeof window.matchMedia === 'function'
    ? window.matchMedia('(prefers-color-scheme: dark)')
    : null

// Module-level state so every caller shares one theme.
const theme = ref<ThemeMode>(readStored())
const systemPrefersDark = ref(media?.matches ?? false)

const resolved = computed<ResolvedTheme>(() => {
  if (theme.value === 'system') return systemPrefersDark.value ? 'dark' : 'light'
  return theme.value
})

function applyClass(mode: ResolvedTheme): void {
  document.documentElement.classList.toggle('dark', mode === 'dark')
}

let initialized = false

/** Call once before mounting the app. Applies the stored theme and follows the OS setting. */
export function initTheme(): void {
  if (initialized) return
  initialized = true
  media?.addEventListener('change', (event) => {
    systemPrefersDark.value = event.matches
  })
  watch(resolved, applyClass, { immediate: true })
  watch(theme, writeStored)
}

export function useTheme(): {
  theme: Ref<ThemeMode>
  resolved: ComputedRef<ResolvedTheme>
  setTheme: (mode: ThemeMode) => void
  cycle: () => void
} {
  function setTheme(mode: ThemeMode): void {
    theme.value = mode
  }

  /** light -> dark -> system -> light */
  function cycle(): void {
    const index = ORDER.indexOf(theme.value)
    setTheme(ORDER[(index + 1) % ORDER.length])
  }

  return { theme, resolved, setTheme, cycle }
}
