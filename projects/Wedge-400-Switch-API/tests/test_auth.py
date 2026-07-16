import os
import pytest
from fastapi.testclient import TestClient

# Use separate test database for tests
os.environ["DATABASE_PATH"] = "test_auth_switch.db"

from fastapi_starter.main import app
from fastapi_starter.database import init_db
from fastapi_starter.auth import COOKIE_NAME

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db(force_recreate=True)
    yield
    if os.path.exists("test_auth_switch.db"):
        os.remove("test_auth_switch.db")

def test_unauthenticated_access():
    """Unauthenticated requests to protected endpoints should return 401."""
    # Reset is admin-only
    response = client.post("/api/sys/switch_reset")
    assert response.status_code == 401
    
    # Port updates are operator/admin
    response = client.patch("/api/sys/ports/Eth1/1", json={"admin_state": "down"})
    assert response.status_code == 401
    
    # Config updates are admin-only
    response = client.get("/api/auth/config")
    assert response.status_code == 401

def test_login_validation():
    """Verify login validation and role assignment for mock AD users."""
    # Fail login
    response = client.post("/api/auth/login", json={"username": "ad_admin", "password": "wrong_password"})
    assert response.status_code == 401
    assert "detail" in response.json()
    
    # Success Admin login
    response = client.post("/api/auth/login", json={"username": "ad_admin", "password": "AdminPass123"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "ad_admin"
    assert data["role"] == "admin"
    assert COOKIE_NAME in response.cookies
    
    # Success Operator login
    response = client.post("/api/auth/login", json={"username": "ad_operator", "password": "OperatorPass123"})
    assert response.status_code == 200
    assert response.json()["role"] == "operator"
    
    # Success Viewer login
    response = client.post("/api/auth/login", json={"username": "ad_viewer", "password": "ViewerPass123"})
    assert response.status_code == 200
    assert response.json()["role"] == "viewer"

def test_session_retribution():
    """Verify session data retrieval."""
    # Login as admin
    login_res = client.post("/api/auth/login", json={"username": "ad_admin", "password": "AdminPass123"})
    cookie_val = login_res.cookies.get(COOKIE_NAME)
    
    # Fetch session
    response = client.get("/api/auth/session", cookies={COOKIE_NAME: cookie_val})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "ad_admin"
    assert data["role"] == "admin"

def test_rbac_rules():
    """Verify role-based access control policies."""
    # Login as viewer
    viewer_login = client.post("/api/auth/login", json={"username": "ad_viewer", "password": "ViewerPass123"})
    viewer_cookie = viewer_login.cookies.get(COOKIE_NAME)
    
    # Login as operator
    operator_login = client.post("/api/auth/login", json={"username": "ad_operator", "password": "OperatorPass123"})
    operator_cookie = operator_login.cookies.get(COOKIE_NAME)
    
    # Login as admin
    admin_login = client.post("/api/auth/login", json={"username": "ad_admin", "password": "AdminPass123"})
    admin_cookie = admin_login.cookies.get(COOKIE_NAME)
    
    # 1. Viewer trying to patch port -> 403
    res = client.patch("/api/sys/ports/Eth1/1", json={"admin_state": "down"}, cookies={COOKIE_NAME: viewer_cookie})
    assert res.status_code == 403
    
    # 2. Operator trying to patch port -> 200
    res = client.patch("/api/sys/ports/Eth1/1", json={"admin_state": "down"}, cookies={COOKIE_NAME: operator_cookie})
    assert res.status_code == 200
    
    # 3. Operator trying to trigger switch reset -> 403
    res = client.post("/api/sys/switch_reset", cookies={COOKIE_NAME: operator_cookie})
    assert res.status_code == 403
    
    # 4. Admin trying to trigger switch reset -> 200
    res = client.post("/api/sys/switch_reset", cookies={COOKIE_NAME: admin_cookie})
    assert res.status_code == 200

def test_ad_config_endpoints():
    """Verify AD config endpoints access controls and serialization."""
    # Login as admin
    admin_login = client.post("/api/auth/login", json={"username": "ad_admin", "password": "AdminPass123"})
    admin_cookie = admin_login.cookies.get(COOKIE_NAME)
    
    # Login as operator
    operator_login = client.post("/api/auth/login", json={"username": "ad_operator", "password": "OperatorPass123"})
    operator_cookie = operator_login.cookies.get(COOKIE_NAME)
    
    # Get config as Operator -> 403
    res = client.get("/api/auth/config", cookies={COOKIE_NAME: operator_cookie})
    assert res.status_code == 403
    
    # Get config as Admin -> 200
    res = client.get("/api/auth/config", cookies={COOKIE_NAME: admin_cookie})
    assert res.status_code == 200
    config_data = res.json()
    assert config_data["ad_group_admin"] == "RDIT-Admin"
    assert config_data["ad_simulate"] == "true"
    
    # Update config as Admin
    config_data["ad_domain"] = "new-domain.local"
    res = client.post("/api/auth/config", json=config_data, cookies={COOKIE_NAME: admin_cookie})
    assert res.status_code == 200
    
    # Fetch again to verify update
    res = client.get("/api/auth/config", cookies={COOKIE_NAME: admin_cookie})
    assert res.status_code == 200
    assert res.json()["ad_domain"] == "new-domain.local"

def test_logout():
    """Verify logout deletes the cookie."""
    login_res = client.post("/api/auth/login", json={"username": "ad_viewer", "password": "ViewerPass123"})
    cookie_val = login_res.cookies.get(COOKIE_NAME)
    
    # Logout
    res = client.post("/api/auth/logout", cookies={COOKIE_NAME: cookie_val})
    assert res.status_code == 200
    # The session cookie value should be deleted/removed
    assert res.cookies.get(COOKIE_NAME) is None or res.cookies.get(COOKIE_NAME) == ""


def test_real_ldap_bind_flow_direct():
    """Verify authenticate_ad behaves correctly with direct binds when bind_dn is empty."""
    from unittest.mock import patch, MagicMock
    from fastapi_starter.auth import authenticate_ad
    from fastapi_starter.database import update_ad_config

    # Enable live AD mode
    update_ad_config({
        "ad_simulate": "false",
        "ad_server": "ldap://ad-test.local:389",
        "ad_domain": "ad-test.local",
        "ad_base_dn": "dc=ad-test,dc=local",
        "ad_bind_dn": "",
        "ad_bind_password": "",
        "ad_group_admin": "RDIT-Admin"
    })

    with patch("ldap3.Connection") as mock_conn_cls:
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        
        # 1. Bind succeeds
        mock_conn.bind.return_value = True
        
        # 2. Mock search returns a user belonging to RDIT-Admin
        mock_entry = MagicMock()
        mock_entry.entry_dn = "cn=testuser,ou=Users,dc=ad-test,dc=local"
        mock_entry.memberOf.value = ["cn=RDIT-Admin,ou=Groups,dc=ad-test,dc=local"]
        mock_conn.entries = [mock_entry]

        res = authenticate_ad("testuser", "testpass")
        assert res is not None
        assert res["username"] == "testuser"
        assert res["role"] == "admin"

        # Assert direct bind was called with testuser@ad-test.local
        mock_conn_cls.assert_called_with(
            mock_conn_cls.call_args[0][0],
            user="testuser@ad-test.local",
            password="testpass",
            authentication=mock_conn_cls.call_args[1].get("authentication")
        )


def test_real_ldap_bind_flow_service_account():
    """Verify authenticate_ad behaves correctly when a query service account bind_dn is configured."""
    from unittest.mock import patch, MagicMock
    from fastapi_starter.auth import authenticate_ad
    from fastapi_starter.database import update_ad_config

    # Set service bind credentials
    update_ad_config({
        "ad_simulate": "false",
        "ad_server": "ldap://ad-test.local:389",
        "ad_domain": "ad-test.local",
        "ad_base_dn": "dc=ad-test,dc=local",
        "ad_bind_dn": "cn=ServiceUser,cn=Users,dc=ad-test,dc=local",
        "ad_bind_password": "service_password",
        "ad_group_admin": "RDIT-Admin"
    })

    with patch("ldap3.Connection") as mock_conn_cls:
        mock_service_conn = MagicMock()
        mock_user_conn = MagicMock()
        
        # Connection class returns service connection, then user connection on successive calls
        mock_conn_cls.side_effect = [mock_service_conn, mock_user_conn]
        
        # Service bind and user bind both succeed
        mock_service_conn.bind.return_value = True
        mock_user_conn.bind.return_value = True
        
        # Mock search returns user entry with dn and group membership
        mock_entry = MagicMock()
        mock_entry.entry_dn = "cn=testuser,ou=Users,dc=ad-test,dc=local"
        mock_entry.memberOf.value = ["cn=RDIT-Admin,ou=Groups,dc=ad-test,dc=local"]
        mock_service_conn.entries = [mock_entry]

        res = authenticate_ad("testuser", "testpass")
        assert res is not None
        assert res["username"] == "testuser"
        assert res["role"] == "admin"

        # First connection bind was using Service account
        mock_conn_cls.assert_any_call(
            mock_conn_cls.call_args_list[0][0][0],
            user="cn=ServiceUser,cn=Users,dc=ad-test,dc=local",
            password="service_password",
            authentication=mock_conn_cls.call_args_list[0][1].get("authentication")
        )
        
        # Second connection bind was using retrieved user DN and user password
        mock_conn_cls.assert_any_call(
            mock_conn_cls.call_args_list[1][0][0],
            user="cn=testuser,ou=Users,dc=ad-test,dc=local",
            password="testpass",
            authentication=mock_conn_cls.call_args_list[1][1].get("authentication")
        )

    # Re-enable simulation for subsequent tests
    update_ad_config({"ad_simulate": "true"})
