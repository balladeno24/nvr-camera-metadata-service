import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_nvr_camera.db"

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app

DB_FILE = Path("test_nvr_camera.db")
client = TestClient(app)

NVR = {
    "make": "Hanwha Vision",
    "model": "QRN-1610S",
    "maximum_input_channels": 1,
    "serial_number": "a3f5e8d1-2c4b-4a9e-8f3d-1b5c7e9f2a4d",
}
CAMERA = {
    "make": "Hikvision",
    "model": "DS-2CD2T83G2-4I",
    "kind": "electro-optical",
    "serial_number": "d5a8c2e1-3f7b-4d9e-8a1c-5b3f7e9d2a4c",
    "location": "Building A",
    "nvr_uuid": NVR["serial_number"],
}


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module():
    engine.dispose()
    if DB_FILE.exists():
        DB_FILE.unlink()


def test_create_and_query_camera():
    nvr_response = client.post("/nvrs", json=NVR)
    assert nvr_response.status_code == 201
    assert nvr_response.json()["serial_number"] == NVR["serial_number"]

    camera_response = client.post("/cameras", json=CAMERA)
    assert camera_response.status_code == 201
    assert camera_response.json()["serial_number"] == CAMERA["serial_number"]

    by_nvr = client.get(f"/nvrs/{NVR['serial_number']}/cameras")
    assert by_nvr.status_code == 200
    assert len(by_nvr.json()) == 1
    assert by_nvr.json()[0]["serial_number"] == CAMERA["serial_number"]

    by_location = client.get(
        "/cameras",
        params={"location": "building a"},
    )
    assert by_location.status_code == 200
    assert len(by_location.json()) == 1
    assert by_location.json()[0]["serial_number"] == CAMERA["serial_number"]

    by_kind = client.get(
        "/cameras",
        params={"kind": "electro-optical"},
    )
    assert by_kind.status_code == 200
    assert len(by_kind.json()) == 1
    assert by_kind.json()[0]["kind"] == "electro-optical"

def test_duplicate_nvr_is_rejected():
    first_response = client.post("/nvrs", json=NVR)
    assert first_response.status_code == 201

    duplicate_response = client.post("/nvrs", json=NVR)
    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "detail": "NVR serial number already exists"
    }


def test_duplicate_camera_is_rejected():
    assert client.post("/nvrs", json=NVR).status_code == 201
    assert client.post("/cameras", json=CAMERA).status_code == 201

    duplicate_response = client.post("/cameras", json=CAMERA)
    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "detail": "Camera serial number already exists"
    }


def test_camera_with_missing_nvr_is_rejected():
    camera = CAMERA | {
        "serial_number": "22222222-2222-4222-8222-222222222222",
        "nvr_uuid": "33333333-3333-4333-8333-333333333333",
    }

    response = client.post("/cameras", json=camera)

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Referenced NVR does not exist"
    }


def test_delete_missing_camera_returns_404():
    response = client.delete(
        "/cameras/44444444-4444-4444-8444-444444444444"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Camera not found"
    }


def test_delete_missing_nvr_returns_404():
    response = client.delete(
        "/nvrs/55555555-5555-4555-8555-555555555555"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "NVR not found"
    }


def test_invalid_camera_uuid_returns_422():
    response = client.delete("/cameras/not-a-valid-uuid")

    assert response.status_code == 422


def test_combined_camera_filters():
    assert client.post("/nvrs", json=NVR).status_code == 201
    assert client.post("/cameras", json=CAMERA).status_code == 201

    matching_response = client.get(
        "/cameras",
        params={
            "location": "BUILDING A",
            "kind": "electro-optical",
        },
    )
    assert matching_response.status_code == 200
    assert len(matching_response.json()) == 1
    assert matching_response.json()[0]["serial_number"] == CAMERA["serial_number"]

    non_matching_response = client.get(
        "/cameras",
        params={
            "location": "Building A",
            "kind": "thermal",
        },
    )
    assert non_matching_response.status_code == 200
    assert non_matching_response.json() == []

def test_channel_capacity_is_enforced():
    client.post("/nvrs", json=NVR)
    client.post("/cameras", json=CAMERA)
    second = CAMERA | {"serial_number": "11111111-1111-4111-8111-111111111111"}
    response = client.post("/cameras", json=second)
    assert response.status_code == 409


def test_delete_nvr_cascades_to_cameras():
    client.post("/nvrs", json=NVR)
    client.post("/cameras", json=CAMERA)
    assert client.delete(f"/nvrs/{NVR['serial_number']}").status_code == 204
    assert client.get("/cameras").json() == []