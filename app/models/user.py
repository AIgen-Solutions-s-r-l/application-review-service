from sqlalchemy import Column, Integer, String
from app.core.postgres import Base

class User(Base):
    """
    SQLAlchemy model representing a user in the database.

    Attributes:
        id (int): The primary key for the user.
        username (str): Unique username for the user.
        email (str): Unique email for the user.
        hashed_password (str): Hashed password for the user.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)