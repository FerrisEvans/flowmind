"""
Common functions for the skills.
"""
import random


def get_file_size(file_path: str) -> int:
    """
    Get the size of the file from the file_path.
    """
    size = random.randint(100, 1000)
    print(f"{file_path}'s size is {size}")
    return size
