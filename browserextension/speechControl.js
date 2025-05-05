// Enhanced Speech Recognition for Browser Extension
class VoiceControl {
  constructor() {
    this.recognition = null;
    this.isListening = false;
    this.commands = {
      "close tab": this.closeCurrentTab,
      "close all tabs": this.closeAllTabs,
      "open new tab": this.openNewTab,
      "refresh page": this.refreshPage,
      "go back": this.goBack,
      "go forward": this.goForward,
      "mute tab": this.muteTab,
      "unmute tab": this.unmuteTab,
      "pin tab": this.pinTab,
      "unpin tab": this.unpinTab,
      "duplicate tab": this.duplicateTab,
      "switch to tab": this.switchToTab,
      "open history": this.openHistoryPage,
      "open downloads": this.openDownloadsPage,
      "clear history": this.clearHistory,
      "zoom in": this.zoomIn,
      "zoom out": this.zoomOut,
      "reset zoom": this.resetZoom,
      "take screenshot": this.takeScreenshot,
      "bookmark page": this.bookmarkPage
    };
    
    this.init();
  }

  init() {
    if (!('webkitSpeechRecognition' in window)) {
      console.error('Speech recognition not supported');
      return;
    }

    this.recognition = new webkitSpeechRecognition();
    this.recognition.continuous = false;
    this.recognition.interimResults = false;
    this.recognition.lang = 'en-US';

    this.setupEventListeners();
  }

  setupEventListeners() {
    const startBtn = document.getElementById('start');
    if (startBtn) {
      startBtn.addEventListener('click', () => this.toggleListening());
    }

    this.recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript.trim().toLowerCase();
      this.processCommand(transcript);
    };

    this.recognition.onerror = (event) => {
      console.error('Speech recognition error', event.error);
      this.updateFeedback(`Error: ${event.error}`, false);
      this.isListening = false;
    };

