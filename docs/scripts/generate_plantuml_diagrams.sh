#!/bin/bash

# Script to generate PlantUML diagrams as PNG files with high contrast theme
# Following TDD principles by ensuring diagrams are visible on any background

echo "===== IoTSphere Architecture Diagram Generator ====="
echo "Generating PlantUML diagrams with high-visibility theme..."

# Set up directories
DOCS_DIR="/Users/lisasimon/repos/IoTSphereAngular/IoTSphere-Refactor/docs"
PLANTUML_DIR="$DOCS_DIR/architecture/plantuml"
IMAGES_DIR="$DOCS_DIR/architecture/images"
TEMP_DIR="/tmp/iotsphere_plantuml"

# Create directories if they don't exist
mkdir -p "$PLANTUML_DIR" "$IMAGES_DIR" "$TEMP_DIR"

# Check if PlantUML JAR exists, if not download it
PLANTUML_JAR="$TEMP_DIR/plantuml.jar"
if [ ! -f "$PLANTUML_JAR" ]; then
    echo "Downloading PlantUML..."
    curl -L https://sourceforge.net/projects/plantuml/files/plantuml.jar/download -o "$PLANTUML_JAR"
    if [ $? -ne 0 ]; then
        echo "Failed to download PlantUML. Please check your internet connection."
        exit 1
    fi
fi

# Define a custom theme for high visibility on any background
cat > "$TEMP_DIR/theme.puml" << EOF
!define BACKGROUND_COLOR white
!define PRIMARY_COLOR #1168BD
!define SECONDARY_COLOR #85BBF0
!define TERTIARY_COLOR #FF8C00
!define TEXT_COLOR black
!define BORDER_COLOR #333333
!define LINE_COLOR #555555

skinparam backgroundColor BACKGROUND_COLOR
skinparam defaultTextAlignment center

skinparam ArrowColor LINE_COLOR
skinparam ArrowThickness 1.5

skinparam rectangle {
    BorderColor BORDER_COLOR
    FontColor TEXT_COLOR
    BackgroundColor BACKGROUND_COLOR
    BorderThickness 2
}

skinparam database {
    BorderColor BORDER_COLOR
    FontColor TEXT_COLOR
    BackgroundColor BACKGROUND_COLOR-#eee
    BorderThickness 2
}

skinparam actor {
    BorderColor PRIMARY_COLOR
    FontColor TEXT_COLOR
    BackgroundColor BACKGROUND_COLOR
    BorderThickness 2
}

skinparam component {
    BorderColor BORDER_COLOR
    FontColor TEXT_COLOR
    BackgroundColor BACKGROUND_COLOR
    BorderThickness 2
}

skinparam interface {
    BorderColor BORDER_COLOR
    FontColor TEXT_COLOR
    BackgroundColor BACKGROUND_COLOR
    BorderThickness 2
}

skinparam note {
    BorderColor TERTIARY_COLOR
    FontColor TEXT_COLOR
    BackgroundColor BACKGROUND_COLOR-#ffe
    BorderThickness 1
}

skinparam cloud {
    BorderColor BORDER_COLOR
    FontColor TEXT_COLOR
    BackgroundColor BACKGROUND_COLOR
    BorderThickness 2
}

skinparam sequence {
    ArrowColor LINE_COLOR
    LifeLineBorderColor LINE_COLOR
    LifeLineBackgroundColor BACKGROUND_COLOR
    ParticipantBorderColor BORDER_COLOR
    ParticipantFontColor TEXT_COLOR
    ParticipantBackgroundColor BACKGROUND_COLOR
    ActorBorderColor PRIMARY_COLOR
    ActorFontColor TEXT_COLOR
    ActorBackgroundColor BACKGROUND_COLOR
}

skinparam class {
    BorderColor BORDER_COLOR
    FontColor TEXT_COLOR
    BackgroundColor BACKGROUND_COLOR
    BorderThickness 2
    AttributeFontColor TEXT_COLOR
    AttributeFontSize 12
}

skinparam stereotypeCBackgroundColor SECONDARY_COLOR
EOF

# Function to generate a PNG from a PlantUML file
generate_png() {
    local input_file="$1"
    local output_file="$2"
    local base_name=$(basename "$input_file" .puml)
    
    echo "Generating diagram: $base_name"
    
    # Include the theme in each diagram
    tmp_file="$TEMP_DIR/$base_name.puml"
    echo "@startuml" > "$tmp_file"
    echo "!include $TEMP_DIR/theme.puml" >> "$tmp_file"
    echo "scale 1.5" >> "$tmp_file"
    tail -n +2 "$input_file" >> "$tmp_file"
    
    # Generate PNG
    java -jar "$PLANTUML_JAR" -tpng "$tmp_file" -o "$(dirname "$output_file")"
    if [ $? -ne 0 ]; then
        echo "❌ Failed to generate diagram: $base_name"
        return 1
    fi
    
    # Move output file to the correct location if needed
    generated_file="$TEMP_DIR/$base_name.png"
    if [ -f "$generated_file" ]; then
        mv "$generated_file" "$output_file"
    fi
    
    echo "✅ Generated: $output_file"
    return 0
}

# Process all PlantUML files
process_plantuml_files() {
    local success_count=0
    local total_count=0
    
    for puml_file in "$PLANTUML_DIR"/*.puml; do
        if [ -f "$puml_file" ]; then
            base_name=$(basename "$puml_file" .puml)
            output_file="$IMAGES_DIR/$base_name.png"
            
            generate_png "$puml_file" "$output_file"
            if [ $? -eq 0 ]; then
                ((success_count++))
            fi
            ((total_count++))
        fi
    done
    
    echo ""
    echo "Diagram generation complete."
    echo "Successfully generated $success_count out of $total_count diagrams."
    echo "PNG files are located in: $IMAGES_DIR"
}

# Main execution
process_plantuml_files

exit 0
