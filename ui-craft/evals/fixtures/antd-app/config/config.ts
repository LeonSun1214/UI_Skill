import { defineConfig } from '@umijs/max';
import defaultSettings from './defaultSettings';
import routes from './routes';

export default defineConfig({
  routes,
  layout: { ...defaultSettings },
  antd: {
    configProvider: {
      theme: {
        token: { colorPrimary: '#7c3aed', borderRadius: 8, fontFamily: 'Inter, sans-serif' },
        components: { Button: { controlHeight: 40 } },
      },
    },
  },
});
