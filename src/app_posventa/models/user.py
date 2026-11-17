from typing import List
from pydantic import BaseModel, EmailStr
from .enums import Role, ModuleEnum

class User(BaseModel):
    email: str
    name: str = ""
    role: Role = Role.AGENT
    allowed_modules: List[ModuleEnum] = []
    is_active: bool = True

    def has_module_access(self, module: ModuleEnum) -> bool:
        if self.role == Role.ADMIN:
            return True
        return module in self.allowed_modules

class UserUpdatePermissions(BaseModel):
    role: Role
    allowed_modules: List[ModuleEnum]
