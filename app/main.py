from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Camera, CameraKind, NVR
from .schemas import CameraCreate, CameraRead, NVRCreate, NVRRead


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="NVR and Camera Metadata Service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/nvrs",
    response_model=NVRRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {
            "description": "An NVR with the supplied serial number already exists"
        },
    },
)
def create_nvr(payload: NVRCreate, db: Session = Depends(get_db)) -> NVR:
    serial = str(payload.serial_number)
    if db.get(NVR, serial):
        raise HTTPException(status_code=409, detail="NVR serial number already exists")

    nvr = NVR(
        serial_number=serial,
        make=payload.make,
        model=payload.model,
        maximum_input_channels=payload.maximum_input_channels,
    )
    db.add(nvr)
    db.commit()
    db.refresh(nvr)
    return nvr


@app.get("/nvrs", response_model=list[NVRRead])
def list_nvrs(db: Session = Depends(get_db)) -> list[NVR]:
    return list(db.scalars(select(NVR).order_by(NVR.make, NVR.model)))


@app.delete(
    "/nvrs/{nvr_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "NVR not found"},
    },
)
def delete_nvr(nvr_uuid: UUID, db: Session = Depends(get_db)) -> Response:
    nvr = db.get(NVR, str(nvr_uuid))
    if not nvr:
        raise HTTPException(status_code=404, detail="NVR not found")
    db.delete(nvr)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    "/cameras",
    response_model=CameraRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Referenced NVR does not exist"},
        409: {
            "description": (
                "Camera serial number already exists, or the NVR has "
                "reached its maximum input channel capacity"
            )
        },
    },
)
def create_camera(payload: CameraCreate, db: Session = Depends(get_db)) -> Camera:
    serial = str(payload.serial_number)
    nvr_uuid = str(payload.nvr_uuid)

    if db.get(Camera, serial):
        raise HTTPException(status_code=409, detail="Camera serial number already exists")

    nvr = db.get(NVR, nvr_uuid)
    if not nvr:
        raise HTTPException(status_code=400, detail="Referenced NVR does not exist")

    camera_count = db.scalar(select(func.count(Camera.serial_number)).where(Camera.nvr_uuid == nvr_uuid)) or 0
    if camera_count >= nvr.maximum_input_channels:
        raise HTTPException(status_code=409, detail="NVR has reached its maximum input channel capacity")

    camera = Camera(
        serial_number=serial,
        make=payload.make,
        model=payload.model,
        kind=payload.kind,
        location=payload.location,
        nvr_uuid=nvr_uuid,
    )
    db.add(camera)
    db.commit()
    db.refresh(camera)
    return camera


@app.delete(
    "/cameras/{camera_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Camera not found"},
    },
)
def delete_camera(camera_uuid: UUID, db: Session = Depends(get_db)) -> Response:
    camera = db.get(Camera, str(camera_uuid))
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    db.delete(camera)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get(
    "/nvrs/{nvr_uuid}/cameras",
    response_model=list[CameraRead],
    responses={
        404: {"description": "NVR not found"},
    },
)
def cameras_for_nvr(nvr_uuid: UUID, db: Session = Depends(get_db)) -> list[Camera]:
    if not db.get(NVR, str(nvr_uuid)):
        raise HTTPException(status_code=404, detail="NVR not found")
    stmt = select(Camera).where(Camera.nvr_uuid == str(nvr_uuid)).order_by(Camera.serial_number)
    return list(db.scalars(stmt))


@app.get("/cameras", response_model=list[CameraRead])
def find_cameras(
    location: str | None = Query(default=None, min_length=1),
    kind: CameraKind | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[Camera]:
    stmt = select(Camera)
    if location is not None:
        stmt = stmt.where(func.lower(Camera.location) == location.lower())
    if kind is not None:
        stmt = stmt.where(Camera.kind == kind)
    return list(db.scalars(stmt.order_by(Camera.serial_number)))