from fastapi.testclient import TestClient

def test_get_my_profile_empty(client: TestClient, auth_tokens):
    """If a profile doesn't exist, GET /me should create and return an empty one."""
    resp = client.get(
        "/api/v1/profiles/me",
        headers={"Authorization": f"Bearer {auth_tokens['access_token']}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert data["first_name"] is None
    assert data["experiences"] == []

def test_update_my_profile(client: TestClient, auth_tokens):
    """Test monolithic update of profile and nested entities."""
    update_payload = {
        "first_name": "John",
        "last_name": "Doe",
        "headline": "Software Engineer",
        "experiences": [
            {
                "title": "Backend Dev",
                "company": "Tech Corp",
                "is_current": True
            }
        ],
        "skills": [
            {
                "name": "Python",
                "proficiency": "Expert"
            }
        ]
    }

    resp = client.put(
        "/api/v1/profiles/me",
        headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        json=update_payload
    )
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["first_name"] == "John"
    assert data["headline"] == "Software Engineer"
    assert len(data["experiences"]) == 1
    assert data["experiences"][0]["company"] == "Tech Corp"
    assert len(data["skills"]) == 1
    assert data["skills"][0]["name"] == "Python"

def test_update_my_profile_replace_lists(client: TestClient, auth_tokens):
    """Test that updating nested lists replaces them entirely."""
    # Add an initial experience
    client.put(
        "/api/v1/profiles/me",
        headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        json={"experiences": [{"title": "Old Job", "company": "Old Corp"}]}
    )
    
    # Send a new payload that should replace the old job
    update_payload = {
        "experiences": [{"title": "New Job", "company": "New Corp"}]
    }
    
    resp = client.put(
        "/api/v1/profiles/me",
        headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        json=update_payload
    )
    assert resp.status_code == 200
    data = resp.json()
    
    # We should only have the New Job now
    assert len(data["experiences"]) == 1
    assert data["experiences"][0]["title"] == "New Job"

def test_get_profile_unauthenticated(client: TestClient):
    client.cookies.clear()
    resp = client.get("/api/v1/profiles/me")
    assert resp.status_code == 401
