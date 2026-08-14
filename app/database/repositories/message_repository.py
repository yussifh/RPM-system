"""
message_repository.py
-----------------------
Data access layer for the messages table.
Handles sending, reading, and listing messages between patients and doctors.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.database.repositories.base_repository import BaseRepository


@dataclass
class Message:
    id: Optional[int]
    sender_id: int
    receiver_id: int
    subject: str
    body: str
    is_read: bool
    sent_at: Optional[datetime]
    sender_name: Optional[str] = None
    receiver_name: Optional[str] = None

    @classmethod
    def from_row(cls, row: dict) -> "Message":
        return cls(
            id=row["id"],
            sender_id=row["sender_id"],
            receiver_id=row["receiver_id"],
            subject=row["subject"],
            body=row["body"],
            is_read=bool(row["is_read"]),
            sent_at=row.get("sent_at"),
            sender_name=row.get("sender_name"),
            receiver_name=row.get("receiver_name"),
        )


class MessageRepository(BaseRepository):

    def send(self, sender_id: int, receiver_id: int,
             subject: str, body: str) -> int:
        """Send a message. Returns the new message ID."""
        result = self.execute_write(
            """
            INSERT INTO messages (sender_id, receiver_id, subject, body)
            VALUES (%s, %s, %s, %s)
            """,
            (sender_id, receiver_id, subject, body),
        )
        return result["lastrowid"]

    def get_inbox(self, user_id: int, limit: int = 50) -> list[Message]:
        """Get all messages received by a user, newest first."""
        rows = self.execute_query(
            """
            SELECT m.*, 
                   u_sender.full_name  AS sender_name,
                   u_recv.full_name    AS receiver_name
            FROM messages m
            JOIN users u_sender ON u_sender.id = m.sender_id
            JOIN users u_recv   ON u_recv.id   = m.receiver_id
            WHERE m.receiver_id = %s
            ORDER BY m.sent_at DESC
            LIMIT %s
            """,
            (user_id, limit),
        )
        return [Message.from_row(r) for r in rows]

    def get_sent(self, user_id: int, limit: int = 50) -> list[Message]:
        """Get all messages sent by a user, newest first."""
        rows = self.execute_query(
            """
            SELECT m.*,
                   u_sender.full_name  AS sender_name,
                   u_recv.full_name    AS receiver_name
            FROM messages m
            JOIN users u_sender ON u_sender.id = m.sender_id
            JOIN users u_recv   ON u_recv.id   = m.receiver_id
            WHERE m.sender_id = %s
            ORDER BY m.sent_at DESC
            LIMIT %s
            """,
            (user_id, limit),
        )
        return [Message.from_row(r) for r in rows]

    def mark_as_read(self, message_id: int, user_id: int) -> None:
        """Mark a message as read (only receiver can mark it)."""
        self.execute_write(
            """
            UPDATE messages SET is_read = TRUE
            WHERE id = %s AND receiver_id = %s
            """,
            (message_id, user_id),
        )

    def count_unread(self, user_id: int) -> int:
        """Count unread messages for a user — used for badge display."""
        row = self.execute_one(
            "SELECT COUNT(*) AS cnt FROM messages WHERE receiver_id = %s AND is_read = FALSE",
            (user_id,),
        )
        return row["cnt"] if row else 0

    def get_conversation(self, user_a: int, user_b: int, limit: int = 100) -> list[Message]:
        """Get full conversation thread between two users."""
        rows = self.execute_query(
            """
            SELECT m.*,
                   u_sender.full_name AS sender_name,
                   u_recv.full_name   AS receiver_name
            FROM messages m
            JOIN users u_sender ON u_sender.id = m.sender_id
            JOIN users u_recv   ON u_recv.id   = m.receiver_id
            WHERE (m.sender_id = %s AND m.receiver_id = %s)
               OR (m.sender_id = %s AND m.receiver_id = %s)
            ORDER BY m.sent_at ASC
            LIMIT %s
            """,
            (user_a, user_b, user_b, user_a, limit),
        )
        return [Message.from_row(r) for r in rows]

    def delete(self, message_id: int, user_id: int) -> None:
        """Delete a message (only sender or receiver can delete)."""
        self.execute_write(
            """
            DELETE FROM messages
            WHERE id = %s AND (sender_id = %s OR receiver_id = %s)
            """,
            (message_id, user_id, user_id),
        )
