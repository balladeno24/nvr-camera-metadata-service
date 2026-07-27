from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .models import CameraKind


class NVRBase(BaseModel):
    make: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    maximum_input_channels: int = Field(gt=0)


class NVRCreate(NVRBase):
    serial_number: UUID


class NVRRead(NVRBase):
    model_config = ConfigDict(from_attributes=True)
    serial_number: UUID


class CameraBase(BaseModel):
    make: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=150)
    kind: CameraKind
    location: str = Field(min_length=1, max_length=200)
    nvr_uuid: UUID


class CameraCreate(CameraBase):
    serial_number: UUID


class CameraRead(CameraBase):
    model_config = ConfigDict(from_attributes=True)
    serial_number: UUID