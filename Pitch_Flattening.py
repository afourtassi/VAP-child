import os
import parselmouth
import numpy as np
import soundfile as sf

def flatten_pitch(input_path, output_path, flatten_method="mean"):
    """
    Process a stereo audio file and flatten its pitch while preserving the stereo channels.
    
    Parameters:
        input_path (str): Path to the input audio file.
        output_path (str): Path to save the processed audio file.
        flatten_method (str): Method to flatten pitch ('mean' or 'linear').
    """
    # Load the audio file
    audio, sr = sf.read(input_path)
    processed_channels = []
    
    # Process each channel separately
    for channel_idx in range(audio.shape[1]):
        sound = parselmouth.Sound(audio[:, channel_idx], sampling_frequency=sr)
        pitch = sound.to_pitch()
        pitch_values = pitch.selected_array['frequency']
        
        # Choose pitch flattening method
        if flatten_method == "mean":
            mean_pitch = np.nanmean(pitch_values[pitch_values > 0])  
            flattened_pitch = np.full_like(pitch_values, mean_pitch)  
        else:  # Linear interpolation
            flattened_pitch = np.interp(
                np.arange(len(pitch_values)),
                np.where(pitch_values > 0)[0],
                pitch_values[pitch_values > 0]
            )
        
        manipulation = parselmouth.praat.call(sound, "To Manipulation", 0.01, 75, 600)
        pitch_tier = parselmouth.praat.call(manipulation, "Extract pitch tier")
        parselmouth.praat.call(pitch_tier, "Remove points between", 0, sound.duration)
        
        time_step = 0.01
        times = np.arange(0, sound.duration, time_step)
        for t in times:
            idx = int(t / time_step)
            if idx < len(flattened_pitch) and flattened_pitch[idx] > 0:
                parselmouth.praat.call(pitch_tier, "Add point", t, flattened_pitch[idx])
        
        parselmouth.praat.call([pitch_tier, manipulation], "Replace pitch tier")
        resynthesized = parselmouth.praat.call(manipulation, "Get resynthesis (overlap-add)")
        processed_channels.append(resynthesized.values[0])
    
    # Combine processed stereo channels
    stereo_audio = np.column_stack(processed_channels)
    sf.write(output_path, stereo_audio, sr, subtype='PCM_16')

def process_directory(input_dir, output_dir, flatten_method="mean"):
    """
    Process all .wav files in a directory by flattening their pitch and saving them to an output directory.
    
    Parameters:
        input_dir (str): Path to the input directory containing .wav files.
        output_dir (str): Path to the output directory where processed files will be saved.
        flatten_method (str): Method to flatten pitch ('mean' or 'linear').
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for filename in os.listdir(input_dir):
        if filename.endswith(".wav"):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)

            # Check if the file already exists in the output directory
            if os.path.exists(output_path):
                print(f"⚠️ File already exists, skipping: {filename}")
                continue  # Skip to the next file

            print(f" Processing {filename}...")
            flatten_pitch(input_path, output_path, flatten_method)
            print(f"✅ Saved: {output_path}")

if __name__ == "__main__":
    input_directory = ""  # Directory containing input audio files
    output_directory = ""  # Directory to save processed files
    
    process_directory(input_directory, output_directory, flatten_method="mean")
    print("✅ All .wav files have been processed!")
