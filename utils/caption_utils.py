import re

import regex


# split caption
def split_caption(text, duration):
    # Use regular expressions to get a list of subtitles split by periods and other punctuation marks.
    segments = re.split(r'(?<=[。！？])(?![^“”]*”)\s*', text)
    # Remove empty segments
    segments = [seg for seg in segments if seg]
    # Calculate the number of Chinese and English characters in each paragraph (removing punctuation)
    cjk_and_english_counts = [len(regex.sub(r'[^\p{L}\p{Nd}\p{Han}]', '', seg)) for seg in segments]
    # Calculate the total number of Chinese and English characters
    total_cjk_and_english_count = sum(cjk_and_english_counts)
    # Allocate time based on the number of Chinese and English characters
    segment_durations = [round((count / total_cjk_and_english_count) * duration, 2) for count in
                         cjk_and_english_counts]
    # Return the split subtitles along with their corresponding durations
    return list(zip(segments, segment_durations))


# Subtitle line break
def add_newlines(text, max_length=38):
    result = []
    # Cumulative length of the current line
    current_length = 0
    # Last split position
    last_cut = 0

    # Regular expression to match non-word characters
    punctuation_pattern = r"\W"

    # Insert a possible newline character after each non-word character (i.e., punctuation)
    for i, char in enumerate(text):
        # The last non-word character before the cumulative length reaches max_length
        if re.match(punctuation_pattern, char) and current_length >= max_length:
            result.append(text[last_cut:i + 1] + '\n')
            last_cut = i + 1
            current_length = 0
        else:
            # If the cumulative length reaches max_length but no non-word character is encountered
            if current_length == max_length:
                result.append(text[last_cut:i] + '\n')
                last_cut = i
                current_length = 0
            # Cumulative length increases
            current_length += 1

    # Add the final segment of text
    if last_cut < len(text):
        result.append(text[last_cut:])
    return ''.join(result).strip()


def split_text_display(text, max_length=15):
    def word_cn_size(text):
        len = 0
        for c in text:
            len += get_char_size(c)
        return len

    def get_char_size(c):
        if ord(c) > 127:
            size = 1
        else:
            size = 0.5
        return size

    def split_lines(str, max_length):
        num = 0
        result = []
        for char in str:
            result.append(char)
            num += get_char_size(char)
            if num >= max_length:
                result.append('\n')
                num = 0
        return ''.join(result).strip('\n')

    length = word_cn_size(text)
    if length <= max_length:
        return text

    total_len = round(max_length * 2 / 3 + max_length)
    if length >= total_len:
        return split_lines(text, max_length)

    # Split into 2 lines (to address the issue of a significant length difference between the two lines),
    # with one line occupying 2/3 of the total length and the other 1/3.
    split_pos = int(length * 2 / 3)
    index = 0
    pos = 0
    for i, char in enumerate(text):
        index += get_char_size(char)
        if index >= split_pos:
            pos = i
            break
    return text[:pos] + '\n' + text[pos:]
