"""
Atoms services of permissions.
"""
import random

def grant_permission(user_id: str) -> None:
    """
    If user don't have permission to transfer files, grant permission to him.
    """
    print(f"[MOCK] {user_id} has been granted")


def query_permissions(user_id: str) -> bool:
    """
    Query if user has permission to transfer files.
    """
    has_permission = random.choice([True, False])
    print(f"[MOCK] {user_id} {'has' if has_permission else 'does not have'} permission to transfer files")
    return has_permission
