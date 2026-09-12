import pytest

from smartrouter.cache.semantic import SemanticCache


@pytest.mark.asyncio
async def test_empty_cache() -> None:
    cache = SemanticCache()
    result = await cache.get_cached_response([1.0, 0.0, 0.0])
    assert result is None


@pytest.mark.asyncio
async def test_add_and_get_exact_match() -> None:
    cache = SemanticCache()
    query_embedding = [1.0, 0.0, 0.0]
    response = "This is a cached response."

    await cache.add_to_cache(query_embedding, response)

    result = await cache.get_cached_response(query_embedding)
    assert result == response


@pytest.mark.asyncio
async def test_add_and_get_similar_match() -> None:
    cache = SemanticCache()
    query_embedding = [1.0, 0.0, 0.0]
    similar_embedding = [0.99, 0.1, 0.0]
    response = "This is a cached response."

    await cache.add_to_cache(query_embedding, response)

    result = await cache.get_cached_response(similar_embedding, threshold=0.95)
    assert result == response


@pytest.mark.asyncio
async def test_add_and_get_below_threshold() -> None:
    cache = SemanticCache()
    query_embedding = [1.0, 0.0, 0.0]
    different_embedding = [0.0, 1.0, 0.0]
    response = "This is a cached response."

    await cache.add_to_cache(query_embedding, response)

    result = await cache.get_cached_response(different_embedding, threshold=0.95)
    assert result is None


@pytest.mark.asyncio
async def test_cosine_similarity_edge_cases() -> None:
    cache = SemanticCache()
    assert cache._cosine_similarity([], []) == 0.0
    assert cache._cosine_similarity([1.0, 0.0], [1.0, 0.0, 0.0]) == 0.0
    assert cache._cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0
