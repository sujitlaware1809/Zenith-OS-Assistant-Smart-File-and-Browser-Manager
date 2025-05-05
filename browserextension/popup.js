// Main initialization function
document.addEventListener('DOMContentLoaded', function() {
    // Load all data when popup opens
    loadAllData();
    
    // Set up refresh button
    document.getElementById('refresh-btn').addEventListener('click', loadAllData);
    
    // Set up close tabs button
    document.getElementById('close-tabs-btn').addEventListener('click', closeSelectedTabs);
    
    // Set up tab switching
    setupTabNavigation();
    
    // Set up system info detection
    if (document.getElementById('system-content')) {
        detectSystemInfo();
    }
    
    // Initialize device orientation detection
    if (window.DeviceOrientationEvent) {
        initDeviceOrientation();
    }

    // Initialize speech recognition
    initSpeechRecognition();
});

// Function to setup tab navigation
function setupTabNavigation() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons
            tabButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            button.classList.add('active');
            
            // Hide all tab contents
            tabContents.forEach(content => content.classList.add('hidden'));
            
            // Show the corresponding tab content
            const tabId = button.getAttribute('data-tab');
            document.getElementById(`${tabId}-content`).classList.remove('hidden');
        });
    });
}

// Function to load all browser data
function loadAllData() {
    getTabsInfo();
    getHistoryInfo();
    getDownloadsInfo();
    getUsageStats();
}

// Function to get and display tabs information with checkboxes for deletion
function getTabsInfo() {
    chrome.tabs.query({}, function(tabs) {
        // Update tab count
        const tabCount = tabs.length;
        document.getElementById('tab-count').textContent = tabCount;
        
        // Count domains
        const domains = {};
        tabs.forEach(tab => {
            try {
                const url = new URL(tab.url);
                const domain = url.hostname;
                domains[domain] = (domains[domain] || 0) + 1;
            } catch (e) {
                // Handle invalid URLs
            }
        });
        
        // Get the top domains
        const domainEntries = Object.entries(domains);
        domainEntries.sort((a, b) => b[1] - a[1]);
        
        const topDomains = domainEntries.slice(0, 3);
        let domainText = '';
        
        if (topDomains.length > 0) {
            domainText = `Top domains: ${topDomains.map(d => 
                `${d[0].replace('www.', '')} (${d[1]})`).join(', ')}`;
        } else {
            domainText = 'No domains found';
        }
        
        document.getElementById('tab-domains').textContent = domainText;
        
        // Create tabs list with checkboxes for deletion
        const tabsList = document.getElementById('open-tabs-list');
        if (!tabsList) return;
        
        tabsList.innerHTML = ''; // Clear previous content
        
        if (tabs.length === 0) {
            tabsList.innerHTML = '<div class="loading">No open tabs found.</div>';
            return;
        }
        
        // Show all open tabs with checkboxes
        tabs.forEach(tab => {
            const tabItem = document.createElement('div');
            tabItem.className = 'tab-item';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'checkbox';
            checkbox.dataset.tabId = tab.id;
            
            const favicon = document.createElement('img');
            favicon.className = 'favicon';
            favicon.src = tab.favIconUrl || 'icons/icon16.png';
            favicon.onerror = function() {
                this.src = 'icons/icon16.png';
            };
            
            const tabInfo = document.createElement('div');
            tabInfo.className = 'tab-info';
            
            const title = document.createElement('div');
            title.className = 'title';
            title.textContent = tab.title || 'Untitled Tab';
            
            const url = document.createElement('div');
            url.className = 'url';
            url.textContent = tab.url;
            
            tabInfo.appendChild(title);
            tabInfo.appendChild(url);
            
            tabItem.appendChild(checkbox);
            tabItem.appendChild(favicon);
            tabItem.appendChild(tabInfo);
            tabsList.appendChild(tabItem);
        });
    });
}

