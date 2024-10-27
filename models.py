from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Float,
    DateTime,
    Boolean,
    create_engine,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from setting import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    firstname = Column(String, nullable=False)
    country = Column(String, nullable=False)
    phone = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    user_date = Column(DateTime, server_default=func.now(), nullable=True)
    card_identity = Column(String, nullable=False, unique=True)
    city = Column(String, nullable=False)

    # Relationships
    security = relationship("Security", back_populates="user", uselist=False)
    accounts_fcfa = relationship(
        "AccountFCFA", back_populates="user", cascade="all, delete-orphan"
    )
    accounts_dh = relationship(
        "AccountDH", back_populates="user", cascade="all, delete-orphan"
    )
    contacts = relationship(
        "Contacts", back_populates="user", cascade="all, delete-orphan"
    )
    recharges = relationship(
        "Recharges", back_populates="user", cascade="all, delete-orphan"
    )


class AccountFCFA(Base):
    __tablename__ = "accounts_fcfa"
    id = Column(Integer, primary_key=True, autoincrement=True)
    balance = Column(Float, nullable=False)
    card_id = Column(String, nullable=False)
    account_date = Column(DateTime, server_default=func.now(), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Boolean, default=True)

    # Relation
    user = relationship("User", back_populates="accounts_fcfa")


class AccountDH(Base):
    __tablename__ = "accounts_dh"
    id = Column(Integer, primary_key=True, autoincrement=True)
    balance = Column(Float, nullable=False)
    card_id = Column(String, nullable=False)
    account_date = Column(DateTime, server_default=func.now(), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Boolean, default=True)

    # Relation
    user = relationship("User", back_populates="accounts_dh")


class TransactionHistory(Base):
    __tablename__ = "transaction_histories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    receiver = Column(String, nullable=False)
    sender = Column(String, nullable=False)
    transaction_date = Column(DateTime, server_default=func.now(), nullable=True)
    transaction_amount = Column(Float, nullable=False)
    transaction_fee = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    devise = Column(String, nullable=False)

    # Relations
    receiver_user = relationship("User", foreign_keys=[receiver_id])
    sender_user = relationship("User", foreign_keys=[sender_id])


class Security(Base):
    __tablename__ = "security"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    user_type = Column(String, nullable=False)
    status = Column(Boolean, default=False)
    security_date = Column(DateTime, server_default=func.now(), nullable=True)
    activation_code = Column(String, nullable=True, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relation
    user = relationship("User", back_populates="security")


class Contacts(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    IDuser = Column(String, nullable=False)
    name = Column(String, nullable=False)
    contact_date = Column(DateTime, server_default=func.now(), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relation
    user = relationship("User", back_populates="contacts")


class Recharges(Base):
    __tablename__ = "recharges"
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero = Column(String, nullable=True)
    solde = Column(Float, nullable=True)
    status = Column(Boolean, nullable=False)
    card = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recharge_date = Column(DateTime, server_default=func.now(), nullable=True)
    # Relation
    user = relationship("User", back_populates="recharges")
