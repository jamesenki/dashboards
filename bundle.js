/**
 * Simple JavaScript bundler and minifier script for IoTSphere
 *
 * This script combines and minifies JavaScript files for production use.
 * Run with Node.js: node bundle.js
 */

const fs = require('fs');
const path = require('path');
const uglifyJS = require('uglify-js');

// Configuration
const config = {
  // Input directory containing individual JS files
  inputDir: './frontend/static/js',

  // Output directory for bundled files
  outputDir: './frontend/static/js/dist',

  // Bundle configurations
  bundles: [
    {
      name: 'core-bundle.min.js',
      files: [
        'performance-optimizer.js',
        'optimized-tab-manager.js',
        'device-data-service.js',
        'unified-chart-manager.js',
        'component-integrator.js'
      ]
    },
    {
      name: 'dashboard-bundle.min.js',
      files: [
        'dashboard-component-manager.js',
        'bdd-test-adapter.js'
      ]
    },
    {
      name: 'compat-bundle.min.js',
      files: [
        'websocket-echo-fix.js',
        'device-metadata-handler.js',
        'shadow-document-handler.js'
      ]
    },
    {
      name: 'debug-bundle.min.js',
      files: [
        'debug.js'
      ]
    }
  ],

  // Whether to minify the output
  minify: true,

  // Whether to create source maps
  sourceMaps: true
};

// Create output directory if it doesn't exist
if (!fs.existsSync(config.outputDir)) {
  console.log(`Creating output directory: ${config.outputDir}`);
  fs.mkdirSync(config.outputDir, { recursive: true });
}

// Process each bundle
config.bundles.forEach(bundle => {
  console.log(`Processing bundle: ${bundle.name}`);

  let bundleCode = '';
  let sourceFiles = [];

  // Concatenate all files for this bundle
  bundle.files.forEach(file => {
    const filePath = path.join(config.inputDir, file);

    if (fs.existsSync(filePath)) {
      console.log(`  Adding file: ${file}`);
      const code = fs.readFileSync(filePath, 'utf8');
      bundleCode += `/* ${file} */\n${code}\n\n`;
      sourceFiles.push({ filename: file, content: code });
    } else {
      console.warn(`  Warning: File not found: ${filePath}`);
    }
  });

  // Minify if configured
  if (config.minify) {
    console.log(`  Minifying bundle: ${bundle.name}`);

    const uglifyOptions = {
      compress: {
        dead_code: true,
        drop_debugger: true,
        global_defs: {
          DEBUG: false
        }
      },
      mangle: true
    };

    if (config.sourceMaps) {
      uglifyOptions.sourceMap = {
        filename: bundle.name,
        url: `${bundle.name}.map`
      };
    }

    const result = uglifyJS.minify(sourceFiles, uglifyOptions);

    if (result.error) {
      console.error(`  Error minifying ${bundle.name}:`, result.error);
    } else {
      bundleCode = result.code;

      // Write source map if enabled
      if (config.sourceMaps && result.map) {
        const mapPath = path.join(config.outputDir, `${bundle.name}.map`);
        fs.writeFileSync(mapPath, result.map);
        console.log(`  Source map written to: ${mapPath}`);
      }
    }
  }

  // Write bundle to output file
  const outputPath = path.join(config.outputDir, bundle.name);
  fs.writeFileSync(outputPath, bundleCode);
  console.log(`  Bundle written to: ${outputPath}`);
});

console.log('Bundling complete!');
console.log('\nTo use these bundles in your HTML, replace the individual script tags with:');
config.bundles.forEach(bundle => {
  console.log(`<script src="/static/js/dist/${bundle.name}"></script>`);
});
