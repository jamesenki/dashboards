#!/bin/bash
# Script to archive files that will be replaced by CDC and Message Broker architecture
# Created: $(date)

# Setup archive directory with today's date
ARCHIVE_DIR="./archive/$(date +%Y%m%d)_pre_cdc_architecture"
mkdir -p "$ARCHIVE_DIR/src"
mkdir -p "$ARCHIVE_DIR/tests"
mkdir -p "$ARCHIVE_DIR/scripts"

# Log file for the archive process
LOG_FILE="$ARCHIVE_DIR/archive_manifest.log"
echo "IoTSphere Pre-CDC Architecture Archive" > "$LOG_FILE"
echo "Created: $(date)" >> "$LOG_FILE"
echo "===============================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Function to archive a file with proper structure
archive_file() {
    local src_file="$1"
    local dest_dir=$(dirname "$ARCHIVE_DIR/$src_file")

    # Create destination directory if it doesn't exist
    mkdir -p "$dest_dir"

    # Copy file to archive
    if [ -f "$src_file" ]; then
        cp "$src_file" "$ARCHIVE_DIR/$src_file"
        echo "Archived: $src_file" >> "$LOG_FILE"
    else
        echo "Warning: File not found - $src_file" >> "$LOG_FILE"
    fi
}

echo "Starting archival process..."

# Scripts related to shadow data that will be replaced by CDC
archive_file "scripts/create_specific_shadow.py"
archive_file "scripts/ensure_all_shadows.py"
archive_file "scripts/populate_device_shadows.py"
archive_file "scripts/test_mongodb_shadow_storage.py"
archive_file "scripts/verify_mongodb_shadows.py"

# Test files that will be replaced or updated
archive_file "tests/api/test_device_shadow_api.py"
archive_file "tests/services/test_mongodb_shadow_storage.py"

# Legacy shadow polling-based components to be replaced by CDC
archive_file "src/micro-frontends/water-heaters/device-details/components/anomaly-alerts.js"
archive_file "src/services/shadow_notification_service.py"

# Shadow data services and APIs that will be refactored or replaced
archive_file "src/api/device_shadow.py"
archive_file "src/api/routes/device_shadows.py"
archive_file "src/api/setup_shadow_api.py"
archive_file "src/api/shadow_document_api.py"
archive_file "src/infrastructure/device_shadow/init_shadow_store.py"
archive_file "src/infrastructure/device_shadow/mongodb_shadow_storage.py"
archive_file "src/services/device_shadow.py"

echo "Archive complete. See $LOG_FILE for details."
echo ""
echo "IMPORTANT: These files have been copied to the archive directory."
echo "After implementing the CDC architecture, review the application functionality"
echo "before permanently removing these files."
