import librosa
import numpy as np
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import torch
from pydub import AudioSegment
import io


# from gruut import sentences
# from gruut import tokenize
# from gruut_ipa import convert_ipa_to_arpabet

#START SLOWER TRANSFORMER MFA WAV2VEC2-------------------------------------
# # ---------------------------------------------------------
# # Load lightweight Wav2Vec2 CTC model (cached locally)
# # ---------------------------------------------------------
# processor = Wav2Vec2Processor.from_pretrained(
#     "jonatasgrosman/wav2vec2-large-xlsr-53-english"
# )
# model = Wav2Vec2ForCTC.from_pretrained(
#     "jonatasgrosman/wav2vec2-large-xlsr-53-english"
# )
# model.eval()


# # ---------------------------------------------------------
# # Grapheme → phonemes using Gruut (FULL CMU-LIKE G2P)
# # ---------------------------------------------------------
# def g2p_char(char, next_char=None):
#     """
#     Map a single English character to ARPAbet phonemes using Gruut.
#     Uses:
#        - dictionary entries
#        - rule-based fallbacks
#     """

#     # Gruut expects whole words, so we wrap the char
#     text = char

#     # Gruut tokenization
#     toks = tokenize(text, lang="en")

#     # If Gruut doesn’t know the char, fallback manually
#     if len(toks) == 0 or toks[0].text is None:
#         return []

#     # Get IPA phonemes from Gruut
#     ipa_phones = []
#     for sent in sentences(text, lang="en"):
#         for word in sent:
#             for pron in word.pronunciations:
#                 ipa_phones.extend(pron.ipa)

#     # Convert IPA → ARPAbet
#     arpabet = []
#     for ipa in ipa_phones:
#         arpa = convert_ipa_to_arpabet(ipa)
#         arpabet.extend(arpa)

#     # If no ARPAbet found → fallback rule-based
#     if len(arpabet) == 0:
#         fallback = fallback_char_to_phonemes(char, next_char)
#         return fallback

#     return arpabet


# # ---------------------------------------------------------
# # Lightweight rule-based fallback (only when Gruut fails)
# # ---------------------------------------------------------
# def fallback_char_to_phonemes(c, next_char=None):
#     c = c.lower()
#     cmap = {
#         "a": ["AE"],
#         "b": ["B"],
#         "c": ["K"],
#         "d": ["D"],
#         "e": ["EH"],
#         "f": ["F"],
#         "g": ["G"],
#         "h": ["HH"],
#         "i": ["IH"],
#         "j": ["JH"],
#         "k": ["K"],
#         "l": ["L"],
#         "m": ["M"],
#         "n": ["N"],
#         "o": ["OW"],
#         "p": ["P"],
#         "q": ["K"],
#         "r": ["R"],
#         "s": ["S"],
#         "t": ["T"],
#         "u": ["UW"],
#         "v": ["V"],
#         "w": ["W"],
#         "x": ["K", "S"],
#         "y": ["Y"],
#         "z": ["Z"]
#     }

#     # Soft C/G logic
#     if c == "c" and next_char in ["e", "i", "y"]:
#         return ["S"]
#     if c == "g" and next_char in ["e", "i", "y"]:
#         return ["JH"]

#     return cmap.get(c, [])


# # ---------------------------------------------------------
# # Mini CTC aligner for multi-phoneme graphemes
# # ---------------------------------------------------------
# def ctc_align_slice(audio_slice, sr, phones):
#     inputs = processor(audio_slice, sampling_rate=sr, return_tensors="pt")
#     with torch.no_grad():
#         logits = model(inputs.input_values).logits[0].cpu().numpy()

#     # Convert logits to most likely frames
#     probs = torch.nn.functional.softmax(torch.tensor(logits), dim=-1).numpy()
#     frames = probs.argmax(axis=-1)

#     # Divide frames into equal chunks per phoneme
#     total_frames = len(frames)
#     per_phone = total_frames // len(phones)

#     results = []
#     for i, p in enumerate(phones):
#         fs = i * per_phone
#         fe = (i + 1) * per_phone if i < len(phones)-1 else total_frames
#         frame_dur = len(audio_slice) / sr / total_frames
#         results.append((p, fs * frame_dur, fe * frame_dur))

