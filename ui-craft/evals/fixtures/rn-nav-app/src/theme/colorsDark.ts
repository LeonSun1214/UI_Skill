const palette = {
  moss300: '#5DD39E',
  stone100: '#F7F5F2',
  stone500: '#78716C',
  stone700: '#44403C',
  stone950: '#0C0A09',
} as const;

export const colors = {
  palette,
  text: palette.stone100,
  textDim: palette.stone500,
  background: palette.stone950,
  tint: palette.moss300,
  border: palette.stone700,
} as const;
