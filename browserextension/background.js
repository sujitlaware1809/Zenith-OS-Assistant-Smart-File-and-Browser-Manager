// Background script for Browser Statistics extension

// Initialize any data storage when the extension is installed
chrome.runtime.onInstalled.addListener(function() {
    console.log('Browser Statistics extension installed');
    
    // Initialize local storage with default values
    chrome.storage.local.set({
        'installDate': new Date().toISOString(),
        'lastUsed': new Date().toISOString(),
        'usageCount': 0,
        'tabHistory': [],
        'systemInfo': {}
    });
    
    // Set up listener for first run
    collectInitialStats();
});

// Listen for browser startup
chrome.runtime.onStartup.addListener(function() {
    console.log('Browser started with Browser Statistics extension');
    updateLastUsed();
    captureSystemInfo();
});

// Function to collect initial statistics when extension is installed
function collectInitialStats() {
    // Count tabs
    chrome.tabs.query({}, function(tabs) {
        chrome.storage.local.set({
            'initialTabCount': tabs.length
        });
        
        // Record initial tab count in history
        recordTabsHistory(tabs.length);
    });
    
    // Count history entries
    const oneMonthAgo = new Date().getTime() - (30 * 24 * 60 * 60 * 1000);
    chrome.history.search({
        text: '',
        startTime: oneMonthAgo,
        maxResults: 1000
    }, function(historyItems) {
        chrome.storage.local.set({
            'initialHistoryCount': historyItems.length
        });
    });
    
    // Count downloads
    chrome.downloads.search({
        limit: 1000,
        orderBy: ['-startTime']
    }, function(downloadItems) {
        chrome.storage.local.set({
            'initialDownloadCount': downloadItems.length
        });
    });
    
    // Capture system information
    captureSystemInfo();
}

// Update last used timestamp whenever popup is opened
chrome.runtime.onMessage.addListener(function(message, sender, sendResponse) {
    if (message.action === 'popup_opened') {
        updateLastUsed();
    } else if (message.action === 'get_system_info') {
        chrome.storage.local.get(['systemInfo'], function(result) {
            sendResponse(result.systemInfo || {});
        });
        return true; // Required for async sendResponse
    }
});

// Function to update last used timestamp and usage count
function updateLastUsed() {
    chrome.storage.local.get(['usageCount'], function(result) {
        const newCount = (result.usageCount || 0) + 1;
        
        chrome.storage.local.set({
            'lastUsed': new Date().toISOString(),
            'usageCount': newCount
        });
    });
}

// Function to record tabs history
function recordTabsHistory(count) {
    chrome.storage.local.get(['tabHistory'], function(result) {
        let history = result.tabHistory || [];
        
        // Add new entry
        history.push({
            timestamp: new Date().toISOString(),
            count: count
        });
        
        // Limit to last 100 entries
        if (history.length > 100) {
            history = history.slice(-100);
        }
        
        chrome.storage.local.set({
            'tabHistory': history
        });
    });
}

// Function to capture system information
function captureSystemInfo() {
    const systemInfo = {
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        language: navigator.language,
        doNotTrack: navigator.doNotTrack,
        cookieEnabled: navigator.cookieEnabled,
        hardwareConcurrency: navigator.hardwareConcurrency || 'unknown',
        captureTime: new Date().toISOString()
    };
    
    chrome.storage.local.set({
        'systemInfo': systemInfo
    });
}

// Listen for tab creation and removal to keep statistics
chrome.tabs.onCreated.addListener(function(tab) {
    chrome.tabs.query({}, function(tabs) {
        recordTabsHistory(tabs.length);
    });
});

chrome.tabs.onRemoved.addListener(function(tabId, removeInfo) {
    chrome.tabs.query({}, function(tabs) {
        recordTabsHistory(tabs.length);
    });
});

// Set up periodic stats collection (every 15 minutes)
setInterval(function() {
    collectPeriodicStats();
}, 15 * 60 * 1000); // 15 minutes in milliseconds

// Function to collect periodic statistics
function collectPeriodicStats() {
    const timestamp = new Date().toISOString();
    
    // Get current tab count
    chrome.tabs.query({}, function(tabs) {
        // Update tab history
        recordTabsHistory(tabs.length);
        
        // Store hourly tab count in a rolling array
        chrome.storage.local.get(['hourlyTabCounts'], function(result) {
            let hourlyTabCounts = result.hourlyTabCounts || [];
            
            // Limit to last 24 entries (24 hours)
            if (hourlyTabCounts.length >= 24) {
                hourlyTabCounts.shift(); // Remove oldest entry
            }
            
            hourlyTabCounts.push({
                timestamp: timestamp,
                count: tabs.length
            });
            
            chrome.storage.local.set({
                'hourlyTabCounts': hourlyTabCounts
            });
        });
    });
    
    // Update system info periodically
    captureSystemInfo();
}