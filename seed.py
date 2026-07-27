import json
from pathlib import Path

from app.database import Base, SessionLocal, engine
from app.models import Camera, CameraKind, NVR


def main() -> None:
    Base.metadata.create_all(bind=engine)

    data = json.loads(
        Path("sample_nvr_camera_data.json").read_text(encoding="utf-8")
    )

    with SessionLocal() as db:
        for item in data["nvrs"]:
            if not db.get(NVR, item["serial_number"]):
                db.add(NVR(**item))
        db.commit()

        for item in data["cameras"]:
            if not db.get(Camera, item["serial_number"]):
                camera_data = item.copy()
                camera_data["kind"] = CameraKind(camera_data["kind"])
                db.add(Camera(**camera_data))
        db.commit()

    print("Sample data loaded.")


if __name__ == "__main__":
    main()