from datetime import datetime, UTC
from sqlmodel import SQLModel, Field
from enum import StrEnum

class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Role(StrEnum):
    ADMIN = "admin"
    CUSTOMER = "customer"
    AGENT = "agent"

class Status(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

# Shared base for common fields on database
class BaseTable(SQLModel):
    """Base Table model which contains the attributes that every table should have"""
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )
    deleted_at: datetime | None = None

# Specific models
class User(BaseTable, table=True):
    """Represents every user in the system, including from customers up to admins."""
    __tablename__ = "users"
    email: str = Field(unique=True, index=True)
    hashed_password: str = Field()
    role: Role = Field(default=Role.CUSTOMER)

class Ticket(BaseTable, table=True):
    """Represents the tickets that customer needs to open and need to be reviewed"""
    __tablename__ = "tickets"
    title: str = Field()
    description: str = Field()
    status: Status = Field(default=Status.OPEN)
    priority: Priority = Field(default=Priority.MEDIUM)
    owner_id: int = Field(foreign_key="users.id")
    assignee_id: int | None = Field(default=None, foreign_key="users.id")
    
class Comment(BaseTable, table=True):
    """The comments that can be inserted on the Tickets"""
    __tablename__ = "comments"
    ticket_id: int = Field(foreign_key="tickets.id")
    author_id: int = Field(foreign_key="users.id")
    body: str = Field()
    is_internal: bool = Field(default=False)