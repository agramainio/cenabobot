from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    short_description: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    source_name: Mapped[str | None] = mapped_column(String(160))
    source_url: Mapped[str | None] = mapped_column(Text)

    servings: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    prep_minutes: Mapped[int | None] = mapped_column(Integer)
    cook_minutes: Mapped[int | None] = mapped_column(Integer)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ingredients: Mapped[list[RecipeIngredient]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
    )
    tags: Mapped[list[RecipeTag]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
    )


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recipe_id: Mapped[str] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    quantity: Mapped[float | None] = mapped_column(Numeric(10, 2))
    unit: Mapped[str | None] = mapped_column(String(40))
    category: Mapped[str | None] = mapped_column(String(80))
    optional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    recipe: Mapped[Recipe] = relationship(back_populates="ingredients")


class RecipeTag(Base):
    __tablename__ = "recipe_tags"

    recipe_id: Mapped[str] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag: Mapped[str] = mapped_column(String(80), primary_key=True)

    recipe: Mapped[Recipe] = relationship(back_populates="tags")


class TelegramGroup(Base):
    __tablename__ = "telegram_groups"

    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str | None] = mapped_column(String(240))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TelegramUser(Base):
    __tablename__ = "telegram_users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(160))
    first_name: Mapped[str | None] = mapped_column(String(160))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("chat_id", "user_id", "recipe_id", name="uq_favorite_chat_user_recipe"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("telegram_groups.chat_id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("telegram_users.user_id", ondelete="CASCADE"))
    recipe_id: Mapped[str] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SuggestionHistory(Base):
    __tablename__ = "suggestion_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("telegram_groups.chat_id", ondelete="CASCADE"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("telegram_users.user_id", ondelete="SET NULL"))
    recipe_id: Mapped[str] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"))
    filter_key: Mapped[str | None] = mapped_column(String(120))
    suggested_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RecipeFeedback(Base):
    __tablename__ = "recipe_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("telegram_groups.chat_id", ondelete="CASCADE"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("telegram_users.user_id", ondelete="SET NULL"))
    recipe_id: Mapped[str] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"))

    feedback_type: Mapped[str] = mapped_column(String(80), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(160))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MealProposal(Base):
    __tablename__ = "meal_proposals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("telegram_groups.chat_id", ondelete="CASCADE"))
    message_id: Mapped[int | None] = mapped_column(BigInteger)
    recipe_id: Mapped[str] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"))
    filter_key: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False)
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("telegram_users.user_id", ondelete="SET NULL")
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    accepted_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))


class MealVote(Base):
    __tablename__ = "meal_votes"
    __table_args__ = (
        UniqueConstraint("proposal_id", "user_id", name="uq_meal_vote_proposal_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    proposal_id: Mapped[int] = mapped_column(ForeignKey("meal_proposals.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("telegram_users.user_id", ondelete="CASCADE"))
    user_name: Mapped[str | None] = mapped_column(String(160))
    vote: Mapped[str] = mapped_column(String(40), nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RecipeImportDraft(Base):
    __tablename__ = "recipe_import_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    raw_text: Mapped[str | None] = mapped_column(Text)

    submitted_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("telegram_users.user_id", ondelete="SET NULL")
    )
    submitted_by_name: Mapped[str | None] = mapped_column(String(160))

    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)

    proposed_recipe_id: Mapped[str | None] = mapped_column(String(120))
    proposed_title: Mapped[str | None] = mapped_column(String(240))
    proposed_yaml: Mapped[str | None] = mapped_column(Text)

    warnings: Mapped[str | None] = mapped_column(Text)
    validation_errors: Mapped[str | None] = mapped_column(Text)

    approved_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("telegram_users.user_id", ondelete="SET NULL")
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    approved_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))