#     return results


# # ---------------------------------------------------------
# # MAIN FUNCTION
# # Converts character timestamps → phoneme timestamps
# # ---------------------------------------------------------
# def align_characters_to_phonemes(audio, char_timestamps):
#     """
#     char_timestamps = list of:
#         (char, start_time_sec, end_time_sec)
#     """

#     audio, sr = librosa.load(audio, sr=16000)
#     aligned = []

#     for i, (char, start, end) in enumerate(char_timestamps):
#         next_char = char_timestamps[i+1][0] if i+1 < len(char_timestamps) else None

#         phones = g2p_char(char, next_char)

#         # No phones → skip
#         if len(phones) == 0:
#             continue

#         # Single-phone → no acoustic alignment needed
#         if len(phones) == 1:
#             aligned.append((phones[0], start, end))
#             continue

#         # Multi-phone → CTC on the slice
#         s = int(start * sr)
#         e = int(end * sr)
#         slice_audio = audio[s:e]
#         phone_times = ctc_align_slice(slice_audio, sr, phones)

#         # Convert to absolute times
#         for phone, ps, pe in phone_times:
#             aligned.append((phone, start + ps, start + pe))

#     return aligned

#END SLOWER TRANSFORMER MFA WAV2VEC2-------------------------------------

#Shared function to normalize the elabs response for use in the following functions


def mp3_bytes_to_wav_bytes(mp3_bytes: bytes) -> bytes:
    # Load MP3 from memory
    mp3_stream = io.BytesIO(mp3_bytes)
    audio = AudioSegment.from_mp3(mp3_stream)

    # Export to WAV in memory
    wav_stream = io.BytesIO()
    audio.export(wav_stream, format="wav")

    return wav_stream.getvalue()

def normalize_input(input_json):
    chars = input_json["alignment"]["characters"]
    starts = input_json["alignment"]["start_times"]
    ends   = input_json["alignment"]["end_times"]

    char_times = [
        {"char": chars[i], "start": starts[i], "end": ends[i]}
        for i in range(len(chars))
    ]

    text = "".join(chars)

    return text, char_times

def denormalize_output(alignment_json):
    alignment = {'phonemes':[], 'starts':[], 'ends':[]}
    for x in alignment_json:
        alignment["phonemes"].append(x['phoneme'])
        alignment['starts'].append(x['start'])
        alignment['ends'].append(x['end'])
    return alignment

def audio_to_float32(audio_source, target_sr=16000, audio_format='wav'):
    """
    Convert audio from mp3 bytes to mono float32 waveform at target sample rate.
    
    Parameters:
        audio_source: str, Path to file OR BytesIO
        target_sr: int, desired sampling rate (default 16 kHz)
        
    Returns:
        np.ndarray: 1D float32 array in range [-1, 1]
    """
    # Load audio
    audio_segment = AudioSegment.from_file(io.BytesIO(audio_source), format=audio_format)
    
    # Convert to mono
    audio_segment = audio_segment.set_channels(1)
    
    # Convert sample rate
    audio_segment = audio_segment.set_frame_rate(target_sr)
    
    # Convert to numpy float32
    audio_np = np.array(audio_segment.get_array_of_samples()).astype(np.float32)
    
    # Normalize to [-1, 1]
    max_val = np.iinfo(audio_segment.array_type).max
    audio_np /= max_val
    
    return audio_np

# # =========================================================
# #   VERSION A — PURE CHARACTER-BASED PHONEME ALIGNER
# #   Uses: g2p-en (ARPAbet), merging character timestamps
# # =========================================================

# from g2p_en import G2p

# g2p = G2p()


# def text_to_phonemes(text):
#     """
#     Converts text to ARPAbet phonemes using g2p-en.
#     Filters out non-phoneme tokens.
#     """
#     raw = g2p(text)
#     return [p for p in raw if p.isalpha()]  # keep phonemes only


# def align_chars_to_phonemes(text, char_times, phonemes):
#     """
#     Aligns character timestamps to phoneme timestamps.

#     char_times: list of {char, start, end}
#     phonemes: list of phoneme strings (e.g. ["DH", "AH"])
#     """
#     idx = 0
#     alignments = []

