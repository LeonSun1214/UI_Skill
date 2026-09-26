import { defineStore } from 'pinia';
import { useDark, useToggle } from '@vueuse/core';

const isDark = useDark();
const toggleDark = useToggle(isDark);

export const useSettingsStore = defineStore('settings', {
  state: () => ({ isDark }),
  actions: { toggleTheme() { toggleDark(); } },
});
