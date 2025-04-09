#!/bin/bash
# Script to fix step definition ambiguities
# Following TDD principles - tests define expected behavior

echo "Fixing step definition ambiguities for real-time monitoring system..."

# Create a backup of the step definition files
cp features/step_definitions/realtime_updates_steps.js features/step_definitions/realtime_updates_steps.js.bak
cp features/step_definitions/shadow_document_steps.js features/step_definitions/shadow_document_steps.js.bak
cp features/step_definitions/common_steps.js features/step_definitions/common_steps.js.bak

# Fix the shadow_document_steps.js file
sed -i '' 's/When('"'"'I navigate to the water heater with ID {string}'"'"'/\/\/ REMOVED to avoid duplicate step definitions - using common_steps.js\n\/\/ When('"'"'I navigate to the water heater with ID {string}'"'"'/' features/step_definitions/shadow_document_steps.js

# Fix the WebSocket connection step definitions in realtime_updates_steps.js
# Find duplicate definitions of "the WebSocket connection is interrupted"
grep -n "the WebSocket connection is interrupted" features/step_definitions/realtime_updates_steps.js |
while read -r line; do
  if [[ $line != *":205:"* ]]; then  # Keep the first occurrence (around line 205)
    line_num=$(echo "$line" | cut -d: -f1)
    sed -i '' "${line_num}s/When('the WebSocket connection is interrupted'/\/\/ REMOVED to avoid duplication\n\/\/ When('the WebSocket connection is interrupted'/" features/step_definitions/realtime_updates_steps.js
  fi
done

# Find duplicate definitions of "the connection is restored"
grep -n "the connection is restored" features/step_definitions/realtime_updates_steps.js |
while read -r line; do
  if [[ $line != *":287:"* ]]; then  # Keep the first occurrence (around line 287)
    line_num=$(echo "$line" | cut -d: -f1)
    sed -i '' "${line_num}s/When('the connection is restored'/\/\/ REMOVED to avoid duplication\n\/\/ When('the connection is restored'/" features/step_definitions/realtime_updates_steps.js
  fi
done

# Find duplicate definitions of "the status indicator should show"
grep -n "the status indicator should show" features/step_definitions/realtime_updates_steps.js |
while read -r line; do
  if [[ $line != *":156:"* ]]; then  # Keep the first occurrence (around line 156)
    line_num=$(echo "$line" | cut -d: -f1)
    sed -i '' "${line_num}s/Then('the status indicator should show {string}'/\/\/ REMOVED to avoid duplication\n\/\/ Then('the status indicator should show {string}'/" features/step_definitions/realtime_updates_steps.js
  fi
done

echo "Fixing completed. Running tests to verify..."

# Run the tests to see if ambiguities are resolved
python test_runner.py --types bdd

echo "Step definition fix completed."
