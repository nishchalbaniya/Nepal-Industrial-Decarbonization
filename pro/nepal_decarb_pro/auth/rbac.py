"""
Role-based access control (RBAC) for the platform.
==================================================

Roles:
  - admin    : full control, user management, configuration
  - operator : data input, dashboard, monitoring (no config)
  - auditor  : read-only access, full audit trail
  - viewer   : dashboards, reports (read-only)
  - api      : service-to-service, programmatic access
"""
from __future__ import annotations

import hashlib
import logging
import secrets
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class Role(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    AUDITOR = "auditor"
    VIEWER = "viewer"
    API = "api"


# Permissions catalog
class Perm(str, Enum):
    # Data
    DATA_INPUT = "data:input"
    DATA_VIEW = "data:view"
    DATA_DELETE = "data:delete"
    # Configuration
    CONFIG_VIEW = "config:view"
    CONFIG_EDIT = "config:edit"
    # Users
    USERS_VIEW = "users:view"
    USERS_EDIT = "users:edit"
    # Reports
    REPORTS_VIEW = "reports:view"
    REPORTS_GENERATE = "reports:generate"
    # Compliance
    COMPLIANCE_VIEW = "compliance:view"
    COMPLIANCE_SUBMIT = "compliance:submit"
    # Markets
    MARKETS_VIEW = "markets:view"
    MARKETS_TRADE = "markets:trade"
    # Realtime
    REALTIME_VIEW = "realtime:view"
    REALTIME_CONTROL = "realtime:control"
    # System
    SYSTEM_ADMIN = "system:admin"


ROLE_PERMS: Dict[Role, Set[Perm]] = {
    Role.ADMIN:    {p for p in Perm},
    Role.OPERATOR: {Perm.DATA_INPUT, Perm.DATA_VIEW, Perm.REPORTS_VIEW, Perm.REPORTS_GENERATE,
                    Perm.MARKETS_VIEW, Perm.REALTIME_VIEW, Perm.CONFIG_VIEW, Perm.COMPLIANCE_VIEW},
    Role.AUDITOR:  {Perm.DATA_VIEW, Perm.REPORTS_VIEW, Perm.COMPLIANCE_VIEW,
                    Perm.MARKETS_VIEW, Perm.USERS_VIEW, Perm.CONFIG_VIEW, Perm.REALTIME_VIEW},
    Role.VIEWER:   {Perm.DATA_VIEW, Perm.REPORTS_VIEW, Perm.MARKETS_VIEW, Perm.REALTIME_VIEW},
    Role.API:      {Perm.DATA_INPUT, Perm.DATA_VIEW, Perm.REPORTS_VIEW, Perm.REPORTS_GENERATE,
                    Perm.COMPLIANCE_VIEW, Perm.MARKETS_VIEW, Perm.REALTIME_VIEW, Perm.CONFIG_VIEW},
}


@dataclass
class User:
    id: str
    username: str
    email: str
    role: Role
    plant_ids: List[str]                       # plants user has access to
    password_hash: str
    api_token: Optional[str] = None
    active: bool = True
    created_at: float = field(default_factory=time.time)
    last_login: Optional[float] = None
    mfa_enabled: bool = False


@dataclass
class AuditEntry:
    """Immutable audit log entry."""
    id: str
    user_id: str
    username: str
    action: str
    resource: str
    timestamp: float
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict = field(default_factory=dict)


def hash_password(pw: str, salt: Optional[str] = None) -> str:
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 100_000)
    return f"{salt}${h.hex()}"


def verify_password(pw: str, stored: str) -> bool:
    try:
        salt, _ = stored.split("$", 1)
    except ValueError:
        return False
    return hash_password(pw, salt) == stored


