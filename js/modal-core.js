/**
 * modal-core.js
 * Centralized modal state and handlers for gallery viewing.
 * Replaces scattered modal open/close/render logic.
 */

const Modal = {
  state: {
    visible: false,
    currentGallery: null,
    currentIndex: 0
  },

  /**
   * Open modal for a gallery.
   * @param {string} galleryName - Key from GALLERIES config (e.g., 'atlas')
   */
  open: (galleryName) => {
    Modal.state.visible = true;
    Modal.state.currentGallery = galleryName;
    Modal.state.currentIndex = galleryState[galleryName] || 0;
    Modal.render();
    document.addEventListener('keydown', Modal.handleKeyboard);
  },

  /**
   * Close modal.
   */
  close: () => {
    Modal.state.visible = false;
    Modal.state.currentGallery = null;
    document.removeEventListener('keydown', Modal.handleKeyboard);
    const modal = document.getElementById('gallery-modal');
    if (modal) {
      modal.style.display = 'none';
    }
  },

  /**
   * Keyboard handler: Escape to close.
   * Arrow keys delegated to gallery handlers.
   */
  handleKeyboard: (e) => {
    if (!Modal.state.visible) return;

    if (e.key === 'Escape') {
      Modal.close();
    }
  },

  /**
   * Render modal: update image, counter, show modal.
   * Called when opening or when image changes.
   */
  render: () => {
    const modal = document.getElementById('gallery-modal');
    if (!modal) return;

    const galleryName = Modal.state.currentGallery;
    if (!galleryName || !GALLERIES[galleryName]) return;

    const config = GALLERIES[galleryName];
    const imgPath = config.images[Modal.state.currentIndex];

    // Update modal image
    const modalImg = modal.querySelector('#modal-image');
    if (modalImg) {
      modalImg.src = imgPath;
      modalImg.alt = `${galleryName} image ${Modal.state.currentIndex + 1}`;
    }

    // Update counter (if exists)
    const counter = modal.querySelector('#image-counter');
    if (counter) {
      counter.textContent = `${Modal.state.currentIndex + 1} / ${config.images.length}`;
    }

    // Show modal
    modal.style.display = 'block';
  }
};
