#!/bin/bash

# Define the final CSV file 
OUTPUT_CSV="data_vap_swb_all.csv"

# Check if the CSV file already exists, otherwise create it 
if [ ! -f "$OUTPUT_CSV" ]; then
    echo "audio_path,start,end,vad_list,session,dataset" > "$OUTPUT_CSV"
fi

# Get the current directory containing .wav files
DATA_DIR="$(pwd)"

for wav_file in "$DATA_DIR"/*.wav; do
    # Check if no .wav file is found
    if [ ! -e "$wav_file" ]; then
        echo " No .wav file found in $DATA_DIR"
        exit 1
    fi

    echo "🔹Processing file: $wav_file"

    # Ensure the file exists before proceeding
    if [ ! -f "$wav_file" ]; then
        echo " ERROR: File not found - $wav_file"
        continue
    fi

    # Define a temporary file to store intermediate results
    TEMP_CSV="temp_output.csv"

    # Run the Python script `vap_gen_data.py` on the audio file
    python vap_gen_data.py --path_audio_file "$wav_file" --output_csv "$TEMP_CSV"

    # Verify if the temporary file was generated successfully
    if [ ! -f "$TEMP_CSV" ]; then
        echo " ERROR: temp_output.csv was not generated for $wav_file"
        continue
    fi

    # Append the results to the final CSV file 
    tail -n +2 "$TEMP_CSV" >> "$OUTPUT_CSV"

    # Delete the temporary file after use
    rm "$TEMP_CSV"

    echo " File successfully processed : $wav_file"
done

echo " All files have been processed, and results are stored in $OUTPUT_CSV"
