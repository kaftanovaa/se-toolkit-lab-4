"""Unit tests for item endpoints and filtering logic."""

import asyncio
import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.item import ItemRecord, ItemUpdate


def test_filter_by_item_id_with_zero_returns_empty() -> None:
    """Test that filtering with item_id=0 returns matching items (boundary value)."""
    from app.routers.interactions import _filter_by_item_id
    from app.models.interaction import InteractionLog
    
    interactions = [
        InteractionLog(id=1, learner_id=1, item_id=1, kind="attempt"),
        InteractionLog(id=2, learner_id=2, item_id=0, kind="view"),
    ]
    result = _filter_by_item_id(interactions, 0)
    assert len(result) == 1
    assert result[0].id == 2


def test_filter_by_item_id_with_multiple_matches() -> None:
    """Test filtering returns all interactions matching the same item_id."""
    from app.routers.interactions import _filter_by_item_id
    from app.models.interaction import InteractionLog
    interactions = [
        InteractionLog(id=1, learner_id=1, item_id=5, kind="attempt"),
        InteractionLog(id=2, learner_id=2, item_id=3, kind="view"),
        InteractionLog(id=3, learner_id=3, item_id=5, kind="hint"),
        InteractionLog(id=4, learner_id=4, item_id=5, kind="attempt"),
    ]
    result = _filter_by_item_id(interactions, 5)
    assert len(result) == 3
    assert all(i.item_id == 5 for i in result)
    assert [i.id for i in result] == [1, 3, 4]


def test_get_item_returns_404_for_nonexistent_id() -> None:
    """Test that get_item raises 404 when item does not exist."""
    from app.routers.items import get_item
    
    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=None)
    
    async def run_test():
        with pytest.raises(HTTPException) as exc_info:
            await get_item(item_id=999, session=mock_session)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Item not found"
    
    asyncio.run(run_test())


def test_put_item_returns_404_for_nonexistent_id() -> None:
    """Test that put_item returns 404 when updating a non-existent item."""
    from app.routers.items import put_item
    
    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=None)
    
    body = ItemUpdate(title="Title", description="New new description")
    
    async def run_test():
        with pytest.raises(HTTPException) as exc_info:
            await put_item(item_id=888, body=body, session=mock_session)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Item not found"
    
    asyncio.run(run_test())


def test_put_item_updates_only_title_and_description() -> None:
    """Test that put_item only updates title and description, not type or parent_id"""
    from app.routers.items import put_item
    
    mock_session = AsyncMock()
    existing_item = ItemRecord(
        id=42,
        type="task",
        parent_id=10,
        title="Original Title",
        description="Original description",
    )
    mock_session.get = AsyncMock(return_value=existing_item)
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    
    body = ItemUpdate(title="Title", description="")
    
    async def run_test():
        result = await put_item(item_id=42, body=body, session=mock_session)
        assert result.title == "Title"
        assert result.description == ""
        assert result.type == "task"
        assert result.parent_id == 10
    
    asyncio.run(run_test())
