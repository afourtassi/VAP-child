import re
import numpy as np
import wave
import argparse

def find_speech_overlaps(timestamps_dic):
    # Return a list of tuple with every overlaps in a dict of timestamps
    overlaps_list = []

    dict_keys = list(timestamps_dic.keys())
    for speaker1 in range(len(dict_keys)-1): # Don't compare the last speaker, useless
        for speaker2 in range(speaker1 +1, len(dict_keys)):
            for i in range(len(timestamps_dic[dict_keys[speaker1]])):
                start1, end1 = timestamps_dic[dict_keys[speaker1]][i]
                for j in range(len(timestamps_dic[dict_keys[speaker2]])):
                    start2, end2 = timestamps_dic[dict_keys[speaker2]][j]

                    # Check for overlap:
                    if start1 < end2 and start2 < end1:
                        overlaps_list.append(((dict_keys[speaker1], i), (dict_keys[speaker2], j)))
    return overlaps_list


def extract_timestamps(filepath):
    # Extract timestamps of speechs from a .cha file and return them as a dictionnary of tuple (start : int, end : int) with key as speaker id
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Use regular expression to find timestamp wrapped between NAK characters ( \x15 in hex)
    extracted_string = re.findall(r'\*(.*?):.*?\x15(.*?)\x15', content)
    # Add timestamps in a dictionnary
    timestamps_dic = {}
    for string in extracted_string:
            num1, num2 = map(int, string[1].split('_'))
            if string[0] not in timestamps_dic:
                timestamps_dic[string[0]] = [(num1, num2)]
            else:
                timestamps_dic[string[0]].append((num1, num2))
            
    return timestamps_dic

def mono_to_stereo(wav_mono_path, timestamps_dict, output_path):
    # Create a stereo .wav from a mono .wav and a timestamps dictionnary
    with wave.open(wav_mono_path, 'rb') as mono_wav:
        n_channels = mono_wav.getnchannels()
        sample_width = mono_wav.getsampwidth()
        frame_rate = mono_wav.getframerate()
        n_frames = mono_wav.getnframes()
        audio_data = np.frombuffer(mono_wav.readframes(n_frames), dtype=np.int16)
        
        stereo_data = np.zeros((n_frames, 2), dtype=np.int16)

        for speaker, timestamps in timestamps_dict.items():
            if speaker == 'CHI':
                channel = 0
            else:
                channel = 1
            
            for start_ms, end_ms in timestamps:
                start_frame = int((start_ms / 1000) * frame_rate)
                end_frame = int((end_ms / 1000) * frame_rate)
                stereo_data[start_frame:end_frame, channel] = audio_data[start_frame:end_frame]
        
        stereo_data_flat = stereo_data.flatten().tobytes()

        with wave.open(output_path, 'wb') as stereo_wav:
                stereo_wav.setnchannels(2)
                stereo_wav.setsampwidth(sample_width)
                stereo_wav.setframerate(frame_rate)
                stereo_wav.writeframes(stereo_data_flat)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--path_audio_file", type=str, default='')
    parser.add_argument("--path_transcript_file", type=str, default='')
    parser.add_argument("--output_stereo_wav", type=str, default='output.wav')
    args = parser.parse_args()

    timestamps_dict = extract_timestamps(args.path_transcript_file)
    overlaps = find_speech_overlaps(timestamps_dict)

    mono_to_stereo(args.path_audio_file, timestamps_dict, args.output_stereo_wav)

    # Display overlaps speakers and timestamps in the console
    for overlap in overlaps:
        print(f"Overlap timestamp {overlap[0][0]}/{overlap[1][0]}: ({timestamps_dict[overlap[0][0]][overlap[0][1]][0]}_{timestamps_dict[overlap[0][0]][overlap[0][1]][1]}|{timestamps_dict[overlap[1][0]][overlap[1][1]][0]}_{timestamps_dict[overlap[1][0]][overlap[1][1]][1]})")