from pydub import AudioSegment
from pydub.utils import make_chunks

audio_file_path = ""
# Load the audio file
audio = AudioSegment.from_file(audio_file_path)

# Define chunk length in milliseconds (5 seconds = 5000 ms)
chunk_length_ms = 5000*9

# Split the audio into chunks
chunks = make_chunks(audio, chunk_length_ms)

# Export each chunk to a separate file
for i, chunk in enumerate(chunks):
    chunk_name = f"chunk_{i+1}.wav"
    print(f"Exporting {chunk_name}")
    chunk.export(chunk_name, format="wav")   