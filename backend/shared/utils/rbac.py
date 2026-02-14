from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()


class RBACMiddleware:
    """Role-Based Access Control middleware"""
    
    def __init__(self, jwt_secret: str, jwt_algorithm: str = "HS256"):
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
    
    def verify_token(self, token: str) -> dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            return payload
        except JWTError as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict:
        """Get current user from JWT token"""
        token = credentials.credentials
        payload = self.verify_token(token)
        
        user_id = payload.get("sub")
        role = payload.get("role")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": role
        }
    
    def require_role(self, required_role: str):
        """Dependency to require specific role"""
        def role_checker(
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ) -> dict:
            user = self.get_current_user(credentials)
            
            if user.get("role") != required_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required role: {required_role}"
                )
            
            return user
        
        return role_checker
    
    def require_admin(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict:
        """Dependency to require ADMIN role"""
        user = self.get_current_user(credentials)
        
        if user.get("role") != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin role required."
            )
        
        return user
    
    def require_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict:
        """Dependency to require USER role (or ADMIN)"""
        user = self.get_current_user(credentials)
        
        if user.get("role") not in ["USER", "ADMIN"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. User role required."
            )
        
        return user


# Helper function to create RBAC instance
def create_rbac(jwt_secret: str, jwt_algorithm: str = "HS256") -> RBACMiddleware:
    """Create RBAC middleware instance"""
    return RBACMiddleware(jwt_secret, jwt_algorithm)
