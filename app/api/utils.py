import os
from pydantic import BaseModel, validator
from typing import List, Optional


def config_parser(config_path):
    with open(config_path, 'r') as config_file:
        config = dict()
        lines = config_file.readlines()
        for line in lines:
            k, v = line.split(' = ')
            config[k] = v.split('\n')[0]
        return config


def verify_path(file_path: str):
    return os.path.exists(file_path)


class BaseMedia(BaseModel):
    duration: int
    media_type: str

    @validator('duration')
    def duration_is_positive(cls, v):
        if v < 1:
            return ValueError('duration should be a positive number')
        return v

    @validator('media_type')
    def correct_media_type(cls, v):
        if v not in ('img', 'vid', 'gif'):
            return ValueError('media_type should be img or vid or gif')
        return v


class ScreenInfo(BaseMedia):
    url: str


class MediaInfo(BaseMedia):
    location: str

    @validator('location')
    def location_exists(cls, v):
2        if not os.path.exists(v):
            return ValueError('file does not exist')
        return v


class Playlist(BaseModel):
    __root__: List[MediaInfo]


class FinishedEvent(BaseModel):
    screen_number: int
