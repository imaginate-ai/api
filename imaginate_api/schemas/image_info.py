from dataclasses import dataclass
from enum import Enum
from typing import Optional

from marshmallow import fields


class ImageStatus(Enum):
  UNVERIFIED = "unverified"
  VERIFIED = "verified"
  REJECTED = "rejected"


@dataclass(frozen=True)
class ImageInfo:
  filename: str
  date: str
  theme: str
  real: bool
  status: Optional[str] = ImageStatus.UNVERIFIED


class ImageInfoSchema:
  OBJ_CLS = ImageInfo

  filename = fields.Str(required=True)
  date = fields.Str(required=True)
  theme = fields.Str(required=True)
  real = fields.Bool(required=True)
  status = fields.Str(required=False, load_default=ImageStatus.UNVERIFIED)


IMAGE_INFO_SCHEMA = ImageInfoSchema()
