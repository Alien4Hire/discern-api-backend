import 'dotenv/config';

export default {
  expo: {
    name: "discernApp",
    slug: "discernApp",
    version: "1.0.0",
    orientation: "portrait",
    icon: "./assets/images/icon.png",
    scheme: "discernapp",
    userInterfaceStyle: "automatic",
    newArchEnabled: true,
    splash: {
      image: "./assets/images/splash-icon.png",
      resizeMode: "contain",
      backgroundColor: "#ffffff"
    },
    ios: {
      supportsTablet: true
    },
    android: {
      adaptiveIcon: {
        foregroundImage: "./assets/images/adaptive-icon.png",
        backgroundColor: "#ffffff"
      },
      windowSoftInputMode: "adjustResize",
      softwareKeyboardLayoutMode: "resize",
      edgeToEdgeEnabled: true,
      package: "com.alien4hire.discernApp"
    },
    web: {
      bundler: "metro",
      output: "static",
      favicon: "./assets/images/favicon.png"
    },
    plugins: [
      "expo-router",
      "expo-web-browser"
    ],
    experiments: {
      typedRoutes: true
    },
    extra: {
      router: {},
      eas: {
        projectId: "ef764e16-18f0-4b1d-bbe1-3eb646f45357"
      },
      API_BASE_URL: process.env.API_BASE_URL || "http://localhost:8000",
      GOOGLE_WEB_CLIENT_ID: process.env.GOOGLE_CLIENT_ID,
      GOOGLE_ANDROID_CLIENT_ID: process.env.GOOGLE_ANDROID_CLIENT_ID,
      GOOGLE_IOS_CLIENT_ID: process.env.GOOGLE_IOS_CLIENT_ID
    }
  }
}