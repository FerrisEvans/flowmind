"""
Atoms services of file transfer.
"""

def file_transfer(file_path: str, sender_id: str, receiver_id: str) -> None:
    """
    Transfer a file from one user to another.

    Preconditions:
    - sender has access/permission to transfer files.
    - receiver has enough space quota to receive the file.

    Args:
        file_path: The path of the file to transfer.
        sender_id: The ID of the sender.
        receiver_id: The ID of the receiver.
    """
    print(f"[MOCK] file transfer: from {sender_id} to {receiver_id}, file: {file_path}")
