# Website Gallery Refactor: Factory + Config-Driven Design
**Date:** 2026-05-11  
**Project:** CMPPort Website  
**Scope:** Gallery navigation, modal, thumbnail rendering  
**Goal:** DRY up 36 near-identical functions → 3 core factory functions; consolidate 100+ lines of duplicated event listeners

---

## Problem Statement

Current index.html has massive code duplication:
- **Gallery functions:** 12 galleries × 3 functions (open, next, prev) = 36 nearly-identical functions
- **Event listeners:** 72+ `addEventListener` calls with duplicate logic
- **Thumbnail rendering:** 12 separate functions with identical pattern
- **Modal logic:** scattered, partially duplicated

Result: ~2000+ lines of gallery code, hard to maintain, scales poorly.

---

## Architecture Overview

### New Core Modules

1. **`js/gallery-core.js`**
   - `createGalleryHandlers(name, config)` → returns `{open, next, prev}` handler object
   - `initAllGalleries(GALLERIES, galleryState)` → loops GALLERIES config, wires all galleries dynamically
   - `wireGalleryEvents(name, handlers)` → binds DOM listeners (buttons, keyboard), renders thumbnails
   - `updateGallery(name)` → shared modal/counter update logic
   - `openGallery(name)` → refactored modal open

2. **`js/modal-core.js`**
   - `Modal` object (centralized modal state + methods)
   - `Modal.open(galleryName)` 
   - `Modal.close()`
   - `Modal.render()` → updates modal DOM
   - `Modal.handleKeyboard()` → Escape + delegation to gallery handlers

3. **`js/thumbnails-core.js`**
   - `renderGalleryThumbnails(name)` → single function replaces 12 individual render functions

### Key Design Decisions

- **Config-driven:** GALLERIES config is source of truth; no hardcoded gallery names in functions
- **Factory pattern:** `createGalleryHandlers()` generates open/next/prev closures per gallery
- **Dynamic initialization:** Single loop `initAllGalleries()` wires all galleries instead of 36 hardcoded functions
- **Data attributes:** HTML buttons use `data-gallery` and `data-action` for selector queries
- **Modal centralization:** One `Modal` object handles all modal state; galleries delegate to it

---

## Factory Function: createGalleryHandlers()

```javascript
function createGalleryHandlers(name, config) {
  // config = GALLERIES[name] entry
  // name = gallery key (e.g., 'atlas', 'quarter')
  
  return {
    open: () => {
      galleryState[name] = 0;
      Modal.open(name);  // Use centralized modal
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
```

**Replaces:** 36 individual functions like `openAtlasGallery()`, `atlasGalleryNext()`, etc.

---

## Event Listener Consolidation: wireGalleryEvents()

```javascript
function wireGalleryEvents(name, handlers) {
  // 1. Wire next/prev buttons using data attributes
  document.querySelectorAll(`[data-gallery="${name}"][data-action="next"]`)
    .forEach(btn => btn.addEventListener('click', handlers.next));
  
  document.querySelectorAll(`[data-gallery="${name}"][data-action="prev"]`)
    .forEach(btn => btn.addEventListener('click', handlers.prev));
  
  // 2. Keyboard navigation (delegated to modal handler)
  // Escape handled by Modal.handleKeyboard()
  // Arrow keys delegated based on Modal.state.currentGallery
  
  // 3. Render thumbnails
  renderGalleryThumbnails(name);
}
```

**HTML buttons (minimal change):**
```html
<button data-gallery="atlas" data-action="next">Next</button>
<button data-gallery="atlas" data-action="prev">Prev</button>
```

**Replaces:** 72+ individual addEventListener calls scattered through inline `<script>`.

---

## Modal Core: Modal Object

```javascript
const Modal = {
  state: {
    visible: false,
    currentGallery: null,
    currentIndex: 0
  },
  
  open: (galleryName) => {
    Modal.state.visible = true;
    Modal.state.currentGallery = galleryName;
    Modal.state.currentIndex = galleryState[galleryName];
    Modal.render();
    document.addEventListener('keydown', Modal.handleKeyboard);
  },
  
  close: () => {
    Modal.state.visible = false;
    Modal.state.currentGallery = null;
    document.removeEventListener('keydown', Modal.handleKeyboard);
    // Hide modal DOM
    document.getElementById('gallery-modal').style.display = 'none';
  },
  
  handleKeyboard: (e) => {
    if (!Modal.state.visible) return;
    if (e.key === 'Escape') {
      Modal.close();
    }
    // Arrow keys handled by gallery handlers (via updateGallery)
  },
  
  render: () => {
    // Update modal image, counter, etc. from galleryState[Modal.state.currentGallery]
    // Show modal DOM
    document.getElementById('gallery-modal').style.display = 'block';
  }
};
```

**Replaces:** scattered modal open/close/render logic duplicated across individual gallery functions.

---

## Thumbnail Rendering: renderGalleryThumbnails()

