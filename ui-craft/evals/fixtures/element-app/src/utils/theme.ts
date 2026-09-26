export function applyPrimary(color: string) {
  document.documentElement.style.setProperty('--el-color-primary', color);
  localStorage.setItem('theme-primary', color);
}
