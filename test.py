import os
from google.cloud import texttospeech
from pydub import AudioSegment
import math

# === SETTINGS ===
input_text_file = "Topic1.txt"
spoken_text_output = "spoken_text_used.txt"
output_trimmed_audio = "output_12min.mp3"
output_full_audio = "combined_output.mp3"

pause_ms = 350  # pause between words
speaking_rate = 0.85
target_duration_ms = 12 * 60 * 1000
words_per_chunk = 100  # safe chunk size for API

# === Step 1: Load and chunk text ===
with open(input_text_file, "r") as f:
    raw_text = f.read().strip()

all_words = raw_text.split()
chunks = [all_words[i:i + words_per_chunk] for i in range(0, len(all_words), words_per_chunk)]

# Save spoken text
with open(spoken_text_output, "w") as f:
    f.write(" ".join(all_words))
print(f"Spoken text saved to {spoken_text_output}")

# Initialize TTS client
client = texttospeech.TextToSpeechClient()

# Process each chunk
chunk_files = []
for i, words in enumerate(chunks):
    ssml = "<speak>" + ("<break time='{}ms'/>".format(pause_ms)).join(words) + "</speak>"
    synthesis_input = texttospeech.SynthesisInput(ssml=ssml)

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-GB",  # Or "en-US" if preferred
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speaking_rate
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    chunk_filename = f"chunk_{i+1}.mp3"
    with open(chunk_filename, "wb") as out:
        out.write(response.audio_content)
        print(f"Chunk {i+1} saved: {chunk_filename}")
    chunk_files.append(chunk_filename)

# === Step 2: Concatenate all chunks ===
print("Combining chunks...")
combined = AudioSegment.empty()
for file in chunk_files:
    audio = AudioSegment.from_file(file, format="mp3")
    combined += audio

combined.export(output_full_audio, format="mp3")
print(f"Combined audio saved to {output_full_audio}")

# === Step 3: Trim to exactly 12 minutes and match spoken text ===
spoken_words_trimmed = []
accumulated_audio = AudioSegment.empty()
total_duration = 0

for i, file in enumerate(chunk_files):
    audio = AudioSegment.from_file(file, format="mp3")
    if total_duration + len(audio) <= target_duration_ms:
        accumulated_audio += audio
        spoken_words_trimmed.extend(chunks[i])
        total_duration += len(audio)
    else:
        # Add only the portion that fits
        remaining_ms = target_duration_ms - total_duration
        accumulated_audio += audio[:remaining_ms]
        
        # Estimate proportion of words that fit in this partial chunk
        words_in_chunk = chunks[i]
        proportion = remaining_ms / len(audio)
        words_to_keep = math.floor(proportion * len(words_in_chunk))
        spoken_words_trimmed.extend(words_in_chunk[:words_to_keep])
        break

# Export trimmed audio
accumulated_audio.export(output_trimmed_audio, format="mp3")
print(f"Trimmed 12-minute audio saved to {output_trimmed_audio}")

# Export matched spoken text
with open(spoken_text_output, "w") as f:
    f.write(" ".join(spoken_words_trimmed))
print(f"Trimmed spoken text saved to {spoken_text_output}")



