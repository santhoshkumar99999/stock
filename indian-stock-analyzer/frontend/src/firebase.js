import { initializeApp } from "firebase/app";
import { getMessaging, getToken, isSupported, onMessage } from "firebase/messaging";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "YOUR_API_KEY",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "indian-stock-analyzer.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "indian-stock-analyzer",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "indian-stock-analyzer.appspot.com",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "YOUR_SENDER_ID",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "YOUR_APP_ID",
};

const VAPID_KEY = import.meta.env.VITE_FIREBASE_VAPID_KEY || "YOUR_VAPID_KEY_HERE";
const app = initializeApp(firebaseConfig);

async function getMessagingIfSupported() {
  const supported = await isSupported();
  return supported ? getMessaging(app) : null;
}

export async function requestNotificationPermission() {
  try {
    const permission = await Notification.requestPermission();
    if (permission !== "granted") {
      return null;
    }

    const messaging = await getMessagingIfSupported();
    if (!messaging) {
      return null;
    }

    const token = await getToken(messaging, {
      vapidKey: VAPID_KEY,
      serviceWorkerRegistration: await navigator.serviceWorker.register("/firebase-messaging-sw.js"),
    });

    if (!token) {
      return null;
    }

    await fetch("/api/fcm/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    });
    return token;
  } catch (err) {
    console.error("FCM setup error:", err);
    return null;
  }
}

export async function onForegroundMessage(callback) {
  const messaging = await getMessagingIfSupported();
  if (!messaging) {
    return () => {};
  }
  return onMessage(messaging, (payload) => {
    callback(payload);
  });
}
