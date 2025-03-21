from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
import argparse
import io
from pydub import AudioSegment
import csv


def vad_data_format(speaker1, speaker2, startAudioSegment):
    """
    Convert Silero VAD output into VAD data format for VAP-Realtime training.
    Ensures proper segment inclusion and prevents missing short segments.
    """

    speaker1_segment_speech = []
    speaker2_segment_speech = []
    speech_id_speaker1 = 0
    speech_id_speaker2 = 0

    # Ensure all valid speech segments are included
    while speech_id_speaker1 < len(speaker1) and speaker1[speech_id_speaker1]['end'] <= startAudioSegment:
        speech_id_speaker1 += 1

    while speech_id_speaker1 < len(speaker1) and speaker1[speech_id_speaker1]['start'] < startAudioSegment + 20:
        start_time = max(0, speaker1[speech_id_speaker1]['start'] - startAudioSegment)
        end_time = min(20, speaker1[speech_id_speaker1]['end'] - startAudioSegment)

        # Ensure very short segments are not ignored
        if end_time > start_time or (end_time - start_time) >= 0.05:
            speaker1_segment_speech.append([round(start_time, 6), round(end_time, 6)])
        speech_id_speaker1 += 1

    while speech_id_speaker2 < len(speaker2) and speaker2[speech_id_speaker2]['end'] <= startAudioSegment:
        speech_id_speaker2 += 1

    while speech_id_speaker2 < len(speaker2) and speaker2[speech_id_speaker2]['start'] < startAudioSegment + 20:
        start_time = max(0, speaker2[speech_id_speaker2]['start'] - startAudioSegment)
        end_time = min(20, speaker2[speech_id_speaker2]['end'] - startAudioSegment)

        if end_time > start_time or (end_time - start_time) >= 0.05:
            speaker2_segment_speech.append([round(start_time, 6), round(end_time, 6)])
        speech_id_speaker2 += 1

    return [speaker1_segment_speech, speaker2_segment_speech]


if __name__ == "__main__":

    # Argument Parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--path_audio_file", type=str, required=True, help="Path to the input audio file")
    parser.add_argument("--output_csv", type=str, default='output.csv', help="Output CSV file name")
    parser.add_argument("--recover", type=int, default=0, help="An integer between 0 and 19.")
    args = parser.parse_args()

    if not 0 <= args.recover <= 19:
        raise argparse.ArgumentTypeError(f"{args.recover} is not between 0 and 19")
    
    # Load the audio file
    audio_file = args.path_audio_file
    sound = AudioSegment.from_file(audio_file)

    # Split stereo audio into two mono channels
    first_speaker, second_speaker = sound.split_to_mono()

    # Stream the two channels separately (to avoid creating files)
    first_speaker_buffer = io.BytesIO()
    second_speaker_buffer = io.BytesIO()
    first_speaker.export(first_speaker_buffer, format="wav")
    second_speaker.export(second_speaker_buffer, format="wav")
    first_speaker_buffer.seek(0)
    second_speaker_buffer.seek(0)

    # Load Silero VAD model and process both channels
    model = load_silero_vad()
    first_speaker_audio = read_audio(first_speaker_buffer, sampling_rate=16000)
    second_speaker_audio = read_audio(second_speaker_buffer, sampling_rate=16000)

    speech_timestamps_first_speaker = get_speech_timestamps(
        first_speaker_audio, model, min_speech_duration_ms=50, min_silence_duration_ms=50, speech_pad_ms=10, return_seconds=True
    )
    
    speech_timestamps_second_speaker = get_speech_timestamps(
        second_speaker_audio, model, min_speech_duration_ms=50, min_silence_duration_ms=50, speech_pad_ms=10, return_seconds=True
    )

    # Create CSV file (input for model training)
    csv_data = [["audio_path", "start", "end", "vad_list", "session", "dataset"]]

    shift = args.recover
    startAudioSegment = 0

    # Ensure no extra segment is added at the end
    while startAudioSegment + 20 <= sound.duration_seconds:
        csv_data_line = [
            audio_file,
            startAudioSegment,
            startAudioSegment + 20,
            vad_data_format(speech_timestamps_first_speaker, speech_timestamps_second_speaker, startAudioSegment),
            0,  # Arbitrary
            "sample",  # Arbitrary
        ]
        csv_data.append(csv_data_line)
        startAudioSegment += 20 - shift

    # Save results to CSV
    with open(args.output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(csv_data)
