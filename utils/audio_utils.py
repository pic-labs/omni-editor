import numpy as np
from moviepy import concatenate_audioclips
from moviepy.audio.AudioClip import AudioArrayClip


# Extend the audio file by adding silence at the beginning/end
def extend_audio(audio_clip, duration=1, reverse=False):
    silent_audio = audio_clip.subclipped(0, duration).with_volume_scaled(0)

    if reverse:
        return concatenate_audioclips([silent_audio, audio_clip])
    else:
        return concatenate_audioclips([audio_clip, silent_audio])


def generate_silent_audio(duration, fps=44100, nchannels=2):
    samples_per_frame = int(fps * duration)
    audio_data = np.zeros((samples_per_frame, nchannels))
    silent_clip = AudioArrayClip(audio_data, fps=fps)
    return silent_clip
