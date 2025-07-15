// PWA Install functionality
let deferredPrompt;
let installButtonDiv;

// Service Worker registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(registration => {
                console.log('Service Worker registered with scope:', registration.scope);
            })
            .catch(error => {
                console.error('Service Worker registration failed:', error);
            });
    });
}

// PWA Install prompt handling
window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();
    // Stash the event so it can be triggered later
    deferredPrompt = e;
    // Show the install button div
    showInstallButton();
});

window.addEventListener('appinstalled', () => {
    // Hide the install button div after successful installation
    hideInstallButton();
    console.log('PWA was installed');
});

function showInstallButton() {
    installButtonDiv = document.getElementById('pwa-install-div');
    if (installButtonDiv) {
        installButtonDiv.style.display = 'block';
    }
}

function hideInstallButton() {
    installButtonDiv = document.getElementById('pwa-install-div');
    if (installButtonDiv) {
        installButtonDiv.style.display = 'none';
    }
}

function installPWA() {
    if (deferredPrompt) {
        // Show the install prompt
        deferredPrompt.prompt();
        // Wait for the user to respond to the prompt
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('User accepted the install prompt');
            } else {
                console.log('User dismissed the install prompt');
            }
            deferredPrompt = null;
        });
    }
}

// Check if app is already installed
function isAppInstalled() {
    // Check if running in standalone mode (installed PWA)
    return window.matchMedia('(display-mode: standalone)').matches || 
           window.navigator.standalone === true;
}

// Hide install button div if app is already installed
document.addEventListener('DOMContentLoaded', () => {
    if (isAppInstalled()) {
        hideInstallButton();
    }
});