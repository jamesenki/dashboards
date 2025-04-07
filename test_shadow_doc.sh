#!/bin/bash

# Create a temporary profile file for cucumber configuration ensuring correct order of loading
cat > cucumber.js <<EOF
module.exports = {
  default: {
    paths: ['./features/shadow_document.feature'],
    require: [
      './features/support/world.js',
      './features/support/hooks.js',
      './features/step_definitions/shadow_document_steps.js'
    ],
    format: ['progress', 'html:test_reports/shadow_doc_test_$(date +"%Y%m%d_%H%M%S").html']
  }
};
EOF

# Run only the shadow document tests with our custom profile
npx cucumber-js --profile default

# Clean up temporary config
rm cucumber.js
