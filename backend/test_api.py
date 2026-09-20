import requests

def test():
    print("Testing API")
    r = requests.post("http://localhost:8000/api/v1/auth/login", json={"email": "test@example.com", "password": "password"})
    if r.status_code != 200:
        print("Login failed:", r.json())
        r = requests.post("http://localhost:8000/api/v1/auth/register", json={"email": "test@example.com", "password": "password", "full_name": "Test User"})
        print("Register:", r.status_code)
        r = requests.post("http://localhost:8000/api/v1/auth/login", json={"email": "test@example.com", "password": "password"})
        
    token = r.json().get("access_token")
    if not token:
        print("Failed to get token")
        return
        
    headers = {"Authorization": f"Bearer {token}"}
    print("Importing...")
    r = requests.post("http://localhost:8000/api/v1/jobs/import", json={"source_type": "url", "data": "https://careers.google.com/jobs/results/123/"}, headers=headers)
    print("Status:", r.status_code)
    print("Response:", r.json())

if __name__ == "__main__":
    test()
