// Jest setup file
document.body.innerHTML = `
  <div id="content">
    <div class="dashboard-container">
      <div class="gauge-panel" id="temperature-gauge-panel">
        <div class="gauge-title">Freezer Temperature</div>
        <div class="gauge-container">
          <div class="gauge" id="temperature-gauge">
            <div class="gauge-fill"></div>
            <div class="gauge-needle"></div>
          </div>
        </div>
        <div class="gauge-value">32°F</div>
      </div>
    </div>
  </div>
`;

// Create fetch mock
global.fetch = jest.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve({}),
  })
);