    this.recognition.onend = () => {
      if (this.isListening) {
        // If we're still supposed to be listening, restart recognition
        this.recognition.start();
      } else {
        this.updateFeedback(null, false);
      }
    };
  }

  toggleListening() {
    if (this.isListening) {
      this.stopListening();
    } else {
      this.startListening();
    }
  }

  startListening() {
    try {
      this.recognition.start();
      this.isListening = true;
      this.updateFeedback("Listening...", true);
    } catch (error) {
      console.error('Error starting speech recognition:', error);
      this.updateFeedback("Error starting microphone", false);
    }
  }

  stopListening() {
    this.isListening = false;
    this.recognition.stop();
  }

  updateFeedback(text, isListening) {
    const feedback = document.getElementById('speech-feedback');
    const speechText = document.getElementById('speech-text');
    const startButton = document.getElementById('start');
    
    if (text) {
      speechText.textContent = text;
      feedback.classList.add('show');
      startButton?.classList.toggle('listening', isListening);
    } else {
      feedback.classList.remove('show');
      startButton?.classList.remove('listening');
    }
  }

  async processCommand(transcript) {
    console.log('Processing command:', transcript);
    this.updateFeedback(`You said: "${transcript}"`, false);

    // First check for exact command matches
    for (const [command, action] of Object.entries(this.commands)) {
      if (transcript.includes(command)) {
        this.updateFeedback(`Executing: ${command}`, false);
        await action.call(this);
        return;
      }
    }

    // If no exact match, try to find the closest command
    const closestCommand = this.findClosestCommand(transcript);
    if (closestCommand) {
      const confirmExecute = confirm(`Did you mean "${closestCommand}"?`);
      if (confirmExecute) {
        this.updateFeedback(`Executing: ${closestCommand}`, false);
        await this.commands[closestCommand].call(this);
      } else {
        this.updateFeedback("Command not recognized", false);
      }
    } else {
      // If no command matches, use Gemini API for more complex commands
      await this.handleComplexCommand(transcript);
    }
  }

  findClosestCommand(transcript) {
    let bestMatch = null;
    let bestScore = 0;
    const threshold = 0.6; // Minimum similarity score to consider

    for (const command of Object.keys(this.commands)) {
      const score = this.similarity(transcript, command);
      if (score > bestScore && score >= threshold) {
        bestScore = score;
        bestMatch = command;
      }
    }

    return bestMatch;
  }

  similarity(s1, s2) {
    // Simple similarity measure - could be improved with more sophisticated algorithm
    const longer = s1.length > s2.length ? s1 : s2;
    const shorter = s1.length > s2.length ? s2 : s1;
    const longerLength = longer.length;
    
    if (longerLength === 0) return 1.0;
    
    return (longerLength - this.editDistance(longer, shorter)) / parseFloat(longerLength);
  }

  editDistance(s1, s2) {
    // Levenshtein distance
    s1 = s1.toLowerCase();
    s2 = s2.toLowerCase();
    
    const costs = [];
    for (let i = 0; i <= s1.length; i++) {
      let lastValue = i;
      for (let j = 0; j <= s2.length; j++) {
        if (i === 0) {
          costs[j] = j;
        } else {
          if (j > 0) {
            let newValue = costs[j - 1];
            if (s1.charAt(i - 1) !== s2.charAt(j - 1)) {
              newValue = Math.min(Math.min(newValue, lastValue), costs[j]) + 1;
            }
            costs[j - 1] = lastValue;
            lastValue = newValue;
          }
        }
      }
      if (i > 0) costs[s2.length] = lastValue;
    }
    return costs[s2.length];
  }

  async handleComplexCommand(transcript) {
    this.updateFeedback("Processing complex command...", false);
    
    try {
      const response = await this.queryGemini(transcript);
      if (response) {
        this.updateFeedback(response, false);
      } else {
        this.updateFeedback("Sorry, I didn't understand that command.", false);
      }
    } catch (error) {
      console.error('Error processing complex command:', error);
      this.updateFeedback("Error processing command", false);
    }
  }

  async queryGemini(query) {
    const apiKey = "AIzaSyD30HnP_8o0wLkgjz9MqJjXx-T8GICv_6s";
    const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${apiKey}`;
    
    const prompt = `The user is controlling their browser with voice commands. They said: "${query}". 
      Possible actions include managing tabs, navigation, history, downloads, and browser settings.
      Respond with ONLY the most appropriate action to take or a very brief response if no action is clear.`;
    
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{
            parts: [{ text: prompt }]
          }]
        })
      });
      
      const data = await response.json();
      const textResponse = data.candidates?.[0]?.content?.parts?.[0]?.text?.trim();
      
      if (textResponse) {
        // Check if the response matches any known command
        for (const [command, action] of Object.entries(this.commands)) {
          if (textResponse.toLowerCase().includes(command)) {
            await action.call(this);
            return `Executed: ${command}`;
          }
        }
        
        // If not a command, just return the response
        return textResponse;
      }
      
      return "Sorry, I didn't understand that command.";
    } catch (error) {
      console.error('Error querying Gemini:', error);
      return "Error processing your request.";
    }
  }

  // Command implementations
  async closeCurrentTab() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      await chrome.tabs.remove(tab.id);
      this.updateFeedback("Closed current tab", false);
    } else {
      this.updateFeedback("No active tab found", false);
    }
  }

  async closeAllTabs() {
    const tabs = await chrome.tabs.query({ currentWindow: true });
    if (tabs.length > 0) {
      const tabIds = tabs.map(tab => tab.id);
      await chrome.tabs.remove(tabIds);
      this.updateFeedback(`Closed all ${tabs.length} tabs`, false);
    } else {
      this.updateFeedback("No tabs to close", false);
    }
  }

  async openNewTab() {
    await chrome.tabs.create({ url: "chrome://newtab", active: true });
    this.updateFeedback("Opened new tab", false);
  }

  async refreshPage() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      await chrome.tabs.reload(tab.id);
      this.updateFeedback("Page refreshed", false);
    } else {
      this.updateFeedback("No active tab to refresh", false);
    }
  }

  async goBack() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      await chrome.tabs.goBack(tab.id);
      this.updateFeedback("Navigated back", false);
    } else {
      this.updateFeedback("No active tab to navigate", false);
    }
  }

  async goForward() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      await chrome.tabs.goForward(tab.id);
      this.updateFeedback("Navigated forward", false);
    } else {
      this.updateFeedback("No active tab to navigate", false);
    }
  }

  async muteTab() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      await chrome.tabs.update(tab.id, { muted: true });
      this.updateFeedback("Tab muted", false);
    } else {
      this.updateFeedback("No active tab to mute", false);
    }
  }

  async unmuteTab() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      await chrome.tabs.update(tab.id, { muted: false });
      this.updateFeedback("Tab unmuted", false);
    } else {
      this.updateFeedback("No active tab to unmute", false);
    }
  }

  async pinTab() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      await chrome.tabs.update(tab.id, { pinned: true });
      this.updateFeedback("Tab pinned", false);
    } else {
      this.updateFeedback("No active tab to pin", false);
    }
  }

  async unpinTab() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      await chrome.tabs.update(tab.id, { pinned: false });
      this.updateFeedback("Tab unpinned", false);
    } else {
      this.updateFeedback("No active tab to unpin", false);
    }
  }

  async duplicateTab() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      await chrome.tabs.duplicate(tab.id);
      this.updateFeedback("Tab duplicated", false);
    } else {
      this.updateFeedback("No active tab to duplicate", false);
    }
  }

  async switchToTab(tabNumber) {
    const tabs = await chrome.tabs.query({ currentWindow: true });
    if (tabs.length === 0) {
      this.updateFeedback("No tabs available", false);
      return;
    }
    
    // If no number specified, list available tabs
    if (tabNumber === undefined) {
      const tabList = tabs.map((tab, index) => 
        `${index + 1}: ${tab.title || 'Untitled tab'}`).join('\n');
      this.updateFeedback(`Available tabs:\n${tabList}\nSay "switch to tab" followed by the number`, false);
      return;
    }
    
    // Check if tab number is valid
    if (tabNumber < 1 || tabNumber > tabs.length) {
      this.updateFeedback(`Invalid tab number. Please choose between 1 and ${tabs.length}`, false);
      return;
    }
    
    // Switch to the selected tab
    const tab = tabs[tabNumber - 1];
    await chrome.tabs.update(tab.id, { active: true });
    this.updateFeedback(`Switched to tab ${tabNumber}: ${tab.title || 'Untitled tab'}`, false);
  }

  async openHistoryPage() {
    await chrome.tabs.create({ url: "chrome://history", active: true });
    this.updateFeedback("Opened history page", false);
  }

  async openDownloadsPage() {
    await chrome.tabs.create({ url: "chrome://downloads", active: true });
    this.updateFeedback("Opened downloads page", false);
  }

  async clearHistory() {
    const confirmClear = confirm("Are you sure you want to clear your browsing history?");
    if (confirmClear) {
      await chrome.browsingData.removeHistory({});
      this.updateFeedback("Browsing history cleared", false);
    } else {
      this.updateFeedback("History clearing canceled", false);
    }
  }

  async zoomIn() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      await chrome.tabs.setZoom(tab.id, 0.1); // Increase zoom by 10%
      this.updateFeedback("Zoomed in", false);
    } else {
      this.updateFeedback("No active tab to zoom", false);
    }
  }

  async zoomOut() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      await chrome.tabs.setZoom(tab.id, -0.1); // Decrease zoom by 10%
      this.updateFeedback("Zoomed out", false);
    } else {
      this.updateFeedback("No active tab to zoom", false);
    }
  }

  async resetZoom() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      await chrome.tabs.setZoom(tab.id, 0); // Reset to default zoom
      this.updateFeedback("Zoom reset", false);
    } else {
      this.updateFeedback("No active tab to zoom", false);
    }
  }

  async takeScreenshot() {
    this.updateFeedback("Taking screenshot...", false);
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (tab) {
      try {
        // Note: The chrome.tabs.captureVisibleTab API requires additional permissions
        const imageUri = await chrome.tabs.captureVisibleTab();
        // Create a new tab with the screenshot
        await chrome.tabs.create({ url: imageUri, active: true });
        this.updateFeedback("Screenshot taken", false);
      } catch (error) {
        console.error('Error taking screenshot:', error);
        this.updateFeedback("Failed to take screenshot", false);
      }
    } else {
      this.updateFeedback("No active tab to screenshot", false);
    }
  }

  async bookmarkPage() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (tab) {
      try {
        await chrome.bookmarks.create({
          title: tab.title,
          url: tab.url
        });
        this.updateFeedback("Page bookmarked", false);
      } catch (error) {
        console.error('Error creating bookmark:', error);
        this.updateFeedback("Failed to create bookmark", false);
      }
    } else {
      this.updateFeedback("No active tab to bookmark", false);
    }
  }
}

// Initialize voice control when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new VoiceControl();
});