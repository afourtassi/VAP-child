from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
import argparse
import io
from pydub import AudioSegment
import csv


def vad_data_format(speaker1, speaker2, segment_id):
    # Convert silero_vad output into VAD data format for VAP-Realtime training (https://github.com/inokoj/VAP-Realtime/tree/main/train)

    speaker1_segment_speech = []
    speaker2_segment_speech = []
    speech_id_speaker1 = 0
    speech_id_speaker2 = 0

    while(speaker1[speech_id_speaker1]['start']<segment_id*20):
        speech_id_speaker1+=1
    while(speech_id_speaker1 < len(speaker1) and speaker1[speech_id_speaker1]['end']<(segment_id+1)*20+2): # 2 seconds window for future voice activity
        speaker1_segment_speech.append([speaker1[speech_id_speaker1]['start'], speaker1[speech_id_speaker1]['end']])
        speech_id_speaker1+=1

    while(speaker2[speech_id_speaker2]['start']<segment_id*20):
        speech_id_speaker2+=1
    while(speech_id_speaker2 < len(speaker2) and speaker2[speech_id_speaker2]['end']<(segment_id+1)*20+2): # 2 seconds window for future voice activity
        speaker2_segment_speech.append([speaker2[speech_id_speaker2]['start'], speaker2[speech_id_speaker2]['end']])
        speech_id_speaker2+=1

    return [speaker1_segment_speech, speaker2_segment_speech]

if __name__ == "__main__":

    # Argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--path_audio_file", type=str, default='')
    parser.add_argument("--output_csv", type=str, default='output.csv')
    args = parser.parse_args()

    # Load the audio file
    audio_file = args.path_audio_file
    sound = AudioSegment.from_file(audio_file)

    # Split the stereo audio into two mono channels
    first_speaker = sound.split_to_mono()[0]
    second_speaker = sound.split_to_mono()[1]

    # Stream the two channels separately (to avoid creating files)
    first_speaker_buffer = io.BytesIO()
    second_speaker_buffer = io.BytesIO()
    first_speaker.export(first_speaker_buffer, format="wav")
    second_speaker.export(second_speaker_buffer, format="wav")
    first_speaker_buffer.seek(0)
    second_speaker_buffer.seek(0)

    # Import model and read both channels
    model = load_silero_vad()
    first_speaker_audio = read_audio(first_speaker_buffer, sampling_rate=16000)
    second_speaker_audio = read_audio(second_speaker_buffer, sampling_rate=16000)

    speech_timestamps_first_speaker = get_speech_timestamps(first_speaker_audio, model,return_seconds=True)
    speech_timestamps_second_speaker = get_speech_timestamps(second_speaker_audio, model,return_seconds=True)

    # Create the .csv file (input for the model training)
    csv_data = [
        ["audio_path", "start", "end", "vad_list", "session", "dataset"]
    ]

    for segment_id in range(int(-(sound.duration_seconds // -20))): # The model can only take one audio segment of a maximum size of 20 seconds
        csv_data_line = [
            audio_file, 
            segment_id*20, 
            (segment_id+1)*20, 
            vad_data_format(speech_timestamps_first_speaker, speech_timestamps_second_speaker, segment_id),
            0, # Arbitrary
            "sample", # Arbitrary
            ]
        csv_data.append(csv_data_line)

    with open(args.output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(csv_data) 