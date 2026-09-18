"""
Sprint 2 Hardening Tests: Optimistic Concurrency, Taxonomy, Structured Errors,
Version Detail, and Canonical API Endpoints.
"""

import pytest

from app.models.user import User
from app.models.profile import Profile, Skill
from app.core.security import get_password_hash
from app.services.profile_versioning import (
    create_profile_version,
    get_profile_version_detail,
    get_profile_history,
    revert_to_version,
)
from app.services.skill_taxonomy import (
    normalize_skill_key,
    resolve_skill,
    canonicalize_profile_skills,
    seed_skill_taxonomy,
)
from app.services.profile_validation import (
    validate_profile,
    ProfileValidationError,
    _is_valid_url,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def seeded_db(db):
    """Seed the taxonomy and provide the db session."""
    seed_skill_taxonomy(db)
    return db


@pytest.fixture
def test_user2(db):
    u = User(
        email="sprint2_user@example.com",
        full_name="Sprint Two",
        hashed_password=get_password_hash("pass123"),
        is_verified=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def test_profile2(db, test_user2):
    p = Profile(
        user_id=test_user2.id,
        first_name="Sprint",
        last_name="Two",
        headline="Senior Dev",
        email="sprint2_user@example.com",
        revision=1,
    )
    db.add(p)
    db.flush()
    db.add(Skill(profile_id=p.id, name="Python", category="Languages"))
    db.commit()
    db.refresh(p)
    return p


# ---------------------------------------------------------------------------
# Taxonomy Tests
# ---------------------------------------------------------------------------


class TestSkillNormalization:
    def test_normalizes_whitespace(self):
        assert normalize_skill_key("  Python  ") == "python"

    def test_normalizes_case(self):
        assert normalize_skill_key("PYTHON") == "python"
        assert normalize_skill_key("Python") == "python"

    def test_normalizes_cpp(self):
        assert normalize_skill_key("C++") == "cpp"

    def test_normalizes_csharp(self):
        assert normalize_skill_key("C#") == "csharp"

    def test_normalizes_dotjs(self):
        assert normalize_skill_key("React.js") == "reactjs"

    def test_normalizes_dotnet(self):
        assert normalize_skill_key(".NET") == "dotnet"

    def test_empty_returns_empty(self):
        assert normalize_skill_key("") == ""


class TestTaxonomySeed:
    def test_seed_creates_entries(self, db):
        count = seed_skill_taxonomy(db)
        assert count > 0

    def test_seed_is_idempotent(self, db):
        count1 = seed_skill_taxonomy(db)
        assert count1 >= 0
        count2 = seed_skill_taxonomy(db)
        assert count2 == 0  # nothing new on re-seed

    def test_resolve_by_canonical_key(self, seeded_db):
        result = resolve_skill("python", seeded_db)
        assert result is not None
        assert result["canonical_key"] == "python"
        assert result["name"] == "Python"

    def test_resolve_by_alias(self, seeded_db):
        result = resolve_skill("K8s", seeded_db)
        assert result is not None
        assert result["canonical_key"] == "kubernetes"

    def test_resolve_case_insensitive(self, seeded_db):
        result = resolve_skill("JAVASCRIPT", seeded_db)
        assert result is not None
        assert result["canonical_key"] == "javascript"

    def test_resolve_js_alias(self, seeded_db):
        result = resolve_skill("JS", seeded_db)
        assert result is not None
        assert result["canonical_key"] == "javascript"

    def test_unknown_skill_returns_none(self, seeded_db):
        result = resolve_skill("ZerothQuantumFramework", seeded_db)
        assert result is None

    def test_canonicalize_deduplication(self, seeded_db):
        skills = [
            {"name": "Python"},
            {"name": "python"},
            {"name": "PYTHON"},
        ]
        result = canonicalize_profile_skills(skills, seeded_db)
        assert len(result) == 1
        assert result[0]["name"] == "Python"

    def test_canonicalize_preserves_unknown(self, seeded_db):
        skills = [{"name": "QuantumFoo"}]
        result = canonicalize_profile_skills(skills, seeded_db)
        assert len(result) == 1
        assert result[0]["name"] == "QuantumFoo"


# ---------------------------------------------------------------------------
# Structured Validation Errors
# ---------------------------------------------------------------------------


class TestStructuredValidationErrors:
    def test_error_is_string_compatible(self):
        err = ProfileValidationError(
            "Experience #1: title is required",
            code="REQUIRED_FIELD",
            path="experiences[0].title",
        )
        assert str(err) == "Experience #1: title is required"
        assert "Experience" in err

    def test_error_has_structured_dict(self):
        err = ProfileValidationError(
            "bad date", code="INVALID_DATE_RANGE", path="experiences[0].end_date"
        )
        d = err.to_dict()
        assert d["code"] == "INVALID_DATE_RANGE"
        assert d["path"] == "experiences[0].end_date"
        assert d["message"] == "bad date"

    def test_validate_profile_returns_error_objects(self):
        data = {
            "first_name": "",
            "last_name": "",
            "headline": "",
            "experiences": [{"title": "", "company": ""}],
        }
        errors = validate_profile(data)
        assert len(errors) > 0
        for e in errors:
            assert isinstance(e, ProfileValidationError)
            d = e.to_dict()
            assert "code" in d
            assert "path" in d
            assert "message" in d

    def test_url_validation_valid(self):
        assert _is_valid_url("https://github.com/user/repo")
        assert _is_valid_url("http://example.com/path")
        assert _is_valid_url("")  # empty is allowed
        assert _is_valid_url(None)  # None is allowed

    def test_url_validation_invalid(self):
        assert not _is_valid_url("not a url!!!")
        assert not _is_valid_url("ftp://")

    def test_invalid_project_url_is_caught(self):
        data = {
            "first_name": "Jane",
            "projects": [{"name": "MyProj", "url": "not_a_url!!"}],
        }
        errors = validate_profile(data)
        assert any(e.code == "INVALID_URL" for e in errors)

    def test_date_error_has_path(self):
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
        date_errors = [e for e in errors if e.code == "INVALID_DATE_RANGE"]
        assert len(date_errors) == 1
        assert "experiences[0]" in date_errors[0].path


# ---------------------------------------------------------------------------
# Optimistic Concurrency
# ---------------------------------------------------------------------------


class TestOptimisticConcurrency:
    def test_stale_revision_returns_409(self, client, auth_headers, test_user2):
        # First get profile (auto-creates it at revision=1)
        client.get("/api/v1/profiles/me", headers=auth_headers)

        # Send update with wrong expected_revision
        resp = client.put(
            "/api/v1/profiles/me",
            json={"first_name": "Updated", "headline": "New", "expected_revision": 999},
            headers=auth_headers,
        )
        assert resp.status_code == 409
        body = resp.json()
        assert body["detail"]["code"] == "REVISION_CONFLICT"

    def test_correct_revision_succeeds(self, client, auth_headers):
        # Get profile
        profile_resp = client.get("/api/v1/profiles/me", headers=auth_headers)
        current_revision = profile_resp.json().get("revision", 1)

        resp = client.put(
            "/api/v1/profiles/me",
            json={
                "first_name": "Good",
                "headline": "Test",
                "expected_revision": current_revision,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["revision"] == current_revision + 1

    def test_no_revision_check_when_omitted(self, client, auth_headers):
        client.get("/api/v1/profiles/me", headers=auth_headers)
        # Without expected_revision, no conflict check happens
        resp = client.put(
            "/api/v1/profiles/me",
            json={"first_name": "NoRevision", "headline": "Fine"},
            headers=auth_headers,
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Version History API
# ---------------------------------------------------------------------------


class TestVersionHistoryAPI:
    def test_get_versions_empty_before_any_update(self, client, auth_headers):
        client.get("/api/v1/profiles/me", headers=auth_headers)
        resp = client.get("/api/v1/profiles/me/versions", headers=auth_headers)
        assert resp.status_code == 200

    def test_update_creates_version(self, client, auth_headers):
        client.get("/api/v1/profiles/me", headers=auth_headers)
        client.put(
            "/api/v1/profiles/me",
            json={"first_name": "V1", "headline": "First"},
            headers=auth_headers,
        )
        resp = client.get("/api/v1/profiles/me/versions", headers=auth_headers)
        assert resp.status_code == 200
        versions = resp.json()
        assert len(versions) >= 1
        assert "version" in versions[0]
        assert "source" in versions[0]

    def test_get_version_detail(self, client, auth_headers):
        client.get("/api/v1/profiles/me", headers=auth_headers)
        client.put(
            "/api/v1/profiles/me",
            json={"first_name": "VersionDetail", "headline": "Test"},
            headers=auth_headers,
        )
        history = client.get(
            "/api/v1/profiles/me/versions", headers=auth_headers
        ).json()
        version_id = history[0]["id"]
        detail_resp = client.get(
            f"/api/v1/profiles/me/versions/{version_id}", headers=auth_headers
        )
        assert detail_resp.status_code == 200
        body = detail_resp.json()
        assert "profile" in body
        assert "schema_version" in body
        assert body["schema_version"] == 1

    def test_version_detail_404_not_found(self, client, auth_headers):
        import uuid

        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/profiles/me/versions/{fake_id}", headers=auth_headers
        )
        assert resp.status_code == 404

    def test_version_detail_isolation_other_user(self, client, db):
        """User A cannot access User B's version."""
        from app.core.security import get_password_hash, create_access_token

        # Create two users
        user_a = User(
            email="usera_sprint2@example.com",
            full_name="A",
            hashed_password=get_password_hash("pw"),
            is_verified=True,
        )
        user_b = User(
            email="userb_sprint2@example.com",
            full_name="B",
            hashed_password=get_password_hash("pw"),
            is_verified=True,
        )
        db.add_all([user_a, user_b])
        db.commit()
        db.refresh(user_a)
        db.refresh(user_b)

        headers_a = {"Authorization": f"Bearer {create_access_token(str(user_a.id))}"}
        headers_b = {"Authorization": f"Bearer {create_access_token(str(user_b.id))}"}

        # User A creates a version
        client.get("/api/v1/profiles/me", headers=headers_a)
        client.put(
            "/api/v1/profiles/me",
            json={"first_name": "Alice", "headline": "X"},
            headers=headers_a,
        )
        history_a = client.get("/api/v1/profiles/me/versions", headers=headers_a).json()
        assert len(history_a) >= 1
        version_id = history_a[0]["id"]

        # User B cannot access User A's version
        resp = client.get(
            f"/api/v1/profiles/me/versions/{version_id}", headers=headers_b
        )
        assert resp.status_code == 404


class TestVersionRevertAPI:
    def test_post_revert_creates_new_version(self, client, auth_headers):
        client.get("/api/v1/profiles/me", headers=auth_headers)
        # First PUT: snapshots empty state -> result has first_name="V1"
        client.put(
            "/api/v1/profiles/me",
            json={"first_name": "V1", "headline": "H1"},
            headers=auth_headers,
        )
        # Second PUT: snapshots "V1" state -> result has first_name="V2"
        client.put(
            "/api/v1/profiles/me",
            json={"first_name": "V2", "headline": "H2"},
            headers=auth_headers,
        )

        # The newest version in history (index 0) captured the "V1" state
        history = client.get(
            "/api/v1/profiles/me/versions", headers=auth_headers
        ).json()
        v1_snapshot_id = history[0][
            "id"
        ]  # newest snapshot = captured state before last PUT

        # Revert to the V1 snapshot via POST endpoint
        resp = client.post(
            f"/api/v1/profiles/me/versions/{v1_snapshot_id}/revert",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "V1"

        # A new revert version should appear in history
        history2 = client.get(
            "/api/v1/profiles/me/versions", headers=auth_headers
        ).json()
        revert_entry = next((h for h in history2 if h["source"] == "revert"), None)
        assert revert_entry is not None


# ---------------------------------------------------------------------------
# No-op Detection
# ---------------------------------------------------------------------------


class TestNoOpVersion:
    def test_identical_save_does_not_increment_version(
        self, db, test_user2, test_profile2
    ):
        # Create initial version
        v1 = create_profile_version(test_user2.id, test_profile2, db, source="update")
        db.commit()
        # Create same version again
        v2 = create_profile_version(test_user2.id, test_profile2, db, source="update")
        db.commit()
        assert v1.id == v2.id  # No new version created — same object returned

    def test_changed_profile_creates_new_version(self, db, test_user2, test_profile2):
        v1 = create_profile_version(test_user2.id, test_profile2, db, source="update")
        db.commit()

        test_profile2.headline = "Changed Headline"
        db.commit()

        v2 = create_profile_version(test_user2.id, test_profile2, db, source="update")
        db.commit()
        assert v1.id != v2.id
        assert v2.version == 2


# ---------------------------------------------------------------------------
# Version Detail Service
# ---------------------------------------------------------------------------


class TestVersionDetailService:
    def test_get_version_detail_returns_schema_version(
        self, db, test_user2, test_profile2
    ):
        v = create_profile_version(test_user2.id, test_profile2, db, source="baseline")
        db.commit()
        detail = get_profile_version_detail(test_user2.id, v.id, db)
        assert detail["schema_version"] == 1
        assert "profile" in detail
        assert detail["profile"]["first_name"] == "Sprint"
        assert detail["source"] == "baseline"

    def test_revert_creates_revert_source_version(self, db, test_user2, test_profile2):
        v1 = create_profile_version(test_user2.id, test_profile2, db, source="update")
        db.commit()

        test_profile2.headline = "Changed"
        db.commit()

        revert_to_version(test_user2.id, v1.id, db)
        db.commit()

        history = get_profile_history(test_user2.id, db)
        revert_entry = next((h for h in history if h["source"] == "revert"), None)
        assert revert_entry is not None

    def test_version_detail_not_found_raises(self, db, test_user2):
        import uuid

        with pytest.raises(ValueError, match="not found"):
            get_profile_version_detail(test_user2.id, uuid.uuid4(), db)
