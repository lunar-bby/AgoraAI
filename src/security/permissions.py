from typing import Dict, Set, List, Optional
from enum import Enum, auto
from dataclasses import dataclass, field

class Permission(Enum):
    READ = auto()
    WRITE = auto()
    EXECUTE = auto()
    ADMIN = auto()

@dataclass
class Role:
    name: str
    permissions: Set[Permission]
    description: str = ""
    parent: Optional['Role'] = None
    
    def has_permission(self, permission: Permission) -> bool:
        if permission in self.permissions:
            return True
        return bool(self.parent and self.parent.has_permission(permission))

@dataclass
class AccessControl:
    resource_id: str
    owner_id: str
    roles: Dict[str, Set[str]] = field(default_factory=dict)
    direct_permissions: Dict[str, Set[Permission]] = field(default_factory=dict)

class PermissionManager:
    def __init__(self):
        self.roles: Dict[str, Role] = {}
        self.user_roles: Dict[str, Set[str]] = {}
        self.access_controls: Dict[str, AccessControl] = {}
        
        self._initialize_default_roles()
    
    def _initialize_default_roles(self) -> None:
        self.roles["admin"] = Role(
            name="admin",
            permissions={
                Permission.READ,
                Permission.WRITE,
                Permission.EXECUTE,
                Permission.ADMIN
            },
            description="Full system access"
        )
        
        self.roles["user"] = Role(
            name="user",
            permissions={Permission.READ, Permission.WRITE},
            description="Standard user access"
        )
        
        self.roles["observer"] = Role(
            name="observer",
            permissions={Permission.READ},
            description="Read-only access"
        )
    
    def create_role(
        self,
        name: str,
        permissions: Set[Permission],
        description: str = "",
        parent: Optional[str] = None
    ) -> Role:
        parent_role = self.roles.get(parent) if parent else None
        role = Role(name, permissions, description, parent_role)
        self.roles[name] = role
        return role
    
    def assign_role(self, user_id: str, role_name: str) -> None:
        if role_name not in self.roles:
            raise ValueError(f"Role {role_name} does not exist")
            
        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()
            
        self.user_roles[user_id].add(role_name)
    
    def remove_role(self, user_id: str, role_name: str) -> None:
        if user_id in self.user_roles:
            self.user_roles[user_id].discard(role_name)
    
    def get_user_roles(self, user_id: str) -> Set[str]:
        return self.user_roles.get(user_id, set())
    
    def has_permission(
        self,
        user_id: str,
        permission: Permission,
        resource_id: Optional[str] = None
    ) -> bool:
        # Check direct resource permissions
        if resource_id and resource_id in self.access_controls:
            ac = self.access_controls[resource_id]
            
            # Check if user is the owner
            if ac.owner_id == user_id:
                return True
                
            # Check direct permissions
            if user_id in ac.direct_permissions:
                if permission in ac.direct_permissions[user_id]:
                    return True
                    
            # Check role-based permissions
            if user_id in ac.roles:
                for role_name in ac.roles[user_id]:
                    role = self.roles.get(role_name)
                    if role and role.has_permission(permission):
                        return True
        
        # Check global roles
        user_roles = self.get_user_roles(user_id)
        return any(
            self.roles[role].has_permission(permission)
            for role in user_roles
            if role in self.roles
        )
    
    def create_access_control(
        self,
        resource_id: str,
        owner_id: str
    ) -> AccessControl:
        ac = AccessControl(resource_id, owner_id)
        self.access_controls[resource_id] = ac
        return ac
    
    def grant_permission(
        self,
        user_id: str,
        permission: Permission,
        resource_id: str
    ) -> None:
        if resource_id not in self.access_controls:
            raise ValueError(f"Resource {resource_id} does not exist")
            
        ac = self.access_controls[resource_id]
        if user_id not in ac.direct_permissions:
            ac.direct_permissions[user_id] = set()
            
        ac.direct_permissions[user_id].add(permission)
    
    def revoke_permission(
        self,
        user_id: str,
        permission: Permission,
        resource_id: str
    ) -> None:
        if resource_id in self.access_controls:
            ac = self.access_controls[resource_id]
            if user_id in ac.direct_permissions:
                ac.direct_permissions[user_id].discard(permission)
    
    def transfer_ownership(
        self,
        resource_id: str,
        new_owner_id: str
    ) -> None:
        if resource_id in self.access_controls:
            self.access_controls[resource_id].owner_id = new_owner_id
    
    def get_accessible_resources(
        self,
        user_id: str,
        permission: Permission
    ) -> List[str]:
        return [
            resource_id for resource_id, ac in self.access_controls.items()
            if self.has_permission(user_id, permission, resource_id)
        ]