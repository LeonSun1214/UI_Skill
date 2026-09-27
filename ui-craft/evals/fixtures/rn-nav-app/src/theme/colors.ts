const palette = {
  moss100: '#E3EFE6',
  moss500: '#0B6E4F',
  moss700: '#07513A',
  stone100: '#F7F5F2',
  stone400: '#A8A29E',
  stone600: '#57534E',
  stone900: '#1C1917',
} as const;

export const colors = {
  palette,
  text: palette.stone900,
  textDim: palette.stone600,
  background: palette.stone100,
  tint: palette.moss500,
  border: palette.stone400,
} as const;
