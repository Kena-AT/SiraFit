"""Tests for Sprint 2: Profile & Skills Full Rewrite

Tests profile validation, versioning, history, and revert functionality.
"""

import pytest
from datetime import date
from app.services.profile_validation import (
    validate_profile,
)
from app.services.profile_versioning import (
    create_profile_version,
    get_profile_history,
    revert_to_version,
    _profile_to_dict,
)
from app.models.profile import Profile, Experience, Skill
from app.models.user import User
from app.core.security import get_password_hash


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def test_user(db):
    """Create a test user for profile tests."""
    user = User(
        email="profile_test@example.com",
        full_name="Profile Test User",
        hashed_password=get_password_hash("password123"),
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_profile(db, test_user):
    """Create a profile with sample data."""
    profile = Profile(
        user_id=test_user.id,
        first_name="Jane",
        last_name="Doe",
        headline="Senior Engineer",
        email="jane@example.com",
    )
    db.add(profile)
    db.flush()

    db.add(
        Experience(
            profile_id=profile.id,
            title="Software Engineer",
            company="Acme Corp",
            start_date=date(2020, 1, 1),
            end_date=date(2023, 12, 31),
            description="Built things",
        )
    )
    db.add(Skill(profile_id=profile.id, name="Python", category="Languages"))
    db.add(Skill(profile_id=profile.id, name="React", category="Frameworks"))
    db.commit()
    db.refresh(profile)
    return profile


# ---------------------------------------------------------------------------
# Validation Tests
# ---------------------------------------------------------------------------


class TestProfileValidation:
    def test_valid_profile_passes(self):
        data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "headline": "Engineer",
            "experiences": [
                {
                    "title": "Dev",
                    "company": "Acme",
                    "start_date": "2020-01-01",
                    "end_date": "2023-12-31",
                }
            ],
            "skills": [{"name": "Python"}],
        }
        errors = validate_profile(data)
        assert errors == []

    def test_empty_profile_fails(self):
        data = {"first_name": "", "last_name": "", "headline": ""}
        errors = validate_profile(data)
        assert len(errors) > 0
        assert "required" in errors[0].lower()

    def test_experience_missing_title(self):
        data = {
            "first_name": "Jane",
            "experiences": [{"title": "", "company": "Acme"}],
        }
        errors = validate_profile(data)
        assert any("title" in e.lower() for e in errors)

    def test_experience_missing_company(self):
        data = {
            "first_name": "Jane",
            "experiences": [{"title": "Dev", "company": ""}],
        }
        errors = validate_profile(data)
        assert any("company" in e.lower() for e in errors)

    def test_experience_end_before_start(self):
        data = {
            "first_name": "Jane",
            "experiences": [
                {
                    "title": "Dev",
                    "company": "Acme",
                    "start_date": "2023-01-01",
                    "end_date": "2020-01-01",
                }
            ],
        }
        errors = validate_profile(data)
        assert any("end date" in e.lower() and "precedes" in e.lower() for e in errors)

    def test_current_role_with_end_date(self):
        data = {
            "first_name": "Jane",
            "experiences": [
                {
                    "title": "Dev",
                    "company": "Acme",
                    "start_date": "2020-01-01",
                    "end_date": "2023-12-31",
                    "is_current": True,
                }
            ],
        }
        errors = validate_profile(data)
        assert any("current" in e.lower() for e in errors)

    def test_education_missing_institution(self):
        data = {
            "first_name": "Jane",
            "educations": [{"institution": "", "degree": "BS"}],
        }
        errors = validate_profile(data)
        assert any("institution" in e.lower() for e in errors)

    def test_education_end_before_start(self):
        data = {
            "first_name": "Jane",
            "educations": [
                {
                    "institution": "MIT",
                    "start_date": "2020-01-01",
                    "end_date": "2018-01-01",
                }
            ],
        }
        errors = validate_profile(data)
        assert any("end date" in e.lower() for e in errors)

    def test_project_missing_name(self):
        data = {
            "first_name": "Jane",
            "projects": [{"name": ""}],
        }
        errors = validate_profile(data)
        assert any("name" in e.lower() for e in errors)

    def test_project_end_before_start(self):
        data = {
            "first_name": "Jane",
            "projects": [
                {
                    "name": "My Project",
                    "start_date": "2023-01-01",
                    "end_date": "2020-01-01",
                }
            ],
        }
        errors = validate_profile(data)
        assert any("end date" in e.lower() for e in errors)

    def test_skill_missing_name(self):
        data = {
            "first_name": "Jane",
            "skills": [{"name": ""}],
        }
        errors = validate_profile(data)
        assert any("name" in e.lower() for e in errors)

    def test_certification_missing_fields(self):
        data = {
            "first_name": "Jane",
            "certifications": [{"name": "", "issuer": ""}],
        }
        errors = validate_profile(data)
        assert len(errors) >= 2  # both name and issuer

    def test_multiple_errors_collected(self):
        data = {
            "experiences": [{"title": "", "company": ""}],
            "educations": [{"institution": ""}],
            "skills": [{"name": ""}],
        }
        errors = validate_profile(data)
        assert len(errors) >= 4  # required field + missing nested fields


# ---------------------------------------------------------------------------
# Versioning Tests
# ---------------------------------------------------------------------------


