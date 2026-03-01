from pydantic import BaseModel
from typing import Optional
from enum import Enum


class JobStep(str, Enum):
    SCRAPING_PHOTO   = "SCRAPING_PHOTO"
    REMOVING_BG      = "REMOVING_BG"
    GENERATING_TRYON = "GENERATING_TRYON"
    GENERATING_VIDEO = "GENERATING_VIDEO"
    ASSEMBLING_VIDEO = "ASSEMBLING_VIDEO"


class FSMState(str, Enum):
    IDLE                = "IDLE"
    SCRAPING_PHOTO      = "SCRAPING_PHOTO"
    REMOVING_BG         = "REMOVING_BG"
    WAITING_APPROVAL    = "WAITING_APPROVAL"
    WAITING_PROMPT_EDIT = "WAITING_PROMPT_EDIT"
    GENERATING_TRYON    = "GENERATING_TRYON"
    GENERATING_VIDEO    = "GENERATING_VIDEO"
    ASSEMBLING_VIDEO    = "ASSEMBLING_VIDEO"
    DONE                = "DONE"


class Job(BaseModel):
    chat_id: int
    step: JobStep
    product_url: Optional[str] = None
    image_url: Optional[str] = None
    clean_image_b64: Optional[str] = None
    product_name: Optional[str] = None
    product_price: Optional[str] = None
    prompt: Optional[str] = None
    tryon_image_url: Optional[str] = None
    raw_video_url: Optional[str] = None
