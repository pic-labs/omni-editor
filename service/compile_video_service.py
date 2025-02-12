import logging
from typing import List, Dict, Optional

from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, afx, \
    CompositeAudioClip, concatenate_audioclips
from pydantic import BaseModel

from config.common_config import FILE_DIR, CAPTION_FONT
from utils.audio_utils import extend_audio, generate_silent_audio
from utils.caption_utils import split_caption, add_newlines, split_text_display
from utils.clips_manager import clean_clips
from utils.file_downloader import download
from utils.img_utils import gen_video_with_img
from utils.video_utils import extend_video_with_first_frame

logger = logging.getLogger(__name__)


class CaptionItem(BaseModel):
    text: str
    startTime: int
    endTime: int

    class Config:
        extra = "allow"


class Caption(BaseModel):
    type: int
    items: List[CaptionItem]

    class Config:
        extra = "allow"


class Shot(BaseModel):
    caption: Optional[str] = None
    captions: Optional[Caption] = None
    audio: Optional[str] = None
    img: Optional[str] = None
    video: Optional[str] = None


class CompileVideoParam(BaseModel):
    bgm: str
    shots: List[Shot]


class ShotMaterial(BaseModel):
    audio: str = None
    img: str = None
    video: str = None


class CompileVideoMaterial(BaseModel):
    bgm: str = None
    shot: Dict[int, ShotMaterial] = {}


