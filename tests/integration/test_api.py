"""Integration tests for REST hospital endpoints."""

from fastapi.testclient import TestClient


def test_health_and_hospital_creation_flow(client: TestClient) -> None:
    assert client.get("/api/v1/health").status_code == 200

    department = client.post(
        "/api/v1/departments",
        json={"name": "Cardiology", "description": "Heart care"},
    )
    assert department.status_code == 201

    patient = client.post(
        "/api/v1/patients",
        json={
            "medical_record_number": "MRN-001",
            "full_name": "Ananya Sen",
        },
    )
    assert patient.status_code == 201

    doctor = client.post(
        "/api/v1/doctors",
        json={
            "department_id": department.json()["id"],
            "full_name": "Dr. Rahul Bose",
            "specialization": "Cardiology",
            "license_number": "MED-001",
        },
    )
    assert doctor.status_code == 201
