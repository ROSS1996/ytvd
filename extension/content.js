// Modal and Overlay classes
class Modal {
    constructor() {
      this.element = null;
      this.message = null;
      this.closeButton = null;
    }
  
    create() {
      this.element = document.createElement('div');
      this.element.className = 'ytd-modal';
      this.element.innerHTML = `
        <p id="ytd-message"></p>
        <button id="ytd-close-button">OK</button>
      `;
      document.body.appendChild(this.element);
  
      this.message = this.element.querySelector('#ytd-message');
      this.closeButton = this.element.querySelector('#ytd-close-button');
      this.closeButton.addEventListener('click', () => this.hide());
    }
  
    show(message) {
      this.message.textContent = message;
      this.element.classList.add('visible');
    }
  
    hide() {
      this.element.classList.remove('visible');
      overlay.hide();
    }
  }
  
  class Overlay {
    constructor() {
      this.element = null;
    }
  
    create() {
      this.element = document.createElement('div');
      this.element.className = 'ytd-overlay';
      document.body.appendChild(this.element);
    }
  
    show() {
      this.element.classList.add('visible');
    }
  
    hide() {
      this.element.classList.remove('visible');
    }
  }
  
  // Create instances
  const modal = new Modal();
  const overlay = new Overlay();
  
  // Initialize modal and overlay
  function initialize() {
    modal.create();
    overlay.create();
  }
  
  // Show modal with message
  function showModal(message) {
    modal.show(message);
    overlay.show();
  }
  
  // Listen for messages from the background script
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'showModal') {
      showModal(request.message);
    }
  });
  
  // Initialize when the content script loads
  initialize();
  
  // Styles
  const styles = `
    .ytd-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.8);
      z-index: 9998;
      opacity: 0;
      visibility: hidden;
      transition: opacity 0.3s ease, visibility 0.3s ease;
    }
  
    .ytd-overlay.visible {
      opacity: 1;
      visibility: visible;
    }
  
    .ytd-modal {
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%) scale(0.9);
      background: white;
      border-radius: 8px;
      z-index: 9999;
      opacity: 0;
      visibility: hidden;
      transition: all 0.3s ease;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
      width: 450px;
      max-width: 90%;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      padding: 30px;
      color: #333;
    }
  
    .ytd-modal.visible {
      opacity: 1;
      visibility: visible;
      transform: translate(-50%, -50%) scale(1);
    }
  
    .ytd-modal p {
      margin: 0 0 20px;
      line-height: 1.6;
      font-size: 16px;
    }
  
    .ytd-modal button {
      display: block;
      width: 100%;
      padding: 12px;
      background-color: #007BFF;
      color: white;
      border: none;
      border-radius: 5px;
      cursor: pointer;
      font-size: 16px;
      transition: background-color 0.3s ease;
    }
  
    .ytd-modal button:hover {
      background-color: #0056b3;
    }

    #ytd-message {
      font-weight: bold;
      font-size: 1.6rem;
    }
  `;
  
  // Apply styles
  const styleElement = document.createElement('style');
  styleElement.textContent = styles;
  document.head.appendChild(styleElement);