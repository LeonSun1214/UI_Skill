import { mode } from '@chakra-ui/theme-tools';

export const globalStyles = {
  colors: {
    brand: { 100: '#E9E3FF', 300: '#7551FF', 500: '#422AFB', 700: '#02044A', 900: '#11047A' },
    secondaryGray: { 300: '#F4F7FE', 400: '#E9EDF7', 600: '#A3AED0', 900: '#1B2559' },
    navy: { 500: '#1b3bbb', 800: '#111c44', 900: '#0b1437' },
  },
  fonts: { heading: "'DM Sans', sans-serif", body: "'DM Sans', sans-serif" },
  styles: {
    global: (props) => ({
      body: { bg: mode('secondaryGray.300', 'navy.900')(props), fontFamily: 'DM Sans' },
    }),
  },
};