// Function to close selected tabs
function closeSelectedTabs() {
    const checkboxes = document.querySelectorAll('.checkbox:checked');
    const tabIds = Array.from(checkboxes).map(checkbox => parseInt(checkbox.dataset.tabId));
    
    if (tabIds.length === 0) {
        alert('Please select at least one tab to close');
        return;
    }
    
    const confirmMessage = `Close ${tabIds.length} selected tab${tabIds.length > 1 ? 's' : ''}?`;
    if (confirm(confirmMessage)) {
        chrome.tabs.remove(tabIds, function() {
            // Reload tab information after closing tabs
            getTabsInfo();
            getUsageStats();
        });
    }
}

// Function to get and display history information
function getHistoryInfo() {
    // Get history from the last 7 days
    const oneWeekAgo = new Date().getTime() - (7 * 24 * 60 * 60 * 1000);
    
    chrome.history.search({
        text: '',              // Search all history
        startTime: oneWeekAgo, // From one week ago
        maxResults: 100        // Limit results
    }, function(historyItems) {
        // Update history count
        document.getElementById('history-count').textContent = historyItems.length;
        
        // Create history list
        const historyList = document.getElementById('history-list');
        if (!historyList) return;
        
        historyList.innerHTML = ''; // Clear previous content
        
        if (historyItems.length === 0) {
            historyList.innerHTML = '<div class="loading">No history items found.</div>';
            return;
        }
        
        // Show the most recent 10 history items
        historyItems.slice(0, 10).forEach(item => {
            const historyItem = document.createElement('div');
            historyItem.className = 'stat-item';
            
            const title = document.createElement('div');
            title.className = 'title';
            title.textContent = item.title || 'Untitled Page';
            
            const url = document.createElement('div');
            url.className = 'url';
            url.textContent = item.url;
            
            const visitDate = new Date(item.lastVisitTime);
            const meta = document.createElement('div');
            meta.className = 'meta';
            meta.textContent = `Visited: ${visitDate.toLocaleString()}`;
            
            historyItem.appendChild(title);
            historyItem.appendChild(url);
            historyItem.appendChild(meta);
            historyList.appendChild(historyItem);
        });
        
        // Create history chart
        createHistoryChart(historyItems);
    });
}

