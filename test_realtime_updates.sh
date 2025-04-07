#!/bin/bash

# Script to run real-time update tests following TDD principles
# This runs first before implementing the actual functionality

echo "Running real-time update tests for IoTSphere..."
node run_realtime_tests.js

# Exit with the exit code from the tests
exit $?
