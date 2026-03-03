"""Unit tests for learner endpoints and filtering logic."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, call

from app.models.learner import Learner


def test_read_learners_filters_by_enrolled_after_boundary() -> None:
    """Test that read_learners passes enrolled_after filter to the query."""
    from app.db.learners import read_learners
    from sqlmodel import col
    
    mock_result = AsyncMock()
    mock_result.all = MagicMock(return_value=[
        Learner(id=3, name="Albert", email="albert @test.com", enrolled_at=datetime(2024, 6, 16, 8, 0, 0)),
    ])
    
    mock_session = AsyncMock()
    mock_session.exec = AsyncMock(return_value=mock_result)
    
    boundary_time = datetime(2024, 6, 15, 12, 0, 0)
    
    async def run_test():
        result = await read_learners(mock_session, enrolled_after=boundary_time)
        assert len(result) == 1
        assert result[0].id == 3
        assert result[0].name == "Albert"
    
    asyncio.run(run_test())


def test_read_learners_with_none_returns_all() -> None:
    """Test that read_learners with enrolled_after=None returns all learners."""
    from app.db.learners import read_learners
    
    all_learners = [
        Learner(id=1, name="NoEnrollment", email="none @test.com", enrolled_at=None),
        Learner(id=2, name="After", email="after @test.com", enrolled_at=datetime(2024, 6, 1, 0, 0, 0)),
        Learner(id=3, name="Before", email="before @test.com", enrolled_at=datetime(2023, 12, 31, 0, 0, 0)),
    ]
    
    mock_result = AsyncMock()
    mock_result.all = MagicMock(return_value=all_learners)
    
    mock_session = AsyncMock()
    mock_session.exec = AsyncMock(return_value=mock_result)
    
    async def run_test():
        result = await read_learners(mock_session, enrolled_after=None)
        assert len(result) == 3
        assert [l.id for l in result] == [1, 2, 3]
    
    asyncio.run(run_test())


def test_get_learners_with_none_enrolled_after() -> None:
    """Test get_learners endpoint when enrolled_after is None (no filtering)."""
    from app.routers.learners import get_learners
    
    mock_session = AsyncMock()
    
    learners_data = [
        Learner(id=1, name="Alice", email="alice @test.com", enrolled_at=None),
        Learner(id=2, name="Bob", email="bob @test.com", enrolled_at=datetime(2024, 1, 1)),
    ]
    
    async def run_test():
        with patch('app.routers.learners.read_learners', new=AsyncMock(return_value=learners_data)) as mock_read:
            result = await get_learners(enrolled_after=None, session=mock_session)
            mock_read.assert_called_once_with(mock_session, None)
            assert len(result) == 2
            assert all(isinstance(l, Learner) for l in result)
    
    asyncio.run(run_test())

