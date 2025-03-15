import { initializeApp } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-app.js";
import { getAuth, 
         GoogleAuthProvider } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-firestore.js";


const firebaseConfig = {
  apiKey: "AIzaSyDiOO6GF4EXsYct4TU6FmIibPVh8t_BuSs",
  authDomain: "elevate-labs-cc9eb.firebaseapp.com",
  projectId: "elevate-labs-cc9eb",
  storageBucket: "elevate-labs-cc9eb.firebasestorage.app",
  messagingSenderId: "388835595942",
  appId: "1:388835595942:web:44c82b46a4e09f77d2c667",
  measurementId: "G-J4PLP0FLNN"
};
  // Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

const db = getFirestore(app);

export { auth, provider, db };