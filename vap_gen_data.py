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

    segment_start_time = segment_id * 20  # Start time of the segment (e.g., 40 for segment_id=2)
    segment_end_time = (segment_id + 1) * 20 + 2  # End time including the extra 2 seconds (e.g., 62 for segment_id=2)

    # Ensure we don't go out of range
    while speech_id_speaker1 < len(speaker1) and speaker1[speech_id_speaker1]['start'] < segment_start_time:
        speech_id_speaker1 += 1

    while speech_id_speaker1 < len(speaker1) and speaker1[speech_id_speaker1]['end'] < segment_end_time:
        speaker1_segment_speech.append([
            round(speaker1[speech_id_speaker1]['start'] - segment_start_time, 6),  # Normalize to 0-22s
            round(speaker1[speech_id_speaker1]['end'] - segment_start_time, 6)
        ])
        speech_id_speaker1 += 1

    while speech_id_speaker2 < len(speaker2) and speaker2[speech_id_speaker2]['start'] < segment_start_time:
        speech_id_speaker2 += 1

    while speech_id_speaker2 < len(speaker2) and speaker2[speech_id_speaker2]['end'] < segment_end_time:
        speaker2_segment_speech.append([
            round(speaker2[speech_id_speaker2]['start'] - segment_start_time, 6),  # Normalize to 0-22s
            round(speaker2[speech_id_speaker2]['end'] - segment_start_time, 6)
        ])
        speech_id_speaker2 += 1

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

    # Convert sampling rate to 16kHz
    sound = sound.set_frame_rate(16000)

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

    speech_timestamps_first_speaker = get_speech_timestamps(first_speaker_audio, model,min_speech_duration_ms = 50,min_silence_duration_ms= 50,speech_pad_ms = 10,return_seconds=True)
    speech_timestamps_second_speaker = get_speech_timestamps(second_speaker_audio, model,min_speech_duration_ms = 50,min_silence_duration_ms= 50,speech_pad_ms = 10,return_seconds=True)

    # Create the .csv file (input for the model training)
    csv_data = [
        ["audio_path", "start", "end", "vad_list", "session", "dataset"]
    ]

    step = 19  # Define overlap (controls how much segments overlap)
    segment_length = 20  # Define segment size

    for segment_id in range(int(sound.duration_seconds // step)):
        start_time = segment_id * step
        end_time = start_time + segment_length

        csv_data_line = [
            audio_file,
            start_time,
            end_time,
            vad_data_format(speech_timestamps_first_speaker, speech_timestamps_second_speaker, segment_id),
            0,  # Arbitrary
            "sample",  # Arbitrary
        ]
        csv_data.append(csv_data_line)
    with open(args.output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(csv_data) 