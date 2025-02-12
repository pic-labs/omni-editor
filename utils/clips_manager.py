import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def clean_clips():
    clips = []

    def add_2_clean(c):
        clips.append(c)
        return c

    try:
        yield add_2_clean
    finally:
        for clip in clips:
            try:
                clip.close()
            except Exception as e:
                logger.error("close clip failed, error: %s", e, exc_info=True)
