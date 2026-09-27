import type { LinkingOptions } from '@react-navigation/native';

export const linking: LinkingOptions<{}> = {
  prefixes: ['fieldnotes://'],
  config: {
    screens: {
      SignIn: 'sign-in',
      Main: {
        screens: {
          Feed: '',
          Profile: 'me',
        },
      },
      Details: 'notes/:id',
    },
  },
};
