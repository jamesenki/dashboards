#!/bin/bash
# archive_deprecated_files.sh

# Base directory
BASE_DIR="/Users/lisasimon/repos/IoTSphereAngular/IoTSphere-Refactor"
ARCHIVE_DIR="$BASE_DIR/archived"

# Create the necessary archive directories
mkdir -p $ARCHIVE_DIR/{frontend/static/css,frontend/static/js/tests,frontend/templates/water-heater,src/api/{routes,implementations,routers},src/{scripts,utils},src/tests/{e2e,integration/monitoring},tests/e2e}

echo "Created archive directories."

# Define arrays of files to move
CSS_FILES=(
    "frontend/static/css/aquatherm-cards.css"
    "frontend/static/css/aquatherm-fixes.css"
    "frontend/static/css/aquatherm-water-heater.css"
)

JS_FILES=(
    "frontend/static/js/aquatherm-card-fix.js"
    "frontend/static/js/aquatherm-fix.js"
    "frontend/static/js/aquatherm-navigation-fix.js"
    "frontend/static/js/aquatherm-test-helper.js"
    "frontend/static/js/aquatherm-ui-debug.js"
    "frontend/static/js/aquatherm-water-heater.js"
    "frontend/static/js/clear-mock-data.js"
)

JS_TEST_FILES=(
    "frontend/static/js/tests/aquatherm-card-test.js"
    "frontend/static/js/tests/aquatherm-comprehensive-tests.js"
)

TEMPLATE_FILES=(
    "frontend/templates/water-heater/standalone.html"
    "frontend/templates/water-heater/debug.html"
)

API_FILES=(
    "src/api/routes/aquatherm_water_heaters.py"
    "src/api/implementations/mock_water_heater_api.py"
    "src/api/routers/mock_water_heater_router.py"
)

SCRIPT_FILES=(
    "src/scripts/check_aquatherm_heaters.py"
    "src/scripts/load_aquatherm_data.py"
    "src/scripts/load_aquatherm_data_fixed.py"
    "src/scripts/test_aquatherm_api.py"
    "src/scripts/archive_mock_data.py"
)

UTIL_FILES=(
    "src/utils/aquatherm_data.py"
)

TEST_FILES=(
    "src/tests/e2e/test_aquatherm_overlay_removal.js"
    "src/tests/validate_aquatherm_integration.py"
    "src/tests/integration/monitoring/test_db_first_with_mock_indicators.py"
    "tests/e2e/aquatherm-tests.spec.js"
    "tests/simple_aquatherm_test.js"
)

# Function to move files with error checking
move_files() {
    local files=("$@")
    for file in "${files[@]}"; do
        if [ -f "$BASE_DIR/$file" ]; then
            target_dir="$ARCHIVE_DIR/$(dirname "$file")"
            mkdir -p "$target_dir"
            mv "$BASE_DIR/$file" "$target_dir/"
            echo "Moved: $file"
        else
            echo "Warning: File not found - $file"
        fi
    done
}

# Move the files
echo "Moving CSS files..."
move_files "${CSS_FILES[@]}"

echo "Moving JS files..."
move_files "${JS_FILES[@]}"

echo "Moving JS test files..."
move_files "${JS_TEST_FILES[@]}"

echo "Moving template files..."
move_files "${TEMPLATE_FILES[@]}"

echo "Moving API files..."
move_files "${API_FILES[@]}"

echo "Moving script files..."
move_files "${SCRIPT_FILES[@]}"

echo "Moving utility files..."
move_files "${UTIL_FILES[@]}"

echo "Moving test files..."
move_files "${TEST_FILES[@]}"

echo "Archive operation complete."
