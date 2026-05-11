/**
 * thumbnails-core.js
 * Unified thumbnail rendering for all galleries.
 * Replaces 12 individual render functions (renderAtlasThumbnails, etc).
 */

/**
 * Render thumbnail strip for a gallery.
 * Creates img elements, binds click handlers to jump to that image.
 * @param {string} name - Gallery key (e.g., 'atlas')
 */
function renderGalleryThumbnails(name) {
  const config = GALLERIES[name];
  if (!config) return;

  const containerId = `${name}-thumbnails`;
  const container = document.getElementById(containerId);
  if (!container) return;

  // Clear old thumbnails
  container.innerHTML = '';

  // Render each thumbnail
  config.images.forEach((imgPath, idx) => {
    const thumb = document.createElement('img');
    thumb.src = imgPath;
    thumb.className = config.thumbClass || 'gallery-thumb';
    thumb.alt = `${name} thumbnail ${idx + 1}`;
    thumb.style.cursor = 'pointer';

    // Click thumbnail to jump to that image
    thumb.addEventListener('click', () => {
      galleryState[name] = idx;
      Modal.state.currentIndex = idx;
      Modal.render();
    });

    container.appendChild(thumb);
  });
}
