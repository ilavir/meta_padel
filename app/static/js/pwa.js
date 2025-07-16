// PWA Install functionality
let deferredPrompt;
let installButtonDiv;
let isInstallable = false;

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

// Check if browser supports PWA installation
function isPWASupported() {
    // Firefox doesn't support beforeinstallprompt event
    const isFirefox = navigator.userAgent.toLowerCase().includes('firefox');
    if (isFirefox) {
        console.log('Firefox detected - PWA install not supported');
        return false;
    }
    
    // Check for basic PWA support
    return 'serviceWorker' in navigator && 'BeforeInstallPromptEvent' in window;
}

// Check if app is already installed
function isAppInstalled() {
    // Multiple checks for installed state
    const standaloneMode = window.matchMedia('(display-mode: standalone)').matches;
    const iosStandalone = window.navigator.standalone === true;
    const androidStandalone = document.referrer.includes('android-app://');
    
    return standaloneMode || iosStandalone || androidStandalone;
}

// Check if app was previously installed (localStorage tracking)
function wasAppInstalled() {
    return localStorage.getItem('pwa-installed') === 'true';
}

// PWA Install prompt handling
window.addEventListener('beforeinstallprompt', (e) => {
    console.log('beforeinstallprompt event fired');
    
    // Don't show if already installed
    if (isAppInstalled() || wasAppInstalled()) {
        console.log('App already installed, not showing install prompt');
        return;
    }
    
    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();
    // Stash the event so it can be triggered later
    deferredPrompt = e;
    isInstallable = true;
    // Enable the install button if it exists
    enableInstallButton();
});

window.addEventListener('appinstalled', () => {
    console.log('PWA was installed');
    // Mark as installed in localStorage
    localStorage.setItem('pwa-installed', 'true');
    // Disable the install button after successful installation
    disableInstallButton();
    isInstallable = false;
    deferredPrompt = null;
});

function enableInstallButton() {
    installButtonDiv = document.getElementById('pwa-install-div');
    const installButton = document.getElementById('pwa-install-btn');
    if (installButtonDiv && installButton && isPWASupported() && !isAppInstalled() && !wasAppInstalled()) {
        installButton.disabled = false;
        console.log('Install button enabled');
    }
}

function disableInstallButton() {
    const installButton = document.getElementById('pwa-install-btn');
    if (installButton) {
        installButton.disabled = true;
        console.log('Install button disabled');
    }
}

function installPWA() {
    console.log('Install PWA clicked');
    
    if (!deferredPrompt) {
        console.log('No deferred prompt available');
        // Show manual installation instructions for unsupported browsers
        showManualInstallInstructions();
        return;
    }
    
    // Show the install prompt
    deferredPrompt.prompt();
    
    // Wait for the user to respond to the prompt
    deferredPrompt.userChoice.then((choiceResult) => {
        console.log('User choice:', choiceResult.outcome);
        if (choiceResult.outcome === 'accepted') {
            console.log('User accepted the install prompt');
            localStorage.setItem('pwa-installed', 'true');
        } else {
            console.log('User dismissed the install prompt');
        }
        deferredPrompt = null;
        isInstallable = false;
        disableInstallButton();
    });
}

function showManualInstallInstructions() {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    const isAndroid = /Android/.test(navigator.userAgent);
    
    let message = 'Для установки приложения:\n\n';
    
    if (isIOS) {
        message += '1. Нажмите кнопку "Поделиться" в Safari\n';
        message += '2. Выберите "На экран Домой"\n';
        message += '3. Нажмите "Добавить"';
    } else if (isAndroid) {
        message += '1. Откройте меню браузера (⋮)\n';
        message += '2. Выберите "Добавить на главный экран"\n';
        message += '3. Нажмите "Добавить"';
    } else {
        message += 'Откройте это приложение в Chrome или Edge для установки';
    }
    
    alert(message);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, checking install state');
    console.log('PWA supported:', isPWASupported());
    console.log('App installed:', isAppInstalled());
    console.log('Was app installed:', wasAppInstalled());
    
    // Check if install button exists (only for non-logged users)
    const installButton = document.getElementById('pwa-install-btn');
    if (!installButton) {
        console.log('Install button not found - user is logged in');
        return;
    }
    
    // Initially disable the button until we know if installation is possible
    installButton.disabled = true;
    
    // Don't enable install button if:
    // - PWA not supported
    // - App already installed
    // - App was previously installed
    if (!isPWASupported() || isAppInstalled() || wasAppInstalled()) {
        console.log('Install not available due to conditions');
        installButton.disabled = true;
        return;
    }
    
    // For supported browsers, wait for beforeinstallprompt event
    // If event doesn't fire within 3 seconds, keep button disabled
    setTimeout(() => {
        if (!isInstallable && !deferredPrompt) {
            console.log('No install prompt available after timeout');
            installButton.disabled = true;
        }
    }, 3000);
});