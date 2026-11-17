/**
 * SoundWave Global Device Permission Manager
 * Production-ready, Secure, Battery-efficient, Privacy-respecting
 * Handles: Microphone, Geolocation, Notifications, Device Sensors & File Storage
 */

(function(window) {
    'use strict';

    class PermissionManager {
        constructor() {
            this.states = {
                microphone: 'prompt',
                geolocation: 'prompt',
                notifications: 'prompt',
                sensors: 'prompt',
                storage: 'granted'
            };

            this.subscribers = {
                microphone: [],
                geolocation: [],
                notifications: [],
                sensors: [],
                storage: []
            };

            this.services = {};
            this.activeMediaStreams = [];

            // Detect current browser / platform
            this.isAndroid = /android/i.test(navigator.userAgent);
            this.isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
            this.isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);

            // Initial check on load
            this.syncAllStatuses();
        }

        /**
         * Register a service that depends on a permission
         */
        registerService(permName, serviceDef) {
            this.services[permName] = serviceDef;
        }

        /**
         * Subscribe to status changes for a permission
         */
        on(permName, callback) {
            if (this.subscribers[permName]) {
                this.subscribers[permName].push(callback);
                // Immediately notify with current state
                try { callback(this.states[permName]); } catch(e) {}
            }
        }

        /**
         * Broadcast state change to subscribers and UI
         */
        notify(permName, state) {
            this.states[permName] = state;
            if (this.subscribers[permName]) {
                this.subscribers[permName].forEach(cb => {
                    try { cb(state); } catch(e) {}
                });
            }

            // Update any UI badge if present on DOM
            this.updateBadgeUI(permName, state);

            // Dispatch global CustomEvent
            window.dispatchEvent(new CustomEvent('soundwave:permissionChange', {
                detail: { permission: permName, state }
            }));
        }

        /**
         * Query current status of all permissions safely
         */
        async syncAllStatuses() {
            // 1. Microphone
            if (navigator.permissions && navigator.permissions.query) {
                try {
                    const status = await navigator.permissions.query({ name: 'microphone' });
                    this.notify('microphone', status.state);
                    status.onchange = () => this.notify('microphone', status.state);
                } catch(e) {
                    // Fallback: If not queried, check if getUserMedia exists
                    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                        this.notify('microphone', 'unsupported');
                    }
                }
            }

            // 2. Geolocation
            if (navigator.permissions && navigator.permissions.query) {
                try {
                    const status = await navigator.permissions.query({ name: 'geolocation' });
                    this.notify('geolocation', status.state);
                    status.onchange = () => this.notify('geolocation', status.state);
                } catch(e) {
                    if (!navigator.geolocation) {
                        this.notify('geolocation', 'unsupported');
                    }
                }
            } else if (!navigator.geolocation) {
                this.notify('geolocation', 'unsupported');
            }

            // 3. Notifications
            if ('Notification' in window) {
                this.notify('notifications', Notification.permission);
            } else {
                this.notify('notifications', 'unsupported');
            }

            // 4. Sensors (Orientation / Motion)
            if (window.DeviceOrientationEvent) {
                if (typeof DeviceOrientationEvent.requestPermission === 'function') {
                    // iOS 13+ requires explicit user gesture request
                    this.notify('sensors', 'prompt');
                } else {
                    this.notify('sensors', 'granted');
                }
            } else {
                this.notify('sensors', 'unsupported');
            }
        }

        /**
         * Request Microphone Permission safely on user action
         */
        async requestMicrophone(options = { keepStream: false }) {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                this.notify('microphone', 'unsupported');
                this.showHelpModal('microphone', 'Your browser does not support audio recording.');
                return { success: false, reason: 'unsupported' };
            }

            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                this.notify('microphone', 'granted');

                if (options.keepStream) {
                    this.activeMediaStreams.push(stream);
                    return { success: true, stream };
                } else {
                    // Stop tracks immediately to save battery & release privacy indicator
                    stream.getTracks().forEach(t => t.stop());
                    return { success: true };
                }
            } catch(err) {
                const isDenied = (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError');
                const state = isDenied ? 'denied' : 'prompt';
                this.notify('microphone', state);
                if (isDenied) {
                    this.showHelpModal('microphone', 'Microphone access is blocked by your browser or device settings.');
                }
                return { success: false, error: err, isDenied };
            }
        }

        /**
         * Request Geolocation Permission on user action
         */
        requestGeolocation(options = { highAccuracy: true, timeout: 10000 }) {
            return new Promise((resolve) => {
                if (!navigator.geolocation) {
                    this.notify('geolocation', 'unsupported');
                    this.showHelpModal('geolocation', 'Geolocation is not supported by your device.');
                    return resolve({ success: false, reason: 'unsupported' });
                }

                navigator.geolocation.getCurrentPosition(
                    (pos) => {
                        this.notify('geolocation', 'granted');
                        resolve({
                            success: true,
                            coords: {
                                latitude: pos.coords.latitude,
                                longitude: pos.coords.longitude,
                                accuracy: pos.coords.accuracy
                            }
                        });
                    },
                    (err) => {
                        const isDenied = (err.code === err.PERMISSION_DENIED);
                        const state = isDenied ? 'denied' : 'prompt';
                        this.notify('geolocation', state);
                        if (isDenied) {
                            this.showHelpModal('geolocation', 'Location access is blocked. You can still search any city manually.');
                        }
                        resolve({ success: false, error: err, isDenied });
                    },
                    {
                        enableHighAccuracy: options.highAccuracy !== false,
                        timeout: options.timeout || 10000,
                        maximumAge: 60000
                    }
                );
            });
        }

        /**
         * Request Notifications Permission on user action
         */
        async requestNotifications() {
            if (!('Notification' in window)) {
                this.notify('notifications', 'unsupported');
                return { success: false, reason: 'unsupported' };
            }

            try {
                const res = await Notification.requestPermission();
                this.notify('notifications', res);
                if (res === 'denied') {
                    this.showHelpModal('notifications', 'Notifications are blocked in your browser settings.');
                }
                return { success: res === 'granted', status: res };
            } catch(e) {
                return { success: false, error: e };
            }
        }

        /**
         * Request Device Sensors (Orientation / Motion) on user action
         */
        async requestSensors() {
            if (!window.DeviceOrientationEvent) {
                this.notify('sensors', 'unsupported');
                return { success: false, reason: 'unsupported' };
            }

            if (typeof DeviceOrientationEvent.requestPermission === 'function') {
                try {
                    const response = await DeviceOrientationEvent.requestPermission();
                    const state = (response === 'granted') ? 'granted' : 'denied';
                    this.notify('sensors', state);
                    return { success: state === 'granted', status: state };
                } catch(e) {
                    this.notify('sensors', 'denied');
                    return { success: false, error: e };
                }
            } else {
                this.notify('sensors', 'granted');
                return { success: true, status: 'granted' };
            }
        }

        /**
         * Clean up active streams (e.g. microphone)
         */
        releaseMicrophone() {
            if (this.activeMediaStreams && this.activeMediaStreams.length > 0) {
                this.activeMediaStreams.forEach(stream => {
                    try { stream.getTracks().forEach(t => t.stop()); } catch(e) {}
                });
                this.activeMediaStreams = [];
            }
        }

        /**
         * UI Helper: Update Badges inside Settings or App
         */
        updateBadgeUI(permName, state) {
            const badge = document.getElementById(`permBadge_${permName}`);
            const btn = document.getElementById(`permBtn_${permName}`);
            if (!badge) return;

            badge.className = 'perm-status-badge';
            if (state === 'granted') {
                badge.classList.add('status-granted');
                badge.textContent = '🟢 Allowed';
                if (btn) btn.textContent = 'Active ✓';
            } else if (state === 'denied') {
                badge.classList.add('status-denied');
                badge.textContent = '🔴 Blocked';
                if (btn) btn.textContent = 'How to Unblock';
            } else if (state === 'unsupported') {
                badge.classList.add('status-unsupported');
                badge.textContent = '⚪ Not Supported';
                if (btn) btn.textContent = 'Unsupported';
            } else {
                badge.classList.add('status-prompt');
                badge.textContent = '🟡 Not Granted';
                if (btn) btn.textContent = 'Grant Permission';
            }
        }

        /**
         * Instructions on how to unblock permission in browser / device
         */
        getInstructions(permName) {
            const prettyName = permName.charAt(0).toUpperCase() + permName.slice(1);
            if (this.isAndroid) {
                return `
                    <div class="perm-instruction-steps">
                        <p><strong>To enable ${prettyName} on Android / Chrome:</strong></p>
                        <ol>
                            <li>Tap the <strong>Padlock (🔒)</strong> or <strong>Tune</strong> icon in your browser address bar.</li>
                            <li>Tap <strong>Permissions</strong> or <strong>Site Settings</strong>.</li>
                            <li>Find <strong>${prettyName}</strong> and switch it to <strong>Allow</strong>.</li>
                            <li>Or open Android <strong>Settings → Apps → SoundWave / Chrome → Permissions → ${prettyName} → Allow</strong>.</li>
                            <li>Return here and tap <strong>Check Status</strong>.</li>
                        </ol>
                    </div>
                `;
            } else if (this.isIOS) {
                return `
                    <div class="perm-instruction-steps">
                        <p><strong>To enable ${prettyName} on iPhone / Safari:</strong></p>
                        <ol>
                            <li>Tap the <strong>Page Settings (aA)</strong> icon in the address bar.</li>
                            <li>Tap <strong>Website Settings</strong>.</li>
                            <li>Find <strong>${prettyName}</strong> and select <strong>Allow</strong>.</li>
                            <li>Or open iOS <strong>Settings → Safari → ${prettyName} → Allow</strong>.</li>
                            <li>Refresh the page.</li>
                        </ol>
                    </div>
                `;
            } else {
                return `
                    <div class="perm-instruction-steps">
                        <p><strong>To enable ${prettyName} in Chrome, Edge, or Brave:</strong></p>
                        <ol>
                            <li>Click the <strong>Padlock (🔒)</strong> or <strong>Tune (⚙️)</strong> icon to the left of the URL.</li>
                            <li>Toggle <strong>${prettyName}</strong> to <strong>Allow / On</strong>.</li>
                            <li>Reload the page to apply changes.</li>
                        </ol>
                    </div>
                `;
            }
        }

        /**
         * Show Help / Troubleshooting Modal
         */
        showHelpModal(permName, reason = '') {
            let modal = document.getElementById('permissionHelpModal');
            if (!modal) {
                modal = document.createElement('div');
                modal.id = 'permissionHelpModal';
                modal.className = 'sp-modal-overlay';
                modal.innerHTML = `
                    <div class="modal-backdrop-blur" onclick="window.SoundWavePermissions.closeHelpModal()"></div>
                    <div class="perm-help-dialog">
                        <button class="modal-close-btn" onclick="window.SoundWavePermissions.closeHelpModal()">✕</button>
                        <div class="perm-help-header">
                            <div class="perm-help-icon" id="permHelpIcon">🛡️</div>
                            <div>
                                <h3 id="permHelpTitle">Permission Required</h3>
                                <p id="permHelpReason" class="text-sub">Please review hardware access settings</p>
                            </div>
                        </div>
                        <div id="permHelpBody" class="perm-help-body"></div>
                        <div class="perm-help-actions">
                            <button class="btn-perm-check" onclick="window.SoundWavePermissions.syncAllStatuses(); window.SoundWavePermissions.closeHelpModal();">
                                🔄 Check Status Now
                            </button>
                            <button class="btn-perm-close" onclick="window.SoundWavePermissions.closeHelpModal()">
                                Close
                            </button>
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);
            }

            const title = document.getElementById('permHelpTitle');
            const reasonEl = document.getElementById('permHelpReason');
            const body = document.getElementById('permHelpBody');
            const icon = document.getElementById('permHelpIcon');

            const icons = {
                microphone: '🎙️',
                geolocation: '📍',
                notifications: '🔔',
                sensors: '🧭',
                storage: '📦'
            };

            if (icon) icon.textContent = icons[permName] || '🛡️';
            if (title) title.textContent = `${permName.toUpperCase()} Access`;
            if (reasonEl) reasonEl.textContent = reason;
            if (body) body.innerHTML = this.getInstructions(permName);

            modal.classList.remove('hidden');
        }

        closeHelpModal() {
            const modal = document.getElementById('permissionHelpModal');
            if (modal) modal.classList.add('hidden');
        }

        /**
         * Open Settings Modal for all permissions
         */
        openSettingsModal() {
            let modal = document.getElementById('devicePermissionsModal');
            if (modal) {
                modal.classList.remove('hidden');
                this.syncAllStatuses();
                return;
            }
        }
    }

    // Expose Global Singleton
    window.SoundWavePermissions = new PermissionManager();

})(window);
