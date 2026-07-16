import os
import re
import pytest

# Configure separate test database before importing main app
os.environ["DATABASE_PATH"] = "test_switch.db"

from fastapi.testclient import TestClient
from fastapi_starter.main import app
from fastapi_starter.database import init_db

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    # Initialize the test database
    init_db(force_recreate=True)
    yield
    # Clean up the test database file after running tests
    if os.path.exists("test_switch.db"):
        os.remove("test_switch.db")

def test_root_and_health():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Wedge 400" in response.text
    
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_openbmc_sensors():
    response = client.get("/api/sys/sensors")
    assert response.status_code == 200
    data = response.json()
    assert "scm" in data
    assert "fans" in data
    assert len(data["fans"]) == 4
    assert data["fans"][0]["name"] == "FAN1_SPEED_RPM"
    assert data["scm"][0]["name"] == "SCM_TEMP_C"

def test_openbmc_presence():
    for dev in ["scm", "psu", "pem", "fan"]:
        response = client.get(f"/api/sys/presence/{dev}")
        assert response.status_code == 200
        assert response.json()["device"] == dev
        assert response.json()["present"] is True

    response = client.get("/api/sys/presence/invalid_dev")
    assert response.status_code == 400

def test_openbmc_firmware_info():
    response = client.get("/api/sys/firmware_info/all")
    assert response.status_code == 200
    assert response.json()["cpld"] == "v2.4"
    assert response.json()["scm"] == "v1.5"

def test_openbmc_switch_reset():
    response = client.post("/api/sys/switch_reset")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_switch_ports():
    response = client.get("/api/sys/ports")
    assert response.status_code == 200
    ports = response.json()
    assert len(ports) > 0
    assert ports[0]["port_id"] == "Eth1/1"

    response = client.get("/api/sys/ports/Eth1/1")
    assert response.status_code == 200
    assert response.json()["port_id"] == "Eth1/1"

    response = client.get("/api/sys/ports/Eth1/999")
    assert response.status_code == 404

def test_patch_port():
    # Make sure DB is clean
    init_db(force_recreate=True)
    
    payload = {"admin_state": "down", "mtu": 9000, "speed_gbps": 100}
    response = client.patch("/api/sys/ports/Eth1/1", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["admin_state"] == "down"
    assert data["oper_state"] == "down"
    assert data["mtu"] == 9000
    assert data["speed_gbps"] == 100

    payload = {"admin_state": "up"}
    response = client.patch("/api/sys/ports/Eth1/1", json=payload)
    assert response.status_code == 200
    assert response.json()["admin_state"] == "up"

def test_vlans():
    # Make sure DB is clean
    init_db(force_recreate=True)
    
    response = client.get("/api/sys/vlans")
    assert response.status_code == 200
    vlans = response.json()
    assert len(vlans) >= 2

    new_vlan = {"vlan_id": 100, "name": "production", "ports": ["Eth1/1", "Eth1/2"]}
    response = client.post("/api/sys/vlans", json=new_vlan)
    assert response.status_code == 200
    assert response.json()["vlan_id"] == 100

    response = client.post("/api/sys/vlans/100/ports", json=["Eth1/3"])
    assert response.status_code == 200
    assert "Eth1/3" in response.json()["ports"]

def test_lldp():
    response = client.get("/api/sys/lldp")
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert response.json()[0]["local_port"] == "Eth1/1"

def test_dynamic_routes():
    # Register a custom mock route
    payload = {"path": "/api/sys/eeprom/scm", "payload": {"device": "scm", "serial": "W400-SCM-123456"}}
    response = client.post("/api/sys/routes", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Fetch registered routes
    response = client.get("/api/sys/routes")
    assert response.status_code == 200
    routes = response.json()
    assert len(routes) > 0
    assert routes[0]["path"] == "/api/sys/eeprom/scm"

    # Query the wildcard handler to see if it responds with the mock payload
    response = client.get("/api/sys/eeprom/scm")
    assert response.status_code == 200
    assert response.json() == {"device": "scm", "serial": "W400-SCM-123456"}


