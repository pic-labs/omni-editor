from moviepy import ImageClip, concatenate_videoclips


# Extend the video file, first frame, mute
def extend_video_with_first_frame(video_clip, extend_duration=1):
    first_frame = video_clip.get_frame(0)
    first_frame_clip = ImageClip(first_frame).with_duration(extend_duration)
    first_frame_clip = first_frame_clip.without_audio()
    clips = [first_frame_clip, video_clip]
    return concatenate_videoclips(clips, method="compose")
