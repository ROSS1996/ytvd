chrome.action.onClicked.addListener((tab) => {
    if (tab.url && tab.url.startsWith("https://www.youtube.com/watch")) {
        chrome.action.setPopup({ popup: "popup.html" });
    } else {
        chrome.action.setPopup({ popup: "" });
        
        chrome.tabs.sendMessage(tab.id, {
            action: 'showModal',
            message: "Esta não é uma página de vídeo do YouTube. Por favor, abra um vídeo do YouTube."
        });
    }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "initiateDownload") {
        handleDownload(request.format, request.tabId);
    }
});

async function handleDownload(format, tabId) {
    try {
        const tab = await chrome.tabs.get(tabId);
        const videoUrl = tab.url;

        const response = await fetch("http://127.0.0.1:5000/download", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ url: videoUrl, format: format }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || "Falha ao baixar o vídeo");
        }

        const data = await response.json();
        showModalInTab(tabId, data.message);
    } catch (error) {
        console.error("Download error:", error);
        handleDownloadError(error, tabId);
    }
}

function handleDownloadError(error, tabId) {
    let message;
    if (error.message.includes("Failed to fetch")) {
        message = "Você esqueceu de iniciar o programa de downloads. Inicie antes de tentar baixar.";
    } else {
        message = "Erro ao baixar: " + error.message;
    }
    showModalInTab(tabId, message);
}

function showModalInTab(tabId, message) {
    chrome.tabs.sendMessage(tabId, {
        action: 'showModal',
        message: message
    }, (response) => {
        if (chrome.runtime.lastError) {
            console.error("Error sending message to tab:", chrome.runtime.lastError);
        }
    });
}
