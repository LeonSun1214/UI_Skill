import { defineStore } from 'pinia'
const KEY = 'fixture-theme'
export const useThemeStore = defineStore('theme', {
  state: () => ({ dark: localStorage.getItem(KEY) === 'dark' }),
  actions: { toggle() { this.dark = !this.dark; localStorage.setItem(KEY, this.dark ? 'dark' : 'light') } },
})