// Function to create history chart
function createHistoryChart(historyItems) {
    const historyChartElement = document.getElementById('history-chart');
    if (!historyChartElement) return;
    
    // Group by day
    const days = {};
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    
    historyItems.forEach(item => {
        const date = new Date(item.lastVisitTime);
        const day = date.getDay();
        days[day] = (days[day] || 0) + 1;
    });
    
    // Prepare data for chart
    const labels = [];
    const data = [];
    
    for (let i = 0; i < 7; i++) {
        const dayIndex = (new Date().getDay() - i + 7) % 7; // Last 7 days
        labels.unshift(dayNames[dayIndex]);
        data.unshift(days[dayIndex] || 0);
    }
    
    // Create chart
    if (window.historyChart) {
        window.historyChart.destroy();
    }
    
    window.historyChart = new Chart(historyChartElement, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Visited Pages',
                data: data,
                backgroundColor: '#1a73e8',
                borderColor: '#1557b0',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

// Function to get and display downloads information
function getDownloadsInfo() {
    chrome.downloads.search({
        limit: 10,
        orderBy: ['-startTime']
    }, function(downloadItems) {
        // Update download count
        document.getElementById('download-count').textContent = downloadItems.length;
        
        // Create downloads list
        const downloadList = document.getElementById('download-list');
        if (!downloadList) return;
        
        downloadList.innerHTML = ''; // Clear previous content
        
        if (downloadItems.length === 0) {
            downloadList.innerHTML = '<div class="loading">No recent downloads found.</div>';
            return;
        }
        
        downloadItems.forEach(item => {
            const downloadItem = document.createElement('div');
            downloadItem.className = 'stat-item';
            
            // Extract filename from download path
            const filename = item.filename.split('\\').pop().split('/').pop();
            
            const title = document.createElement('div');
            title.className = 'title';
            title.textContent = filename;
            
            const meta = document.createElement('div');
            meta.className = 'meta';
            
            // Format file size
            let fileSize = 'Unknown size';
            if (item.fileSize) {
                const fileSizeInKB = item.fileSize / 1024;
                if (fileSizeInKB < 1024) {
                    fileSize = fileSizeInKB.toFixed(2) + ' KB';
                } else {
                    fileSize = (fileSizeInKB / 1024).toFixed(2) + ' MB';
                }
            }
            
            const downloadDate = new Date(item.startTime);
            meta.textContent = `${fileSize} • Downloaded: ${downloadDate.toLocaleString()}`;
            
            downloadItem.appendChild(title);
            downloadItem.appendChild(meta);
            downloadList.appendChild(downloadItem);
        });
    });
}

// Function to get and display browser usage statistics
function getUsageStats() {
    // Get storage usage data
    chrome.storage.local.getBytesInUse(null, function(bytesInUse) {
        const usageStats = document.getElementById('usage-stats');
        if (!usageStats) return;
        
        usageStats.innerHTML = ''; // Clear previous content
        
        // Create usage statistics items
        addUsageItem(usageStats, 'Chrome Storage Used', formatBytes(bytesInUse));
        
        // Add tab count as a usage stat
        chrome.tabs.query({}, function(tabs) {
            addUsageItem(usageStats, 'Open Tabs', tabs.length);
            
            // Count windows
            chrome.windows.getAll(function(windows) {
                addUsageItem(usageStats, 'Browser Windows', windows.length);
                
                // Count incognito windows
                const incognitoCount = windows.filter(win => win.incognito).length;
                if (incognitoCount > 0) {
                    addUsageItem(usageStats, 'Incognito Windows', incognitoCount);
                }
                
                // Create usage chart
                createUsageChart(tabs);
            });
        });
    });
}

// Function to create usage chart
function createUsageChart(tabs) {
    const usageChartElement = document.getElementById('usage-chart');
    if (!usageChartElement) return;
    
    // Group tabs by domain
    const domains = {};
    tabs.forEach(tab => {
        try {
            const url = new URL(tab.url);
            const domain = url.hostname.replace('www.', '');
            domains[domain] = (domains[domain] || 0) + 1;
        } catch (e) {
            // Handle invalid URLs
        }
    });
    
    // Get top 5 domains
    const domainEntries = Object.entries(domains);
    domainEntries.sort((a, b) => b[1] - a[1]);
    
    const topDomains = domainEntries.slice(0, 5);
    const otherCount = domainEntries.slice(5).reduce((sum, entry) => sum + entry[1], 0);
    
    // Prepare data for chart
    const labels = topDomains.map(entry => entry[0]);
    const data = topDomains.map(entry => entry[1]);
    
    if (otherCount > 0) {
        labels.push('Other');
        data.push(otherCount);
    }
    
    // Create chart
    if (window.usageChart) {
        window.usageChart.destroy();
    }
    
    window.usageChart = new Chart(usageChartElement, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#1a73e8',
                    '#34a853',
                    '#fbbc05',
                    '#ea4335',
                    '#9c27b0',
                    '#607d8b'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 10,
                        font: {
                            size: 10
                        }
                    }
                }
            }
        }
    });
}

// Helper function to add usage statistic item
function addUsageItem(container, label, value) {
    const item = document.createElement('div');
    item.className = 'usage-item';
    
    const labelElement = document.createElement('div');
    labelElement.className = 'usage-label';
    labelElement.textContent = label;
    
    const valueElement = document.createElement('div');
    valueElement.className = 'usage-value';
    valueElement.textContent = value;
    
    item.appendChild(labelElement);
    item.appendChild(valueElement);
    container.appendChild(item);
}