class TestProfileVersioning:
    def test_create_first_version(self, db, test_user, test_profile):
        version = create_profile_version(test_user.id, test_profile, db)
        assert version.version == 1
        assert version.user_id == test_user.id
        # Data is stored in schema-versioned envelope
        data = version.data
        assert data["schema_version"] == 1
        profile_data = data["profile"]
        assert profile_data["first_name"] == "Jane"
        assert profile_data["last_name"] == "Doe"
        assert len(profile_data["experiences"]) == 1
        assert len(profile_data["skills"]) == 2

    def test_create_subsequent_versions(self, db, test_user, test_profile):
        v1 = create_profile_version(test_user.id, test_profile, db)
        assert v1.version == 1
        db.commit()
        # Mutate profile so it's not a no-op snapshot
        test_profile.headline = "Updated Headline"
        db.commit()
        v2 = create_profile_version(test_user.id, test_profile, db)
        db.commit()
        assert v2.version == 2

    def test_get_profile_history(self, db, test_user, test_profile):
        create_profile_version(test_user.id, test_profile, db)
        db.commit()
        # Mutate so second create_profile_version is not a no-op
        test_profile.headline = "Version Two"
        db.commit()
        create_profile_version(test_user.id, test_profile, db)
        db.commit()

        history = get_profile_history(test_user.id, db)
        assert len(history) == 2
        assert history[0]["version"] == 2  # newest first
        assert history[1]["version"] == 1
        assert "Jane" in history[0]["summary"]

    def test_profile_to_dict_serializes_dates(self, db, test_profile):
        data = _profile_to_dict(test_profile)
        assert data["experiences"][0]["start_date"] == "2020-01-01"
        assert data["experiences"][0]["end_date"] == "2023-12-31"

    def test_revert_to_version(self, db, test_user, test_profile):
        # Create version with original data
        v1 = create_profile_version(test_user.id, test_profile, db)
        db.commit()

        # Modify profile
        test_profile.first_name = "John"
        db.commit()

        # Revert
        revert_to_version(test_user.id, v1.id, db)
        db.commit()
        db.refresh(test_profile)

        assert test_profile.first_name == "Jane"

    def test_revert_creates_backup_version(self, db, test_user, test_profile):
        # Create v1
        v1 = create_profile_version(test_user.id, test_profile, db)
        db.commit()

        # Modify profile
        test_profile.first_name = "John"
        db.commit()

        # Revert to v1
        revert_to_version(test_user.id, v1.id, db)
        db.commit()

        # Should have 2 versions: v1 + the auto-created backup
        history = get_profile_history(test_user.id, db)
        assert len(history) == 2

    def test_revert_nonexistent_version_raises(self, db, test_user):
        import uuid

        with pytest.raises(ValueError, match="not found"):
            revert_to_version(test_user.id, uuid.uuid4(), db)

    def test_version_retention_policy(self, db, test_user, test_profile):
        """Test that old versions are pruned beyond MAX_VERSIONS."""
        from app.services.profile_versioning import MAX_VERSIONS

        # Create more versions than the retention limit
        for _ in range(MAX_VERSIONS + 5):
            create_profile_version(test_user.id, test_profile, db)
            db.commit()

        history = get_profile_history(test_user.id, db, limit=MAX_VERSIONS + 10)
        assert len(history) <= MAX_VERSIONS


# ---------------------------------------------------------------------------
# API Integration Tests
# ---------------------------------------------------------------------------


class TestProfileAPI:
    def test_get_profile_creates_default(self, client, auth_headers):
        response = client.get("/api/v1/profiles/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "first_name" in data

    def test_update_profile_with_validation(self, client, auth_headers):
        # First get the profile
        resp = client.get("/api/v1/profiles/me", headers=auth_headers)
        assert resp.status_code == 200

        # Update with valid data
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "headline": "Updated Headline",
            "experiences": [],
            "skills": [],
        }
        response = client.put(
            "/api/v1/profiles/me",
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["first_name"] == "Updated"

    def test_update_profile_validation_error(self, client, auth_headers):
        # Get profile first
        client.get("/api/v1/profiles/me", headers=auth_headers)

        # Try to update with invalid data (empty experience)
        update_data = {
            "first_name": "",
            "last_name": "",
            "headline": "",
            "experiences": [{"title": "", "company": ""}],
        }
        response = client.put(
            "/api/v1/profiles/me",
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_get_profile_history(self, client, auth_headers):
        # Create profile first
        client.get("/api/v1/profiles/me", headers=auth_headers)

        # Update to create a version
        client.put(
            "/api/v1/profiles/me",
            json={"first_name": "Versioned", "headline": "Test"},
            headers=auth_headers,
        )

        response = client.get("/api/v1/profiles/me/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert "version" in data[0]

    def test_revert_profile(self, client, auth_headers):
        # Create profile (auto-created, first_name derived from user's full_name)
        get_resp = client.get("/api/v1/profiles/me", headers=auth_headers)
        auto_first_name = get_resp.json()["first_name"]

        # Update to create a version — version stores the OLD state
        client.put(
            "/api/v1/profiles/me",
            json={"first_name": "Original", "headline": "Test"},
            headers=auth_headers,
        )

        # Get history to find the version
        history_resp = client.get("/api/v1/profiles/me/history", headers=auth_headers)
        versions = history_resp.json()
        assert len(versions) >= 1

        # Revert to first version (which has the auto-created state)
        v1_id = versions[-1]["id"]  # oldest version
        revert_resp = client.put(
            f"/api/v1/profiles/me/revert/{v1_id}",
            headers=auth_headers,
        )
        assert revert_resp.status_code == 200
        # The oldest version has the auto-created state
        assert revert_resp.json()["first_name"] == auto_first_name