```javascript
function renderGalleryThumbnails(name) {
  const config = GALLERIES[name];
  const container = document.getElementById(`${name}-thumbnails`);
  
  // Clear old thumbnails
  container.innerHTML = '';
  
  // Render thumbnails using config.thumbClass
  config.images.forEach((img, idx) => {
    const thumb = document.createElement('img');
    thumb.src = img;
    thumb.className = config.thumbClass;  // e.g., 'gallery-thumb-60'
    thumb.addEventListener('click', () => {
      galleryState[name] = idx;
      updateGallery(name);
    });
    container.appendChild(thumb);
  });
}
```

**Replaces:** 12 individual functions like `renderAtlasThumbnails()`, `renderQuarterThumbnails()`, etc.

---

## Integration: initAllGalleries()

```javascript
function initAllGalleries(GALLERIES, galleryState) {
  Object.keys(GALLERIES).forEach(name => {
    const config = GALLERIES[name];
    const handlers = createGalleryHandlers(name, config);
    wireGalleryEvents(name, handlers);
  });
}
```

**Called once at end of `<script>` block in index.html:**
```html
<script>
  // ... GALLERIES config definition ...
  // ... galleryState init ...
  
  // Initialize all galleries with core functions
  initAllGalleries(GALLERIES, galleryState);
</script>
```

---

## File Structure Changes

### Files to Create
- `js/gallery-core.js` — core gallery functions
- `js/modal-core.js` — Modal object
- `js/thumbnails-core.js` — thumbnail rendering

### Changes to index.html
- **Add** (before `</body>`):
  ```html
  <script src="js/modal-core.js"></script>
  <script src="js/thumbnails-core.js"></script>
  <script src="js/gallery-core.js"></script>
  ```

- **Delete:**
  - All 36 hardcoded gallery functions (`openAtlasGallery()`, `atlasGalleryNext()`, etc.)
  - All 72+ duplicated `addEventListener` blocks
  - All 12 individual thumbnail render functions
  - Scattered modal open/close/render logic

- **Keep:**
  - GALLERIES config
  - `galleryState` object
  - Single call to `initAllGalleries(GALLERIES, galleryState)`

---

## Verification Plan

### Functional Tests (per gallery)
- [ ] Click "View Gallery" button → modal opens with first image
- [ ] Click "Next" button → image cycles forward, counter increments
- [ ] Click "Previous" button → image cycles backward, counter decrements
- [ ] Click thumbnail → modal jumps to that image
- [ ] Press ArrowRight → next image
- [ ] Press ArrowLeft → previous image
- [ ] Press Escape → modal closes
- [ ] Click modal close (X) button → modal closes

### Regression Tests
- [ ] Test all 12 galleries (atlas, quarter, obk, trp, kbh, pryd, obkf, thaiOil, tempFactory, pierreRepair, kaoyai, boonNak)
- [ ] No console errors or warnings
- [ ] Gallery state persists correctly across open/close
- [ ] Thumbnail strip renders without missing images
- [ ] Modal UI (image, counter, buttons) displays correctly

### Code Quality
- [ ] Zero console errors
- [ ] Browser DevTools: no broken references
- [ ] Code size reduction: ~2000+ lines → ~300 lines

---

## Acceptance Criteria

- ✅ All 12 galleries open/next/prev work identically to before (user flow unchanged)
- ✅ Keyboard navigation (arrows, Escape) works
- ✅ Thumbnail rendering correct for all galleries
- ✅ Modal opens/closes without errors
- ✅ No console errors or warnings
- ✅ Gallery state persists across open/close cycles
- ✅ HTML buttons have `data-gallery` and `data-action` attributes
- ✅ New files: `gallery-core.js`, `modal-core.js`, `thumbnails-core.js` created and imported
- ✅ Old code (36 functions, 72+ listeners, 12 render functions) completely removed
- ✅ GALLERIES config unchanged (backward compatible)

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Broken gallery functionality | Test all 12 galleries before/after; keep old code as reference during refactor |
| Missing event bindings | Use `data-gallery` attributes consistently; test button clicks |
| Modal state bugs | Centralize modal state in `Modal` object; add debug logging during testing |
| Browser compat (querySelectorAll, data attributes) | Verify in Chrome, Firefox, Safari |

---

## Next Steps (Implementation Plan)

1. Create `js/gallery-core.js` with `createGalleryHandlers()`, `initAllGalleries()`, `wireGalleryEvents()`, `updateGallery()`
2. Create `js/modal-core.js` with `Modal` object
3. Create `js/thumbnails-core.js` with `renderGalleryThumbnails()`
4. Update index.html: add script imports, delete old functions, call `initAllGalleries()`
5. Test all 12 galleries (open, next/prev, close)
6. Test keyboard navigation
7. Verify no console errors
8. Commit with message: "refactor: extract gallery core functions, eliminate 36 duplicate handlers"