#     for phon in phonemes:
#         start = None
#         end = None
#         consumed_chars = ""

#         # greedily consume characters as part of this phoneme
#         # until at least 1 character is used
#         while idx < len(char_times) and consumed_chars == "":
#             entry = char_times[idx]

#             if start is None:
#                 start = entry["start"]
#             end = entry["end"]

#             consumed_chars += entry["char"]
#             idx += 1

#         alignments.append({
#             "phoneme": phon,
#             "start": start,
#             "end": end
#         })

#     return alignments


# # ---------------------------------------------------------
# # Example Usage
# # ---------------------------------------------------------
# # if __name__ == "__main__":
# #     text = "the"
# #     char_times = [
# #         {"char": "t", "start": 0.20, "end": 0.24},
# #         {"char": "h", "start": 0.24, "end": 0.30},
# #         {"char": "e", "start": 0.30, "end": 0.45},
# #     ]

# #     phonemes = text_to_phonemes(text)   # -> ['DH', 'AH']
# #     aligned = align_chars_to_phonemes(text, char_times, phonemes)

# #     print(aligned)

# # =========================================================
# #   VERSION B — ADVANCED HIGH-ACCURACY PHONEME ALIGNER
# #   Fixes corner cases while still using only character
# #   alignment + G2P (no audio).
# # =========================================================

# from g2p_en import G2p
# import re

# g2p = G2p()

# # multi-letter graphemes
# GRAPHEME_CLUSTERS = [
#     "sh", "ch", "th", "ph", "gh", "ng", "wh", "ck",
#     "ea", "ou", "oi", "ai", "au", "ow", "ie", "ee", "oa"
# ]

# # known silent letters
# SILENT_CHARS = [
#     "k" , # knight
#     "w" , # write
#     "b" , # lamb
#     "l" , # half, talk
#     "e" , # word-final silent e
# ]

# # heuristics for schwa detection
# SCHWA_PATTERN = re.compile(r"(a|e|i|o|u)")


# def detect_silent(char, idx, text):
#     """Silence heuristics (high accuracy)."""
#     # final silent 'e'
#     if char == "e" and idx == len(text) - 1:
#         return True

#     # "kn" (k silent)
#     if idx == 0 and char == "k" and text.startswith("kn"):
#         return True

#     # "wr" (w silent)
#     if idx == 0 and char == "w" and text.startswith("wr"):
#         return True

#     # "gh" silent (night)
#     if char == "g" and text[idx:idx+2] == "gh":
#         return True

#     return False


# def greedy_graphemes(text):
#     """Split text into best-guess grapheme chunks."""
#     text = text.lower()
#     chunks = []
#     i = 0

#     while i < len(text):
#         # match clusters first
#         matched = False
#         for cluster in GRAPHEME_CLUSTERS:
#             if text[i:].startswith(cluster):
#                 chunks.append(cluster)
#                 i += len(cluster)
#                 matched = True
#                 break

#         if not matched:
#             chunks.append(text[i])
#             i += 1

#     return chunks


# def text_to_phonemes(text):
#     """ARPAbet phonemes from g2p-en."""
#     raw = g2p(text)
#     return [p for p in raw if p.isalpha()]


# def align_chars_to_phonemes_advanced(text, char_times, phonemes):
#     """
#     High-accuracy mapping of grapheme chunks → phonemes using:
#     - cluster detection
#     - silent letter removal
#     - vowel cluster splitting
#     """
#     text = text.lower()
#     graphemes = greedy_graphemes(text)

#     g_idx = 0  # index in graphemes
#     c_idx = 0  # index in char_times

#     results = []

#     for phon in phonemes:
#         start = None
#         end = None

#         # assign characters belonging to this phoneme
#         while g_idx < len(graphemes) and start is None:
#             g = graphemes[g_idx]

#             # skip silent graphemes
#             if len(g) == 1 and detect_silent(g, g_idx, text):
#                 g_idx += 1
#                 c_idx += 1
#                 continue

#             # accumulate char times for this grapheme
#             for _ in range(len(g)):
#                 entry = char_times[c_idx]

#                 if start is None:
#                     start = entry["start"]
#                 end = entry["end"]

