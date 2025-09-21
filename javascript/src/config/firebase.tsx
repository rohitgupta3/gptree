import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyB7wZrsxn1Kj96a-Zs3pcHRV04-vSldh3Q",
  authDomain: "gptree-a6771.firebaseapp.com",
  projectId: "gptree-a6771",
  storageBucket: "gptree-a6771.firebasestorage.app",
  messagingSenderId: "542750643665",
  appId: "1:542750643665:web:743921904a37a857e17cf0",
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