class RBACManager:
    """User / role / audit manager. Backed by SQLite JSON for portability."""
    def __init__(self, store_path: str = "rbac_store.json"):
        self.store_path = store_path
        self.users: Dict[str, User] = {}
        self.audit: List[AuditEntry] = []
        self._load()

    def _load(self) -> None:
        p = Path(self.store_path)
        if p.exists():
            import json
            data = json.loads(p.read_text())
            for u in data.get("users", []):
                u["role"] = Role(u["role"])
                self.users[u["id"]] = User(**u)
            self.audit = [AuditEntry(**e) for e in data.get("audit", [])]

    def _save(self) -> None:
        import json
        data = {
            "users": [{**u.__dict__, "role": u.role.value} for u in self.users.values()],
            "audit": [a.__dict__ for a in self.audit[-10_000:]],  # keep last 10k
        }
        Path(self.store_path).write_text(json.dumps(data, indent=2, default=str))

    # --- Users ----------------------------------------------------------
    def create_user(self, username: str, email: str, role: Role, password: str,
                    plant_ids: List[str] = None) -> User:
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            role=role,
            plant_ids=plant_ids or [],
            password_hash=hash_password(password),
            api_token=secrets.token_urlsafe(32) if role == Role.API else None,
        )
        self.users[user.id] = user
        self._audit("create_user", "user", user_id=user.id, details={"role": role.value})
        self._save()
        return user

    def authenticate(self, username: str, password: str) -> Optional[User]:
        for u in self.users.values():
            if u.username == username and u.active and verify_password(password, u.password_hash):
                u.last_login = time.time()
                self._audit("login", "user", user_id=u.id)
                self._save()
                return u
        self._audit("login_failed", "user", details={"username": username})
        return None

    def authenticate_token(self, token: str) -> Optional[User]:
        for u in self.users.values():
            if u.api_token == token and u.active:
                return u
        return None

    def get_user(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)

    def list_users(self) -> List[User]:
        return list(self.users.values())

    def deactivate_user(self, user_id: str) -> None:
        if user_id in self.users:
            self.users[user_id].active = False
            self._audit("deactivate_user", "user", user_id=user_id)
            self._save()

    # --- Authorization --------------------------------------------------
    def has_permission(self, user: User, perm: Perm, plant_id: Optional[str] = None) -> bool:
        if not user.active:
            return False
        if perm not in ROLE_PERMS.get(user.role, set()):
            return False
        # Plant-level scoping
        if plant_id and user.plant_ids and plant_id not in user.plant_ids:
            return False
        return True

    def require(self, user: User, perm: Perm, plant_id: Optional[str] = None) -> None:
        if not self.has_permission(user, perm, plant_id):
            self._audit("permission_denied", perm.value, user_id=user.id,
                        details={"plant_id": plant_id})
            raise PermissionError(f"User {user.username} lacks {perm.value}")

    # --- Audit ----------------------------------------------------------
    def _audit(self, action: str, resource: str, user_id: str = "system",
               username: str = "system", **kwargs) -> None:
        entry = AuditEntry(
            id=str(uuid.uuid4()),
            user_id=user_id, username=username, action=action, resource=resource,
            timestamp=time.time(), **kwargs,
        )
        self.audit.append(entry)

    def list_audit(self, since_ts: float = 0.0,
                   user_id: Optional[str] = None,
                   action: Optional[str] = None) -> List[AuditEntry]:
        out = [a for a in self.audit if a.timestamp >= since_ts]
        if user_id:
            out = [a for a in out if a.user_id == user_id]
        if action:
            out = [a for a in out if a.action == action]
        return out

    # --- Bootstrap ------------------------------------------------------
    def ensure_default_admin(self) -> None:
        """Create a default admin if no users exist."""
        if not self.users:
            admin = self.create_user("admin", "admin@himalayancarbonnepal.com",
                                     Role.ADMIN, "ChangeMe!2026", plant_ids=["*"])
            logger.info("Default admin created. username=admin, password=ChangeMe!2026")
            return admin


# Global default
_default_rbac: Optional[RBACManager] = None

def get_rbac() -> RBACManager:
    global _default_rbac
    if _default_rbac is None:
        _default_rbac = RBACManager()
        _default_rbac.ensure_default_admin()
    return _default_rbac
