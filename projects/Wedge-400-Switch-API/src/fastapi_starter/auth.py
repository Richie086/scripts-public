import jwt
import ldap3
from datetime import datetime, timedelta, timezone
from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyCookie
from typing import Dict, Any, List, Optional
from . import database as db

# Cookie-based session extractor
COOKIE_NAME = "wedge_session"
cookie_sec = APIKeyCookie(name=COOKIE_NAME, auto_error=False)

def create_token(username: str, role: str, secret: str) -> str:
    """Generate signed JWT token valid for 8 hours."""
    payload = {
        "sub": username,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=8)
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def verify_token(token: str, secret: str) -> Optional[Dict[str, Any]]:
    """Decode and verify JWT token signature and expiration."""
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return {
            "username": payload.get("sub"),
            "role": payload.get("role")
        }
    except jwt.PyJWTError:
        return None

def authenticate_ad(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate against Active Directory / LDAP.
    Supports local simulation mode if config key 'ad_simulate' is set to 'true'.
    """
    config = db.get_ad_config()
    is_simulate = config.get("ad_simulate", "true").lower() == "true"

    if is_simulate:
        # Predefined mock accounts for simulation/testing
        mock_users = {
            "ad_admin": {"password": "AdminPass123", "role": "admin", "group": config.get("ad_group_admin", "RDIT-Admin")},
            "ad_operator": {"password": "OperatorPass123", "role": "operator", "group": config.get("ad_group_operator", "WedgeOperators")},
            "ad_viewer": {"password": "ViewerPass123", "role": "viewer", "group": config.get("ad_group_viewer", "WedgeViewers")},
        }
        
        user_info = mock_users.get(username)
        if user_info and user_info["password"] == password:
            return {
                "username": username,
                "role": user_info["role"],
                "group": user_info["group"]
            }
        return None

    # Real LDAP Authentication
    server_url = config.get("ad_server", "ldap://ad.company.local:389")
    domain = config.get("ad_domain", "company.local")
    base_dn = config.get("ad_base_dn", "dc=company,dc=local")
    bind_dn = config.get("ad_bind_dn", "")
    bind_password = config.get("ad_bind_password", "")

    try:
        server = ldap3.Server(server_url, get_info=ldap3.ALL)
        
        # 1. Establish search connection (Service Account or Direct User)
        if bind_dn:
            conn = ldap3.Connection(server, user=bind_dn, password=bind_password, authentication=ldap3.SIMPLE)
            if not conn.bind():
                print(f"LDAP Error: Service account bind failed for {bind_dn}")
                return None
        else:
            user_dn = username
            if "@" not in username and "\\" not in username and domain:
                user_dn = f"{username}@{domain}"
            conn = ldap3.Connection(server, user=user_dn, password=password, authentication=ldap3.SIMPLE)
            if not conn.bind():
                return None

        # 2. Search for the user record to extract groups and full DN
        search_filter = f"(sAMAccountName={username})"
        conn.search(search_base=base_dn, search_filter=search_filter, attributes=["memberOf"])
        
        if not conn.entries and "@" not in username and domain:
            search_filter = f"(userPrincipalName={username}@{domain})"
            conn.search(search_base=base_dn, search_filter=search_filter, attributes=["memberOf"])

        if not conn.entries:
            conn.unbind()
            return None

        user_entry = conn.entries[0]
        user_actual_dn = user_entry.entry_dn

        # 3. Verify user password by attempting direct simple bind
        if bind_dn:
            user_conn = ldap3.Connection(server, user=user_actual_dn, password=password, authentication=ldap3.SIMPLE)
            if not user_conn.bind():
                conn.unbind()
                return None
            user_conn.unbind()

        # 4. Extract groups and map roles
        role = "viewer" # default fallback
        matched_group = "None"
        
        groups = user_entry.memberOf.value if hasattr(user_entry, "memberOf") else []
        group_names = []
        
        for g_dn in groups:
            try:
                cn = g_dn.split(",")[0].split("=")[1]
                group_names.append(cn.lower())
            except Exception:
                pass
        
        admin_group = config.get("ad_group_admin", "RDIT-Admin").lower()
        operator_group = config.get("ad_group_operator", "WedgeOperators").lower()
        viewer_group = config.get("ad_group_viewer", "WedgeViewers").lower()
        
        if admin_group in group_names:
            role = "admin"
            matched_group = config.get("ad_group_admin", "RDIT-Admin")
        elif operator_group in group_names:
            role = "operator"
            matched_group = config.get("ad_group_operator", "WedgeOperators")
        elif viewer_group in group_names:
            role = "viewer"
            matched_group = config.get("ad_group_viewer", "WedgeViewers")
            
        conn.unbind()
        return {
            "username": username,
            "role": role,
            "group": matched_group
        }
    except Exception as e:
        # Log LDAP failures or network timeouts gracefully
        print(f"LDAP Error: {e}")
        return None

def get_current_user(request: Request, token: Optional[str] = Security(cookie_sec)) -> Dict[str, Any]:
    """Retrieve logged-in user profile from session cookie."""
    if not token:
        raise HTTPException(status_code=401, detail="Session cookie missing or expired")
    
    config = db.get_ad_config()
    secret = config.get("jwt_secret", "default_jwt_secret_key_change_me_in_production")
    
    user_payload = verify_token(token, secret)
    if not user_payload:
        raise HTTPException(status_code=401, detail="Invalid session credentials")
        
    return user_payload

class require_role:
    """Security dependency ensuring current user has one of the allowed roles."""
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
        
    def __call__(self, user: Dict[str, Any] = Security(get_current_user)) -> Dict[str, Any]:
        if user.get("role") not in self.allowed_roles:
            raise HTTPException(status_code=403, detail="Permission denied: Insufficient privileges")
        return user
