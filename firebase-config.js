// Cloud sync config. Optional.
//
// Left as null, the app behaves exactly as it always has: it reads
// places.js and saves your edits to localStorage in this browser only.
// Fill this in to share one live list across devices.
//
// Setup, roughly ten minutes:
//   1. console.firebase.google.com -> Create a project (decline Analytics)
//   2. Build -> Firestore Database -> Create database -> Native mode, us-west1
//   3. Project settings -> Your apps -> Web -> register, copy the config object
//   4. Paste it below, replacing null
//   5. Authentication -> Sign-in method -> enable Google, pick a support email
//   6. Authentication -> Settings -> Authorized domains -> add mmm.molendino.com
//   7. Firestore -> Rules -> paste firestore.rules from this repo, with the
//      email addresses that should have access
//
// The apiKey below is NOT a secret. It identifies the project; it does not
// grant access to anything. Access is controlled entirely by the security
// rules in firestore.rules. It is safe to commit and safe to serve publicly.

window.FIREBASE_CONFIG = {
  apiKey: "AIzaSyBf2Tpi2JaT8_da5e1w2E7jpGSeNJALcTA",
  authDomain: "magic-munch-map.firebaseapp.com",
  projectId: "magic-munch-map",
  storageBucket: "magic-munch-map.firebasestorage.app",
  messagingSenderId: "376760392499",
  appId: "1:376760392499:web:5fd2a09f139b6ff7083c46",
  measurementId: "G-JG1FYNS3FK"
};