class CompileVideoService:
    @staticmethod
    def compile_video(task_id: str, param: CompileVideoParam) -> dict:
        if not param.shots:
            return {}
        try:
            material = CompileVideoService.download_materials(param, task_id)
            video_name = CompileVideoService.compile_video_with_material(param, task_id, material)
            logger.info("compile_video success, task_id: %s, video: %s", task_id, video_name)
            return {"video": video_name}
        except Exception as e:
            logger.error("compile_video fail, param: %s, error: %s", param, e, exc_info=True)
            raise e

    @staticmethod
    def compile_shot_videos(clip_cleaner, param, material):
        video_clips = []
        for index, shot in enumerate(param.shots):
            # process video
            video_clip = CompileVideoService.get_shot_video_clip(clip_cleaner, index, shot, material)
            # assemble video
            video_clip = CompileVideoService.assemble_shot_audio(clip_cleaner, index, material, shot, video_clip)
            # assemble caption
            if shot.captions:
                video_clip = CompileVideoService.assemble_caption_v2(clip_cleaner, video_clip, shot.captions)
            else:
                video_clip = CompileVideoService.assemble_caption(clip_cleaner, video_clip, shot.caption)
            video_clips.append(video_clip)
        return video_clips

    @staticmethod
    def get_shot_video_clip(clip_cleaner, index, shot, material):
        # If the video does not exist, convert the image to video.
        if not shot.video:
            audio_clip = clip_cleaner(AudioFileClip(material.shot[index].audio))
            video_clip = clip_cleaner(gen_video_with_img(material.shot[index].img, audio_clip.duration))
        else:
            video_clip = clip_cleaner(VideoFileClip(material.shot[index].video))

        # If the audio is longer than the video, extend the first frame of the video.
        if shot.audio and shot.video:
            audio_clip = clip_cleaner(AudioFileClip(material.shot[index].audio))
            if audio_clip.duration > video_clip.duration:
                extend_duration = audio_clip.duration - video_clip.duration
                video_clip = clip_cleaner(extend_video_with_first_frame(video_clip, extend_duration))

        # If it is the opening, add 1 second.
        if index == 0:
            extend_duration = 1
            video_clip = clip_cleaner(extend_video_with_first_frame(video_clip, extend_duration))
        return video_clip

    @staticmethod
    def compile_video_with_material(param, task_id, material) -> str:
        with clean_clips() as clip_cleaner:
            shot_video_clips = CompileVideoService.compile_shot_videos(clip_cleaner, param, material)
            mix_shots_video = clip_cleaner(concatenate_videoclips(shot_video_clips))
            mix_bgm_video = CompileVideoService.assemble_bmg(clip_cleaner, mix_shots_video, material.bgm)
            video_name = CompileVideoService.write_video_file(task_id, mix_bgm_video)
            return video_name

    @staticmethod
    def write_video_file(task_id, video) -> str:
        video_name = task_id + ".mp4"
        video_path = FILE_DIR + video_name
        video.write_videofile(video_path, fps=16, codec="libx264", audio_codec="aac")
        return video_name

    @staticmethod
    def assemble_bmg(clip_cleaner, video, bgm):
        bgm_clip = clip_cleaner(AudioFileClip(bgm))
        bgm_clip = clip_cleaner(bgm_clip.with_volume_scaled(0.2))
        if bgm_clip.duration >= video.duration:
            bgm_clip = clip_cleaner(bgm_clip.with_duration(video.duration))
        else:
            bgm_clip = clip_cleaner(bgm_clip.fx(afx.audio_loop, duration=video.duration))
        mix_bgm_audio = clip_cleaner(CompositeAudioClip([bgm_clip, video.audio]))
        mix_bgm_video = clip_cleaner(video.with_audio(mix_bgm_audio))
        return mix_bgm_video

    @staticmethod
    def assemble_shot_audio(clip_cleaner, index, material, shot, video_clip):
        if not shot.audio:
            return video_clip
        audio_clip = clip_cleaner(AudioFileClip(material.shot[index].audio))
        # If the original video is longer than the original audio, extend the audio at both the beginning and the end.
        if shot.video:
            origin_video_clip = clip_cleaner(VideoFileClip(material.shot[index].video))
            if origin_video_clip.duration > audio_clip.duration:
                extend_duration = (origin_video_clip.duration - audio_clip.duration) / 2
                audio_clip = clip_cleaner(extend_audio(audio_clip, extend_duration, True))
                audio_clip = clip_cleaner(extend_audio(audio_clip, extend_duration))
        # If it is the opening, add 1 second.
        if index == 0:
            extend_duration = 1
            silence_audio = clip_cleaner(generate_silent_audio(extend_duration, audio_clip.fps, audio_clip.nchannels))
            clips = [silence_audio, audio_clip]
            audio_clip = clip_cleaner(concatenate_audioclips(clips))
        video_clip = clip_cleaner(video_clip.with_audio(audio_clip))
        return video_clip

    @staticmethod
    def assemble_caption(clip_cleaner, video_clip, caption):
        captions_seg_clips = []
        captions_seg = split_caption(caption, video_clip.duration)
        width, height = video_clip.size
        seg_start = 0

        for seg_index, (seg, seg_duration) in enumerate(captions_seg):
            if height > width:
                seg = add_newlines(seg, max_length=15)
                captions_clip = clip_cleaner(TextClip(font=CAPTION_FONT, text=seg, font_size=40,
                                                      text_align='center', color='white', stroke_color='black',
                                                      method='caption', stroke_width=1, size=(width, None)))
                captions_width, captions_height = captions_clip.size
                # For vertical video caption: position them halfway between the center of the screen and their
                # current position (captions_height + 280 from the bottom).
                captions_pos = (
                    (width - captions_width) / 2, height - height / 2 + (height / 2 - captions_height - 280) / 2)
            else:
                seg = add_newlines(seg, max_length=38)
                captions_clip = clip_cleaner(TextClip(font=CAPTION_FONT, text=seg, font_size=40,
                                                      text_align='center', color='white', stroke_color='black',
                                                      method='caption', stroke_width=1, size=(width, None)))
                captions_width, captions_height = captions_clip.size
                # For horizontal video caption: position them 70 units from the bottom.
                captions_pos = ((width - captions_width) / 2, height - captions_height - 70)
            captions_clip = clip_cleaner(captions_clip.with_position(captions_pos))
            captions_clip = clip_cleaner(captions_clip.with_start(seg_start))
            captions_clip = clip_cleaner(captions_clip.with_duration(seg_duration))
            captions_seg_clips.append(captions_clip)

            seg_start += seg_duration
        video_clip = clip_cleaner(CompositeVideoClip([video_clip, *captions_seg_clips]))
        return video_clip

    @staticmethod
    def assemble_caption_v2(clip_cleaner, video_clip, captions):
        captions_seg_clips = []
        captions_segs = captions.items
        width, height = video_clip.size
        # For the opening, add 1 second of silence, evenly distributed before and after.
        start_head = 0.5
        for item in captions_segs:
            start = item.startTime / 1000 + start_head
            end = item.endTime / 1000 + start_head
            if end > video_clip.duration:
                end = video_clip.duration
            time_s = end - start

            if height > width:
                item.text = split_text_display(item.text, max_length=15)
                captions_clip = clip_cleaner(TextClip(font=CAPTION_FONT, text=item.text, font_size=40,
                                                      color='white', stroke_color='black', size=(width, None),
                                                      method='caption', text_align='center',
                                                      stroke_width=1))
                captions_width, captions_height = captions_clip.size
                # For vertical video caption: position them halfway between the center of the screen and their
                # current position (captions_height + 280 from the bottom).
                captions_pos = (
                    (width - captions_width) / 2, height - height / 2 + (height / 2 - captions_height - 280) / 2)
            else:
                item.text = split_text_display(item.text, max_length=38)
                captions_clip = clip_cleaner(TextClip(font=CAPTION_FONT, text=item.text, font_size=40,
                                                      color='white', stroke_color='black', size=(width, None),
                                                      method='caption', text_align='center',
                                                      stroke_width=1))
                captions_width, captions_height = captions_clip.size
                # For horizontal video caption: position them 70 units from the bottom.
                captions_pos = ((width - captions_width) / 2, height - captions_height - 70)
            captions_clip = clip_cleaner(captions_clip.with_position(captions_pos))
            captions_clip = clip_cleaner(captions_clip.with_start(start))
            captions_clip = clip_cleaner(captions_clip.with_duration(time_s))
            captions_seg_clips.append(captions_clip)

        video_clip = clip_cleaner(CompositeVideoClip([video_clip, *captions_seg_clips]))
        return video_clip

    @staticmethod
    def download_materials(param: CompileVideoParam, task_id: str) -> CompileVideoMaterial:
        p = CompileVideoMaterial()
        p.bgm = download(param.bgm, task_id)
        # Loop through param.shots, supplementing audio and video.
        for index, shot in enumerate(param.shots):
            sp = ShotMaterial()
            if shot.audio and len(shot.audio) > 0:
                sp.audio = download(shot.audio, task_id)
            if shot.img and len(shot.img) > 0:
                sp.img = download(shot.img, task_id)
            if shot.video and len(shot.video) > 0:
                sp.video = download(shot.video, task_id)
            p.shot[index] = sp
        return p