#                 c_idx += 1

#             g_idx += 1

#         results.append({
#             "phoneme": phon,
#             "start": start,
#             "end": end
#         })

#     return results


# ---------------------------------------------------------
# Example Usage
# ---------------------------------------------------------
# if __name__ == "__main__":
#     text = "thought"
#     char_times = [
#         {"char":"t","start":0.00,"end":0.05},
#         {"char":"h","start":0.05,"end":0.10},
#         {"char":"o","start":0.10,"end":0.22},
#         {"char":"u","start":0.22,"end":0.32},
#         {"char":"g","start":0.32,"end":0.35},
#         {"char":"h","start":0.35,"end":0.38},
#         {"char":"t","start":0.38,"end":0.46},
#     ]

#     phonemes = text_to_phonemes(text)
#     aligned = align_chars_to_phonemes_advanced(text, char_times, phonemes)

#     print(aligned)


# START OF ONNXRUNTIME ARM OPTIMIZED PHONEME ALIGNER MFA IMPLEMENTATION---------


def ctc_decode(logits, blank_id=0):
    """
    Simple CTC greedy decoder.
    Returns a list of phoneme IDs with repeats and blanks removed.
    """
    pred_ids = np.argmax(logits, axis=-1)

    decoded = []
    prev = blank_id

    for p in pred_ids:
        if p != blank_id and p != prev:
            decoded.append(p)
        prev = p

    return decoded

def phoneme_timestamps(logits, phoneme_map, sr=16000, hop_ms=20):
    """
    Turns model logits into phoneme + timestamps.
    hop_ms: model frame stride, usually 20ms for wav2vec2
    """
    timestep = hop_ms / 1000.0
    pred_ids = np.argmax(logits, axis=-1)

    results = []
    prev_id = None
    start_t = 0

    for i, p in enumerate(pred_ids):
        if p != prev_id:
            if prev_id is not None and prev_id != 0:  # ignore blank
                results.append({
                    "phoneme": phoneme_map[prev_id],
                    "start": start_t,
                    "end": i * timestep
                })
            prev_id = p
            start_t = i * timestep

    # append final
    if prev_id is not None and prev_id != 0:
        results.append({
            "phoneme": phoneme_map[prev_id],
            "start": start_t,
            "end": len(pred_ids) * timestep
        })

    return results

import onnxruntime as ort
import librosa
import numpy as np

def load_phoneme_map():
    """
    For facebook/wav2vec2-base-960h-phoneme.
    If you're using another model, I can give you its map.
    """
    return [
        "<pad>", "AA", "AE", "AH", "AO", "AW", "AY",
        "B", "CH", "D", "DH", "EH", "ER", "EY", "F",
        "G", "HH", "IH", "IY", "JH", "K", "L", "M",
        "N", "NG", "OW", "OY", "P", "R", "S", "SH",
        "T", "TH", "UH", "UW", "V", "W", "Y", "Z", "ZH"
    ]

def clean_alignment(alignment, min_gap=0.05, min_duration=0.14, clamp=True):
    """
    Cleans MFA alignment by filling small gaps and merging too-short phonemes.
    
    Args:
        alignment (dict): MFA alignment dictionary with keys 'phonemes', 'starts', 'ends'.
        min_gap (float): gaps smaller than this are bridged (seconds)
        min_duration (float): phonemes shorter than this are merged (seconds)
    
    Returns:
        dict: cleaned alignment
    """
    phonemes = alignment['phonemes'][:]
    starts = alignment['starts'][:]
    ends = alignment['ends'][:]

    # Step 1: fill small gaps
    for i in range(len(starts) - 1):
        gap = starts[i+1] - ends[i]
        if 0 < gap < min_gap:
            ends[i] = starts[i+1]

    # Step 2: clamp very short phonemes
    if clamp:
        i = 0
        while i < len(starts):
            dur = ends[i] - starts[i]
            if dur < min_duration:
                if i > 0:
                    # merge into previous phoneme
                    ends[i-1] = ends[i]
                    del phonemes[i], starts[i], ends[i]
                    i -= 1  # stay on the same index after deletion
                elif i < len(starts) - 1:
                    # merge into next phoneme if first phoneme is too short
                    starts[i+1] = starts[i]
                    del phonemes[i], starts[i], ends[i]
                    i -= 1
            i += 1

    return {
        'phonemes': phonemes,
        'starts': starts,
        'ends': ends
    }

