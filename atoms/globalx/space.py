"""
Atoms services of web-spaces.
"""
import random

def query_quota(user_id: str) -> int:
    """
    Query the quota of the user.
    """
    quota = random.randint(100, 1000)
    print(f"[MOCK] {user_id} has {quota} quota to transfer files")
    return quota
