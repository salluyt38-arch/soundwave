// SoundWave — Firebase Auth & Cloud Firestore Service
// Supports Google Sign-In, Email/Password, Real-time Liked Songs & Subscription Sync across PC and Mobile

(function (window) {
    'use strict';

    // Default placeholder configuration.
    // Users can paste their Firebase project keys here or directly in the App's "Firebase Settings" modal!
    const DEFAULT_CONFIG = {
        apiKey: "YOUR_API_KEY",
        authDomain: "soundwave-stream.firebaseapp.com",
        projectId: "soundwave-stream",
        storageBucket: "soundwave-stream.appspot.com",
        messagingSenderId: "123456789012",
        appId: "1:123456789012:web:abcdef123456"
    };

    const STORAGE_KEY_FB_CONFIG = 'soundwave_firebase_config_custom';
    const STORAGE_KEY_AUTH_USER = 'soundwave_cached_firebase_user';

    class SoundWaveFirebaseService {
        constructor() {
            this.app = null;
            this.auth = null;
            this.db = null;
            this.currentUser = null;
            this.isConfigured = false;
            this.authListeners = [];
            this.firestoreUnsubscribe = null;
            this.init();
        }

        getConfig() {
            try {
                const saved = localStorage.getItem(STORAGE_KEY_FB_CONFIG);
                if (saved) {
                    const parsed = JSON.parse(saved);
                    if (parsed && parsed.apiKey && parsed.projectId) {
                        return parsed;
                    }
                }
            } catch (e) {
                console.warn('Error reading stored Firebase config:', e);
            }
            return DEFAULT_CONFIG;
        }

        saveConfig(newConfig) {
            try {
                localStorage.setItem(STORAGE_KEY_FB_CONFIG, JSON.stringify(newConfig));
                this.init();
                return true;
            } catch (e) {
                console.error('Failed to save Firebase config:', e);
                return false;
            }
        }

        resetConfig() {
            localStorage.removeItem(STORAGE_KEY_FB_CONFIG);
            this.init();
        }

        init() {
            const config = this.getConfig();
            this.isConfigured = Boolean(
                config.apiKey &&
                !config.apiKey.includes('YOUR_API_KEY') &&
                config.projectId &&
                !config.projectId.includes('YOUR_PROJECT')
            );

            if (typeof firebase === 'undefined') {
                console.warn('Firebase SDK scripts not loaded yet.');
                return;
            }

            try {
                // Initialize or retrieve existing app
                if (!firebase.apps.length) {
                    this.app = firebase.initializeApp(config);
                } else {
                    this.app = firebase.app();
                }

                this.auth = firebase.auth();
                this.db = firebase.firestore();

                // Setup Auth state listener
                this.auth.onAuthStateChanged((user) => {
                    this.currentUser = user;
                    if (user) {
                        localStorage.setItem(STORAGE_KEY_AUTH_USER, JSON.stringify({
                            uid: user.uid,
                            email: user.email,
                            displayName: user.displayName || user.email.split('@')[0],
                            photoURL: user.photoURL || ''
                        }));
                        this.startFirestoreSync(user.uid);
                    } else {
                        localStorage.removeItem(STORAGE_KEY_AUTH_USER);
                        if (this.firestoreUnsubscribe) {
                            this.firestoreUnsubscribe();
                            this.firestoreUnsubscribe = null;
                        }
                    }
                    this.notifyAuthListeners(user);
                });

                console.log(`[SoundWave Firebase] Initialized (${this.isConfigured ? 'Live Mode' : 'Setup Mode'})`);
            } catch (err) {
                console.warn('[SoundWave Firebase] Init warning:', err.message);
            }
        }

        onAuthStateChanged(callback) {
            if (typeof callback === 'function') {
                this.authListeners.push(callback);
                // Call immediately with cached or current user if available
                callback(this.currentUser || this.getCachedUser());
            }
        }

        notifyAuthListeners(user) {
            this.authListeners.forEach(cb => {
                try {
                    cb(user);
                } catch (e) {
                    console.error('Error in auth listener:', e);
                }
            });
        }

        getCachedUser() {
            try {
                const raw = localStorage.getItem(STORAGE_KEY_AUTH_USER);
                return raw ? JSON.parse(raw) : null;
            } catch (e) {
                return null;
            }
        }

        // ================= AUTH METHODS =================

        async loginWithGoogle() {
            if (!this.isConfigured || !this.auth) {
                // Friendly simulated login in Setup Mode so user can preview full functionality!
                return this.simulateDemoLogin('Google User', 'google.user@example.com', 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100');
            }

            try {
                const provider = new firebase.auth.GoogleAuthProvider();
                provider.addScope('profile');
                provider.addScope('email');
                const result = await this.auth.signInWithPopup(provider);
                return { success: true, user: result.user };
            } catch (error) {
                console.error('Google Sign-In Error:', error);
                // If popup was blocked or domain not authorized, fallback to redirect or return error
                return { success: false, error: error.message };
            }
        }

        async loginWithEmail(email, password) {
            if (!this.isConfigured || !this.auth) {
                return this.simulateDemoLogin(email.split('@')[0], email, 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100');
            }

            try {
                const result = await this.auth.signInWithEmailAndPassword(email, password);
                return { success: true, user: result.user };
            } catch (error) {
                console.error('Email Login Error:', error);
                return { success: false, error: error.message };
            }
        }

        async signupWithEmail(email, password, displayName) {
            if (!this.isConfigured || !this.auth) {
                return this.simulateDemoLogin(displayName || email.split('@')[0], email, 'https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=100');
            }

            try {
                const result = await this.auth.createUserWithEmailAndPassword(email, password);
                if (displayName && result.user) {
                    await result.user.updateProfile({ displayName: displayName });
                }
                return { success: true, user: result.user };
            } catch (error) {
                console.error('Email Signup Error:', error);
                return { success: false, error: error.message };
            }
        }

        async logout() {
            if (this.auth && this.isConfigured) {
                try {
                    await this.auth.signOut();
                } catch (e) {
                    console.error('Firebase signout error:', e);
                }
            }
            this.currentUser = null;
            localStorage.removeItem(STORAGE_KEY_AUTH_USER);
            if (this.firestoreUnsubscribe) {
                this.firestoreUnsubscribe();
                this.firestoreUnsubscribe = null;
            }
            this.notifyAuthListeners(null);
            return { success: true };
        }

        simulateDemoLogin(name, email, photo) {
            const demoUser = {
                uid: 'demo_' + Math.random().toString(36).substring(2, 9),
                displayName: name,
                email: email,
                photoURL: photo,
                isDemo: true
            };
            this.currentUser = demoUser;
            localStorage.setItem(STORAGE_KEY_AUTH_USER, JSON.stringify(demoUser));
            this.notifyAuthListeners(demoUser);
            return {
                success: true,
                user: demoUser,
                isDemoNotice: 'Demo session active. Connect your real Firebase project keys in settings for permanent cloud storage!'
            };
        }

        // ================= CLOUD FIRESTORE SYNC =================

        startFirestoreSync(uid) {
            if (!this.isConfigured || !this.db) return;

            try {
                const userDocRef = this.db.collection('soundwave_users').doc(uid);

                // Listen to remote changes in real-time
                this.firestoreUnsubscribe = userDocRef.onSnapshot((doc) => {
                    if (doc.exists) {
                        const data = doc.data();
                        window.dispatchEvent(new CustomEvent('soundwave:remote-data-sync', {
                            detail: {
                                likedSongs: data.likedSongs || [],
                                subscription: data.subscription || null,
                                updatedAt: data.updatedAt
                            }
                        }));
                    } else {
                        // First time user: initialize cloud document with local state
                        window.dispatchEvent(new CustomEvent('soundwave:request-initial-push'));
                    }
                }, (error) => {
                    console.warn('Firestore snapshot error:', error.message);
                });
            } catch (err) {
                console.warn('Firestore sync failed to start:', err.message);
            }
        }

        async pushUserDataToCloud(data) {
            if (!this.currentUser) return { success: false, reason: 'Not logged in' };

            // In demo mode, local storage serves as virtual cloud
            if (!this.isConfigured || !this.db || this.currentUser.isDemo) {
                try {
                    localStorage.setItem(`soundwave_cloud_mock_${this.currentUser.uid}`, JSON.stringify(data));
                    return { success: true, mode: 'demo-local' };
                } catch (e) {
                    return { success: false, error: e.message };
                }
            }

            try {
                const userDocRef = this.db.collection('soundwave_users').doc(this.currentUser.uid);
                await userDocRef.set({
                    email: this.currentUser.email,
                    displayName: this.currentUser.displayName,
                    photoURL: this.currentUser.photoURL || '',
                    likedSongs: data.likedSongs || [],
                    subscription: data.subscription || null,
                    updatedAt: firebase.firestore.FieldValue.serverTimestamp()
                }, { merge: true });

                return { success: true, mode: 'firestore' };
            } catch (error) {
                console.error('Failed to push to Firestore:', error);
                return { success: false, error: error.message };
            }
        }
    }

    // Attach singleton to window
    window.SoundWaveFirebase = new SoundWaveFirebaseService();

})(window);
