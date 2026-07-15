from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.profile import Profile
from app.core.security import get_password_hash


class TestProfileEndpoints:
    """Test profile CRUD endpoints"""

    def test_get_profile_creates_if_not_exists(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test GET /profiles/me creates profile if it doesn't exist"""
        response = client.get("/api/v1/profiles/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(test_user.id)
        assert data["first_name"] is None
        assert "experiences" in data
        assert "educations" in data
        assert "skills" in data
        assert "projects" in data
        assert "certifications" in data

    def test_get_profile_returns_existing(
        self, client: TestClient, test_user: User, auth_headers: dict, db: Session
    ):
        """Test GET /profiles/me returns existing profile"""
        # Create a profile
        profile = Profile(
            user_id=test_user.id,
            first_name="John",
            last_name="Doe",
            headline="Software Engineer",
            email="john@example.com",
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

        response = client.get("/api/v1/profiles/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["headline"] == "Software Engineer"

    def test_update_profile_basic_fields(self, client: TestClient, auth_headers: dict):
        """Test PUT /profiles/me updates basic fields"""
        update_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "headline": "Senior Developer",
            "summary": "Experienced software engineer",
            "email": "jane@example.com",
            "phone": "+1234567890",
            "location": "San Francisco, CA",
            "website": "https://janesmith.com",
            "linkedin": "https://linkedin.com/in/janesmith",
            "github": "https://github.com/janesmith",
        }

        response = client.put(
            "/api/v1/profiles/me", json=update_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Smith"
        assert data["headline"] == "Senior Developer"
        assert data["summary"] == "Experienced software engineer"

    def test_update_profile_with_experiences(
        self, client: TestClient, auth_headers: dict
    ):
        """Test PUT /profiles/me with experiences array"""
        update_data = {
            "first_name": "John",
            "experiences": [
                {
                    "title": "Senior Engineer",
                    "company": "Tech Corp",
                    "location": "NYC",
                    "start_date": "2020-01-01",
                    "end_date": "2023-12-31",
                    "is_current": False,
                    "description": "Led development team",
                },
                {
                    "title": "Junior Engineer",
                    "company": "Startup Inc",
                    "location": "SF",
                    "start_date": "2018-06-01",
                    "is_current": False,
                    "description": "Full stack development",
                },
            ],
        }

        response = client.put(
            "/api/v1/profiles/me", json=update_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["experiences"]) == 2
        assert data["experiences"][0]["title"] == "Senior Engineer"
        assert data["experiences"][1]["company"] == "Startup Inc"

    def test_update_profile_replaces_nested_arrays(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that updating nested arrays replaces them completely"""
        # First update with 2 experiences
        update_data_1 = {
            "experiences": [
                {"title": "Job 1", "company": "Company 1", "is_current": False},
                {"title": "Job 2", "company": "Company 2", "is_current": False},
            ]
        }
        response = client.put(
            "/api/v1/profiles/me", json=update_data_1, headers=auth_headers
        )
        assert response.status_code == 200
        assert len(response.json()["experiences"]) == 2

        # Second update with 1 experience (should replace, not append)
        update_data_2 = {
            "experiences": [
                {"title": "Job 3", "company": "Company 3", "is_current": True}
            ]
        }
        response = client.put(
            "/api/v1/profiles/me", json=update_data_2, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["experiences"]) == 1
        assert data["experiences"][0]["title"] == "Job 3"

    def test_update_profile_with_all_sections(
        self, client: TestClient, auth_headers: dict
    ):
        """Test PUT /profiles/me with all nested sections"""
        update_data = {
            "first_name": "Alice",
            "last_name": "Johnson",
            "experiences": [
                {"title": "Developer", "company": "Tech Co", "is_current": True}
            ],
            "educations": [
                {
                    "institution": "MIT",
                    "degree": "BS",
                    "field_of_study": "Computer Science",
                }
            ],
            "skills": [
                {"name": "Python", "category": "Languages", "proficiency": "Expert"},
                {"name": "React", "category": "Frameworks", "proficiency": "Advanced"},
            ],
            "projects": [
                {
                    "name": "Portfolio Site",
                    "description": "Personal portfolio",
                    "url": "https://example.com",
                }
            ],
            "certifications": [
                {
                    "name": "AWS Certified",
                    "issuer": "Amazon",
                    "issue_date": "2023-01-01",
                }
            ],
        }

        response = client.put(
            "/api/v1/profiles/me", json=update_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Alice"
        assert len(data["experiences"]) == 1
        assert len(data["educations"]) == 1
        assert len(data["skills"]) == 2
        assert len(data["projects"]) == 1
        assert len(data["certifications"]) == 1

    def test_update_profile_validation_required_fields(
        self, client: TestClient, auth_headers: dict
    ):
        """Test validation for required fields in nested objects"""
        # Experience missing required 'company' field
        update_data = {
            "experiences": [
                {"title": "Developer"}  # Missing 'company'
            ]
        }

        response = client.put(
            "/api/v1/profiles/me", json=update_data, headers=auth_headers
        )

        # Should return 422 validation error
        assert response.status_code == 422

    def test_update_profile_validation_max_length(
        self, client: TestClient, auth_headers: dict
    ):
        """Test validation for max length constraints"""
        update_data = {
            "first_name": "A" * 300  # Exceeds 255 char limit
        }

        response = client.put(
            "/api/v1/profiles/me", json=update_data, headers=auth_headers
        )

        # Should return 422 validation error
        assert response.status_code == 422

    def test_unauthorized_access(self, client: TestClient):
        """Test that profile endpoints require authentication"""
        response = client.get("/api/v1/profiles/me")
        assert response.status_code == 401

        response = client.put("/api/v1/profiles/me", json={})
        assert response.status_code == 401

    def test_profile_isolation(self, client: TestClient, db: Session):
        """Test that users can only access their own profiles"""
        # Create two users
        user1 = User(
            email="user1@example.com",
            full_name="User One",
            hashed_password=get_password_hash("password123"),
            is_verified=True,
        )
        user2 = User(
            email="user2@example.com",
            full_name="User Two",
            hashed_password=get_password_hash("password123"),
            is_verified=True,
        )
        db.add_all([user1, user2])
        db.commit()

        # Create profile for user1
        profile1 = Profile(user_id=user1.id, first_name="User", last_name="One")
        db.add(profile1)
        db.commit()

        # Login as user2 and try to access profile
        from app.core.security import create_access_token

        token = create_access_token(str(user2.id))
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/v1/profiles/me", headers=headers)

        # Should create new profile for user2, not return user1's profile
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(user2.id)
        assert data["first_name"] is None  # New profile, not user1's

    def test_date_ordering(self, client: TestClient, auth_headers: dict):
        """Test that experiences are ordered by start_date descending"""
        update_data = {
            "experiences": [
                {
                    "title": "Old Job",
                    "company": "Company A",
                    "start_date": "2015-01-01",
                    "is_current": False,
                },
                {
                    "title": "Recent Job",
                    "company": "Company B",
                    "start_date": "2022-01-01",
                    "is_current": False,
                },
                {
                    "title": "Middle Job",
                    "company": "Company C",
                    "start_date": "2018-01-01",
                    "is_current": False,
                },
            ]
        }

        response = client.put(
            "/api/v1/profiles/me", json=update_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should be ordered: Recent, Middle, Old (descending by start_date)
        assert data["experiences"][0]["title"] == "Recent Job"
        assert data["experiences"][1]["title"] == "Middle Job"
        assert data["experiences"][2]["title"] == "Old Job"
