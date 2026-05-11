/**
 * gallery-core.js
 * Core gallery functions: factory, initialization, event wiring, updates.
 * Replaces 36 individual gallery functions (openAtlasGallery, atlasGalleryNext, etc).
 */

/**
 * Factory: create open/next/prev handlers for a gallery.
 * Returns object with {open, next, prev} functions bound to a specific gallery.
 * @param {string} name - Gallery key (e.g., 'atlas')
 * @param {object} config - GALLERIES[name] entry
 * @returns {object} {open, next, prev} handlers
 */
function createGalleryHandlers(name, config) {
  return {
    open: () => {
      galleryState[name] = 0;
      Modal.open(name);
    },

    next: () => {
      const len = config.images.length;
      galleryState[name] = (galleryState[name] + 1) % len;
      updateGallery(name);
    },

    prev: () => {
      const len = config.images.length;
      galleryState[name] = (galleryState[name] - 1 + len) % len;
      updateGallery(name);
    }
  };
}

/**
 * Update gallery display: sync Modal state with galleryState, re-render modal.
 * Called when user navigates (next/prev or thumbnail click).
 * @param {string} name - Gallery key
 */
function updateGallery(name) {
  if (!galleryState.hasOwnProperty(name)) return;

  Modal.state.currentGallery = name;
  Modal.state.currentIndex = galleryState[name];
  Modal.render();
}

/**
 * Open gallery modal and set initial index.
 * Delegates to Modal.open for centralized modal handling.
 * @param {string} name - Gallery key
 */
function openGallery(name) {
  if (!GALLERIES[name]) return;
  Modal.open(name);
}
