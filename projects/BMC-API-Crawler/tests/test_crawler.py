import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from crawler.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_settings():
    # GET settings
    response = client.get("/api/settings")
    assert response.status_code == 200
    assert "switch_url" in response.json()

    # POST settings
    payload = {"switch_url": "http://192.168.1.99/projects/test-switch"}
    response = client.post("/api/settings", json=payload)
    assert response.status_code == 200
    assert response.json()["switch_url"] == "http://192.168.1.99/projects/test-switch"

@patch("httpx.get")
@patch("httpx.post")
def test_crawl_flow(mock_post, mock_get):
    # Mock httpx.get to return a mock python script containing api endpoints
    mock_response_get = MagicMock()
    mock_response_get.status_code = 200
    mock_response_get.text = 'self.query("/api/sys/mac_address"); self.query("/api/sys/eeprom/scm")'
    mock_get.return_value = mock_response_get

    # Mock httpx.post for route registrations on switch
    mock_response_post = MagicMock()
    mock_response_post.status_code = 200
    mock_post.return_value = mock_response_post

    # Request crawl
    payload = {
        "url": "https://raw.githubusercontent.com/test-endpoint.py",
        "switch_url": "http://127.0.0.1:8000/projects/wedge-switch-400-api"
    }
    response = client.post("/api/crawl", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "/api/sys/mac_address" in data["endpoints_found"]
    assert "/api/sys/eeprom/scm" in data["endpoints_found"]
    assert len(data["registered"]) == 2
    
    # Check that post was called to push routes to switch
    assert mock_post.call_count == 2

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "BMC API Crawler Console" in response.text

@patch("httpx.get")
def test_crawl_error_handling(mock_get):
    # Test HTTP fetch error (non-200)
    mock_response_get = MagicMock()
    mock_response_get.status_code = 404
    mock_get.return_value = mock_response_get

    payload = {
        "url": "https://raw.githubusercontent.com/invalid-file.py",
        "switch_url": "http://127.0.0.1:8000/projects/wedge-switch-400-api"
    }
    response = client.post("/api/crawl", json=payload)
    assert response.status_code == 400
    assert "Failed to fetch doc URL" in response.json()["detail"]

    # Test HTTP connection exception
    mock_get.side_effect = Exception("Connection refused")
    response = client.post("/api/crawl", json=payload)
    assert response.status_code == 400
    assert "HTTP connection error fetching doc" in response.json()["detail"]
