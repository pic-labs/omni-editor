from PIL import Image
from moviepy import ImageClip


# Extend video file, first frame, mute
def gen_video_with_img(img_path, extend_duration=1):
    img_clip = ImageClip(img_path).with_duration(extend_duration)
    img_clip = img_clip.without_audio()
    return img_clip


def img_resize(img_path, width, height):
    origin_img = Image.open(img_path)
    original_width, original_height = origin_img.size
    # The dimensions are the same, no need to resize.
    if original_width == width and original_height == height:
        return origin_img, origin_img.format

    if origin_img.mode in ('P', 'RGBA'):
        origin_img = origin_img.convert('RGB')

    # The aspect ratio is the same, resize directly.
    if original_width / original_height == (width / height):
        return origin_img.resize((width, height), resample=Image.LANCZOS), origin_img.format

    # The aspect ratio is different, crop first, then resize.
    if (original_width / original_height) > (width / height):
        new_height = original_height
        new_width = int(original_height * width / height)
    else:
        new_width = original_width
        new_height = int(original_width * height / width)
    # Determine the center point.
    x_center = original_width // 2
    y_center = original_height // 2

    # Calculate the cropping area.
    left = x_center - new_width // 2
    top = y_center - new_height // 2
    right = x_center + new_width // 2
    bottom = y_center + new_height // 2
    crop_img = origin_img.crop((left, top, right, bottom))
    return crop_img.resize((width, height), resample=Image.LANCZOS), origin_img.format
