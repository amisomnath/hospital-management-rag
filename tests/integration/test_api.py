"""Integration tests for REST hospital endpoints."""

from fastapi.testclient import TestClient


def test_health_and_hospital_creation_flow(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    assert client.get("/api/v1/health").status_code == 200

    department = client.post(
        "/api/v1/departments",
        headers=auth_headers,
        json={"name": "Cardiology", "description": "Heart care"},
    )
    assert department.status_code == 201

    patient = client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={
            "medical_record_number": "MRN-001",
            "full_name": "Ananya Sen",
        },
    )
    assert patient.status_code == 201

    doctor = client.post(
        "/api/v1/doctors",
        headers=auth_headers,
        json={
            "department_id": department.json()["id"],
            "full_name": "Dr. Rahul Bose",
            "specialization": "Cardiology",
            "license_number": "MED-001",
        },
    )
    assert doctor.status_code == 201


def test_hospital_routes_require_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/departments")
    assert response.status_code == 401


def test_public_registration_cannot_self_assign_admin(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "attacker@example.com",
            "full_name": "Not Admin",
            "password": "strong-password",
            "role": "admin",
        },
    )
    assert response.status_code == 422


def test_bulk_document_upload_rebuilds_once_and_skips_duplicates(
    client: TestClient, staff_auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/v1/documents/upload/bulk",
        headers=staff_auth_headers,
        files=[
            ("files", ("policy.md", b"Approved visiting policy.", "text/markdown")),
            (
                "files",
                (
                    "policy-copy.md",
                    b"Approved visiting policy.",
                    "text/markdown",
                ),
            ),
            (
                "files",
                ("medication.txt", b"Approved medication safety.", "text/plain"),
            ),
        ],
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["files_received"] == 3
    assert payload["documents_indexed"] == 2
    assert payload["duplicates_skipped"] == 1
    assert payload["chunks_created"] == 2
    assert payload["vectors_stored"] == 2