// Helper function to format bytes to human-readable format
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// System Info Tab Functions
function detectSystemInfo() {
    // Detect OS
    const userAgent = navigator.userAgent;
    let osInfo = "Unknown";
    
    if (userAgent.indexOf("Win") !== -1) osInfo = "Windows";
    if (userAgent.indexOf("Windows NT 10") !== -1) osInfo = "Windows 10";
    if (userAgent.indexOf("Mac") !== -1) osInfo = "macOS";
    if (userAgent.indexOf("Linux") !== -1) osInfo = "Linux";
    if (userAgent.indexOf("Android") !== -1) osInfo = "Android";
    if (userAgent.indexOf("iOS") !== -1) osInfo = "iOS";
    
    document.getElementById('os-info').textContent = osInfo;
    
    // Detect Browser
    let browserInfo = "Unknown";
    const browserVersion = getBrowserVersion();
    
    if (userAgent.indexOf("Chrome") !== -1) browserInfo = `Chrome ${browserVersion}`;
    if (userAgent.indexOf("Firefox") !== -1) browserInfo = `Firefox ${browserVersion}`;
    if (userAgent.indexOf("Safari") !== -1 && userAgent.indexOf("Chrome") === -1) browserInfo = `Safari ${browserVersion}`;
    if (userAgent.indexOf("Edge") !== -1) browserInfo = `Edge ${browserVersion}`;
    
    document.getElementById('browser-info').textContent = browserInfo;
    
    // Get plugins info
    const pluginsInfo = Array.from(navigator.plugins).map(plugin => plugin.name).join(', ');
    document.getElementById('plugins-info').textContent = pluginsInfo || "No plugins detected";
    
    // Detect hardware info
    document.getElementById('cpu-info').textContent = `Win32, ${navigator.hardwareConcurrency} Cores`;
    
    // Detect display info
    document.getElementById('display-info').textContent = `${window.screen.width} x ${window.screen.height} - ${window.screen.colorDepth}bits/pixel`;
    
    // Detect GPU info (requires canvas)
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    
    if (gl) {
        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        if (debugInfo) {
            const vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
            const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
            document.getElementById('gpu-info').textContent = `Vendor: ${vendor} Renderer: ${renderer}`;
        } else {
            document.getElementById('gpu-info').textContent = "WebGL info unavailable";
        }
    }
    
    // Detect battery
    if (navigator.getBattery) {
        navigator.getBattery().then(battery => {
            updateBatteryInfo(battery);
            
            // Add battery event listeners
            battery.addEventListener('chargingchange', () => updateBatteryInfo(battery));
            battery.addEventListener('levelchange', () => updateBatteryInfo(battery));
        });
    } else {
        document.getElementById('battery-info').textContent = "Battery API not supported";
    }
    
    // Detect connection info
    document.getElementById('referrer-info').textContent = document.referrer || "Direct navigation";
    
    // Public IP detection (we'll simulate this for privacy reasons)
    document.getElementById('ip-info').textContent = "157.51.125.202"; // Use a simulated IP
    
    // Speed test (simulated)
    document.getElementById('speed-info').textContent = "17103.14 kbps";
    
    // Detect social media logins (simulated)
    const socialInfo = document.getElementById('social-info');
    socialInfo.innerHTML = `
        <div class="info-item">
            <span class="info-label">Google:</span>
            <span class="info-value">logged in</span>
        </div>
        <div class="info-item">
            <span class="info-label">Flickr:</span>
            <span class="info-value">logged in</span>
        </div>
    `;
}

// Function to update battery information
function updateBatteryInfo(battery) {
    const batteryLevel = Math.floor(battery.level * 100);
    const isCharging = battery.charging ? "charging" : "discharging";
    const chargingTime = battery.chargingTime === Infinity ? "Infinity" : formatTime(battery.chargingTime);
    
    document.getElementById('battery-info').innerHTML = `
        Charging: ${isCharging}<br>
        Battery Level: ${batteryLevel}%<br>
        Charging Time: ${chargingTime}
    `;
}

// Function to get browser version
function getBrowserVersion() {
    const userAgent = navigator.userAgent;
    let offset, version = "";
    
    if ((offset = userAgent.indexOf("Chrome")) !== -1) {
        version = userAgent.substring(offset + 7);
    } else if ((offset = userAgent.indexOf("Firefox")) !== -1) {
        version = userAgent.substring(offset + 8);
    } else if ((offset = userAgent.indexOf("Safari")) !== -1) {
        version = userAgent.substring(offset + 7);
    } else if ((offset = userAgent.indexOf("Edge")) !== -1) {
        version = userAgent.substring(offset + 5);
    }
    
    if ((offset = version.indexOf(";")) !== -1) {
        version = version.substring(0, offset);
    }
    if ((offset = version.indexOf(" ")) !== -1) {
        version = version.substring(0, offset);
    }
    if ((offset = version.indexOf(")")) !== -1) {
        version = version.substring(0, offset);
    }
    
    return version;
}

