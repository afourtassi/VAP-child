#!/bin/bash

# Define the destination folder for the converted files
DESTINATION="/home/youcef.brahimi/Downloads/wav_files"

# Create the destination folder if it doesn't exist
mkdir -p "$DESTINATION"

# Directories containing .sph files
SOURCE_DIRS=("swb1_d1_data" "swb1_d2_data" "swb1_d3_data" "swb1_d4_data")

# Loop through each source directory
for dir in "${SOURCE_DIRS[@]}"; do
  echo "Searching in directory: /home/youcef.brahimi/Downloads/$dir"

  # Find all .sph files and convert them to .wav with 16kHz
  find "/home/youcef.brahimi/Downloads/$dir" -type f -name "*.sph" | while read FILE_PATH; do
    OUTPUT_FILE="$DESTINATION/$(basename "${FILE_PATH%.sph}.wav")"

    echo "Processing: $FILE_PATH"

    # Check if the destination folder is writable
    if [ ! -w "$DESTINATION" ]; then
        echo "❌ ERROR: No write permission on $DESTINATION"
        exit 1
    fi

    # Convert using SoX
    sox "$FILE_PATH" -r 16000 -b 16 -e signed-integer "$OUTPUT_FILE"

    if [ $? -eq 0 ]; then
        echo "✅ File converted: $OUTPUT_FILE"
    else
        echo "❌ ERROR: Conversion failed for $FILE_PATH"
    fi
  done
done

echo " Conversion completed. The .wav files are in $DESTINATION"
