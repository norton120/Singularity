from pydantic_settings import BaseSettings
from enum import Enum

class BlockSize(str, Enum):
    small = "small"
    medium = "medium"
    big = "big"


class Settings(BaseSettings):
    """Settings for the application"""
    start_time: str = "09:00"
    end_time: str = "17:00"
    small_block_size: int = 25
    medium_block_size: int = 50
    big_block_size: int = 80
    small_max_points: int = 4
    medium_max_points: int = 10
    big_max_points: int = 15
    small_break_size: int = 10
    medium_break_size: int = 17
    big_break_size: int = 17
    task_overlap: bool = True
    lunch: bool = True
    lunch_size: BlockSize = BlockSize.medium
    lunch_aprox_start: str = "12:00"
    imap_host: str
    imap_port: int
    imap_username: str
    imap_password: str
    slack_api_token: str
    slack_user_id: str
    calendar_email:str