def wav2vec2_forced_align(audio_input, model_path="models/aligner/wav2vec2_960h.onnx"):
    # Determine if input is path or array

    if isinstance(audio_input, str):
        import librosa
        audio, sr = librosa.load(audio_input, sr=16000)
    else:
        audio = audio_input.astype(np.float32)
        sr = 16000  # assume already 16 kHz

    # Create ONNX session
    sess = ort.InferenceSession(
    model_path,
    providers=['CoreMLExecutionProvider', 'CPUExecutionProvider']
    )

    # ONNX model expects (batch, time)
    inp = audio[None, :].astype(np.float32)
    logits = sess.run(None, {"input_values": inp})[0][0]


    phoneme_map = load_phoneme_map()
    aligned = phoneme_timestamps(logits, phoneme_map)

    return aligned

#START MFA CORPUS ALIGNER

# import io
# import tempfile
# from pydub import AudioSegment
# from montreal_forced_aligner.corpus import Corpus
# from montreal_forced_aligner.models import AcousticModel
# from montreal_forced_aligner.aligner import BasicAligner
# import textgrid

# def align_tts_bytes(audio_bytes: bytes, transcript: str, model_name="english_us_arpa", silence_threshold_ms=30):
#     """
#     Align TTS audio (bytes) with transcript using MFA, return cleaned phoneme alignment.
    
#     :param audio_bytes: WAV audio bytes
#     :param transcript: Corresponding transcript text
#     :param model_name: MFA acoustic model name
#     :param silence_threshold_ms: Bridge silences shorter than this
#     :return: List of (start_time, end_time, phoneme) tuples
#     """
#     # 1️⃣ Load acoustic model
#     model_path = AcousticModel.download(model_name)
#     am = AcousticModel(model_path)

#     # 2️⃣ Save audio and transcript to temporary files
#     with tempfile.TemporaryDirectory() as tmpdir:
#         audio_path = f"{tmpdir}/audio.wav"
#         transcript_path = f"{tmpdir}/audio.txt"

#         # Load audio bytes with pydub and export as WAV
#         audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
#         audio.export(audio_path, format="wav")

#         # Write transcript
#         with open(transcript_path, "w", encoding="utf-8") as f:
#             f.write(transcript)

#         # 3️⃣ Create MFA corpus
#         corpus = Corpus(tmpdir, transcription_dir=tmpdir)
#         corpus.load()

#         # 4️⃣ Align
#         aligner = BasicAligner(corpus, am, tmpdir)
#         aligner.align()

#         # 5️⃣ Read aligned TextGrid
#         tg = textgrid.TextGrid()
#         tg.read(f"{tmpdir}/audio.TextGrid")
#         phoneme_tier = tg.getFirst("phones")

#         # 6️⃣ Postprocess: bridge very short silences
#         cleaned_intervals = []
#         prev_end = 0.0
#         for interval in phoneme_tier:
#             start, end, mark = interval.minTime, interval.maxTime, interval.mark
#             if mark.lower() in ["sil", "sp"] and (end - start) * 1000 < silence_threshold_ms:
#                 # merge tiny silences into previous phoneme
#                 if cleaned_intervals:
#                     cleaned_intervals[-1] = (
#                         cleaned_intervals[-1][0],
#                         end,
#                         cleaned_intervals[-1][2]
#                     )
#                 else:
#                     cleaned_intervals.append((start, end, mark))
#             else:
#                 cleaned_intervals.append((start, end, mark))
#             prev_end = end

#         return cleaned_intervals


# Example usage
# if __name__ == "__main__":
#     # audio_bytes = open("tts.wav", "rb").read()  # your TTS output bytes
#     audio_bytes = ...  # your in-memory WAV bytes
#     transcript = "Hello world, this is a test."

#     phoneme_alignment = align_tts_bytes(audio_bytes, transcript)
#     for start, end, phoneme in phoneme_alignment:
#         print(start, end, phoneme)
#END MFA CORPUS ALIGNER
