document.addEventListener("DOMContentLoaded", () => {
    initializeUI();
    attachButtonListeners();
    checkIfDownloading();
});

// Utility function to fetch with timeout
function fetchWithTimeout(url, options, timeout = 100) { // 500 ms timeout
    return Promise.race([
        fetch(url, options),
        new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Request timed out')), timeout)
        )
    ]);
}

async function checkIfVideoIsValid(tab) {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.?be\/)[\w-]{11}$/;

    // Preemptive check for valid YouTube URL format
    if (!youtubeRegex.test(tab.url)) {
        showInvalidPage(); // Show invalid page immediately if URL is not valid
        return false; // Not a valid video
    }

    try {
        const response = await fetchWithTimeout(`http://127.0.0.1:5000/valid_video`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ url: tab.url }),
        });

        if (response.ok) {
            return true; // Valid video
        } else {
            showInvalidPage(); // Show invalid page for non-200 responses
            return false; // Not a valid video
        }
    } catch (error) {
        // If there is a fetch error or timeout, show the offline page
        showOfflinePage();
        return false; // Not valid due to offline
    }
}


function showOfflinePage() {
    document.querySelector('.valid-page').style.display = 'none';
    document.getElementById('invalid-page').style.display = 'none'; // Ensure invalid page is hidden
    document.getElementById('offline-page').style.display = 'block'; // Show offline page
}

function showInvalidPage() {
    document.querySelector('.valid-page').style.display = 'none'; // Hide valid page
    document.getElementById('invalid-page').style.display = 'block'; // Show invalid page
    document.getElementById('offline-page').style.display = 'none'; // Ensure offline page is hidden
}

// Listen for messages to reload the popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'showModal') {
        // Display the error message
        document.getElementById("message").style.display = 'block';
        document.getElementById("message").textContent = request.message;
    } else if (request.action === 'reloadPopup') {
        // Reinitialize the UI when the popup is opened
        initializeUI();
        checkIfDownloading();
    }
});

function initializeUI() {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const tab = tabs[0];
        const pageTitle = tab.title;
        const videoTitle = extractVideoTitle(pageTitle);

        const titleElement = createTitleElement(videoTitle);
        
        // Get the valid-page section and insert the title element before the h3
        const validPage = document.querySelector('.valid-page');
        const h3Element = validPage.querySelector('h3');
        
        // Insert the title element before the h3 in valid-page
        validPage.insertBefore(titleElement, h3Element);
    });
}

function extractVideoTitle(pageTitle) {
    const suffix = ' - YouTube';
    return pageTitle.endsWith(suffix) ? pageTitle.slice(0, -suffix.length) : pageTitle;
}

function createTitleElement(videoTitle) {
    const titleElement = document.createElement('h2');
    titleElement.textContent = videoTitle;
    titleElement.classList.add('video-title');
    return titleElement;
}

function attachButtonListeners() {
    document.getElementById("audio").addEventListener("click", () => {
        initiateDownload("audio");
    });

    document.getElementById("video").addEventListener("click", () => {
        initiateDownload("video");
    });
}

async function checkIfDownloading() {
    chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
        const tab = tabs[0];

        const isValidVideo = await checkIfVideoIsValid(tab);
        if (!isValidVideo) {
            return; // If not valid, exit early
        }

        // If it's a valid video, proceed to check if it's downloading
        const response = await fetch(`http://127.0.0.1:5000/is_downloading?url=${encodeURIComponent(tab.url)}`);
        const data = await response.json();

        if (data.is_downloading) {
            // Hide buttons and show a message
            document.getElementById("audio").style.display = 'none';
            document.getElementById("video").style.display = 'none';
            document.getElementById("message").style.display = 'block';
            document.getElementById("message").textContent = "Já está baixando...";
        }
    });
}

function initiateDownload(format) {
    chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
        const activeTab = tabs[0];
        chrome.runtime.sendMessage({ 
            action: "initiateDownload", 
            format: format,
            tabId: activeTab.id
        });
        
        // Hide buttons and show a message
        document.getElementById("audio").style.display = 'none';
        document.getElementById("video").style.display = 'none';
        document.getElementById("message").style.display = 'block';
        document.getElementById("message").textContent = `Baixando ${format}`;
    });
}
