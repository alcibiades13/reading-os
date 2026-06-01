import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.readingos.app',
  appName: 'Reading OS',
  webDir: 'dist',
  server: {
    androidScheme: 'http',
    cleartext: true
  },
  plugins: {
    CapacitorHttp: {
      enabled: true
    },
    BarcodeScanner: {
      // Uses Google ML Kit — no extra config needed beyond camera permission
    }
  }
};

export default config;