// Helper function to format time
function formatTime(seconds) {
    if (seconds === Infinity) return "Infinity";
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    seconds = Math.floor(seconds % 60);
    
    return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m ${seconds}s`;
}

// Device Orientation Functions
function initDeviceOrientation() {
    const orientationStatus = document.getElementById('orientation-status');
    const alphaValue = document.getElementById('alpha-value');
    const betaValue = document.getElementById('beta-value');
    const gammaValue = document.getElementById('gamma-value');
    const deviceModel = document.getElementById('device-model');
    
    if (!orientationStatus || !deviceModel) return;
    
    if (window.DeviceOrientationEvent) {
        orientationStatus.textContent = "Available";
        
        window.addEventListener('deviceorientation', (event) => {
            // Update values
            alphaValue.textContent = event.alpha ? `${Math.round(event.alpha)}°` : "null";
            betaValue.textContent = event.beta ? `${Math.round(event.beta)}°` : "null";
            gammaValue.textContent = event.gamma ? `${Math.round(event.gamma)}°` : "null";
            
            // Update device model orientation
            if (deviceModel && event.beta !== null && event.gamma !== null) {
                deviceModel.style.transform = `rotateX(${-event.beta}deg) rotateY(${event.gamma}deg)`;
            }
        });
    } else {
        orientationStatus.textContent = "Not available";
        document.getElementById('beta-value').textContent = "null";
        document.getElementById('gamma-value').textContent = "null";
    }
}

// Speech Recognition Functions
function updateSpeechFeedback(text, isListening = false) {
    const feedback = document.getElementById('speech-feedback');
    const speechText = document.getElementById('speech-text');
    const startButton = document.getElementById('start');
    
    if (text) {
        speechText.textContent = text;
        feedback.classList.add('show');
        if (isListening) {
            startButton.classList.add('listening');
        } else {
            startButton.classList.remove('listening');
        }
    } else {
        feedback.classList.remove('show');
        startButton.classList.remove('listening');
    }
}

// Update the initSpeechRecognition function
function initSpeechRecognition() {
    const startBtn = document.getElementById('start');
    if (!startBtn) return;

    const recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';

    startBtn.addEventListener('click', () => {
        recognition.start();
        updateSpeechFeedback('Listening...', true);
    });

    recognition.onresult = async (event) => {
        const transcript = event.results[0][0].transcript.trim();
        updateSpeechFeedback(`You said: ${transcript}`);
        console.log('You said:', transcript);
        
        // Show processing state
        updateSpeechFeedback('Processing command...');
        
        const geminiReply = await sendToGemini(transcript);
        handleGeminiResponse(geminiReply);
    };

    recognition.onend = () => {
        // Hide feedback after a delay
        setTimeout(() => {
            updateSpeechFeedback(null);
        }, 2000);
    };

    recognition.onerror = (event) => {
        updateSpeechFeedback(`Error: ${event.error}`);
        setTimeout(() => {
            updateSpeechFeedback(null);
        }, 2000);
    };
}

async function sendToGemini(userText) {
    const apiKey = "AIzaSyD30HnP_8o0wLkgjz9MqJjXx-T8GICv_6s";
    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${apiKey}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            contents: [{
                parts: [{
                    text: `User said: "${userText}". What browser action should I take: "open tabs", "close tab", or "clear history"? Reply with only the action name.`
                }]
            }]
        })
    });

    const data = await response.json();
    const textResponse = data.candidates?.[0]?.content?.parts?.[0]?.text;
    return textResponse?.toLowerCase().trim();
}

function handleGeminiResponse(action) {
    if (!action) {
        alert("No response from Gemini.");
        return;
    }

    if (action.includes("open tabs")) {
        chrome.tabs.query({}, (tabs) => {
            alert(`You have ${tabs.length} tabs open.`);
        });
    } else if (action.includes("close tab")) {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs.length > 0) {
                chrome.tabs.remove(tabs[0].id);
            }
        });
    } else if (action.includes("clear history")) {
        chrome.browsingData.removeHistory({ since: 0 }, () => {
            alert("History cleared.");
        });
    } else {
        alert("Sorry, I didn't understand the command.");
    }
}