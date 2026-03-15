// === Dyslexia Accessibility Toggle Module ===
(function () {
  const STORAGE_KEY = 'dyslexia-settings';

  const defaults = {
    font: 'default',      // 'default' | 'opendyslexic' | 'lexend' | 'arial'
    zebra: false,
    spacing: false,
    noDecorations: false,
    largeText: false,
  };

  function loadSettings() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) return { ...defaults, ...JSON.parse(saved) };
    } catch (e) { /* ignore */ }
    return { ...defaults };
  }

  function saveSettings(settings) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch (e) { /* ignore */ }
  }

  function applySettings(settings) {
    const body = document.body;

    // Font classes
    body.classList.remove('dyslexia-font-opendyslexic', 'dyslexia-font-lexend', 'dyslexia-font-arial');
    if (settings.font !== 'default') {
      body.classList.add(`dyslexia-font-${settings.font}`);
    }

    // Toggle classes
    body.classList.toggle('dyslexia-zebra', settings.zebra);
    body.classList.toggle('dyslexia-spacing', settings.spacing);
    body.classList.toggle('dyslexia-no-decorations', settings.noDecorations);
    body.classList.toggle('dyslexia-large-text', settings.largeText);
  }

  function createPanel(settings) {
    // Floating action button
    const fab = document.createElement('button');
    fab.className = 'dyslexia-fab';
    fab.title = 'Accessibility Settings';
    fab.setAttribute('aria-label', 'Open accessibility settings');
    fab.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="4.5" r="2.5"/><path d="M12 7v5"/><path d="M8 21l2-7h4l2 7"/><path d="M6 12h12"/></svg>`;

    // Panel
    const panel = document.createElement('div');
    panel.className = 'dyslexia-panel';
    panel.innerHTML = `
      <div class="dyslexia-panel-title">Accessibility</div>

      <div class="dyslexia-option">
        <span class="dyslexia-option-label">Font</span>
        <select class="dyslexia-select" id="dyslexiaFont">
          <option value="default">Default</option>
          <option value="opendyslexic">OpenDyslexic</option>
          <option value="lexend">Lexend</option>
          <option value="arial">Arial</option>
        </select>
      </div>

      <div class="dyslexia-option">
        <span class="dyslexia-option-label">Zebra striping</span>
        <label class="dyslexia-toggle">
          <input type="checkbox" id="dyslexiaZebra">
          <span class="dyslexia-toggle-slider"></span>
        </label>
      </div>

      <div class="dyslexia-option">
        <span class="dyslexia-option-label">Enhanced spacing</span>
        <label class="dyslexia-toggle">
          <input type="checkbox" id="dyslexiaSpacing">
          <span class="dyslexia-toggle-slider"></span>
        </label>
      </div>

      <div class="dyslexia-option">
        <span class="dyslexia-option-label">No decorations</span>
        <label class="dyslexia-toggle">
          <input type="checkbox" id="dyslexiaNoDecorations">
          <span class="dyslexia-toggle-slider"></span>
        </label>
      </div>

      <div class="dyslexia-option">
        <span class="dyslexia-option-label">Larger text</span>
        <label class="dyslexia-toggle">
          <input type="checkbox" id="dyslexiaLargeText">
          <span class="dyslexia-toggle-slider"></span>
        </label>
      </div>
    `;

    document.body.appendChild(fab);
    document.body.appendChild(panel);

    // Set initial values
    const fontSelect = panel.querySelector('#dyslexiaFont');
    const zebraCheck = panel.querySelector('#dyslexiaZebra');
    const spacingCheck = panel.querySelector('#dyslexiaSpacing');
    const noDecorationsCheck = panel.querySelector('#dyslexiaNoDecorations');
    const largeTextCheck = panel.querySelector('#dyslexiaLargeText');

    fontSelect.value = settings.font;
    zebraCheck.checked = settings.zebra;
    spacingCheck.checked = settings.spacing;
    noDecorationsCheck.checked = settings.noDecorations;
    largeTextCheck.checked = settings.largeText;

    // Toggle panel visibility
    fab.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = panel.classList.toggle('open');
      fab.classList.toggle('active', isOpen);
    });

    // Close panel when clicking outside
    document.addEventListener('click', (e) => {
      if (!panel.contains(e.target) && e.target !== fab) {
        panel.classList.remove('open');
        fab.classList.remove('active');
      }
    });

    // Event listeners for changes
    function onChange() {
      settings.font = fontSelect.value;
      settings.zebra = zebraCheck.checked;
      settings.spacing = spacingCheck.checked;
      settings.noDecorations = noDecorationsCheck.checked;
      settings.largeText = largeTextCheck.checked;
      applySettings(settings);
      saveSettings(settings);
    }

    fontSelect.addEventListener('change', onChange);
    zebraCheck.addEventListener('change', onChange);
    spacingCheck.addEventListener('change', onChange);
    noDecorationsCheck.addEventListener('change', onChange);
    largeTextCheck.addEventListener('change', onChange);
  }

  // Initialize on DOM ready
  function init() {
    const settings = loadSettings();
    applySettings(settings);
    createPanel(settings);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
