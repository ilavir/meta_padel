// PWA Install functionality - Simplified version
let deferredPrompt;

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
    console.log('beforeinstallprompt event fired');
    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();
    // Stash the event so it can be triggered later
    deferredPrompt = e;
});

window.addEventListener('appinstalled', () => {
    console.log('PWA was installed');
    deferredPrompt = null;
});

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
        } else {
            console.log('User dismissed the install prompt');
        }
        deferredPrompt = null;
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