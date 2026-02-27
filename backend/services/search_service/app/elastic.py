from elasticsearch import AsyncElasticsearch

from shared.utils import setup_logger
from .config import settings

logger = setup_logger(__name__)

_es_client: AsyncElasticsearch | None = None

SHOWS_INDEX = "shows"
VENUES_INDEX = "venues"


async def init_es():
    """Initialize the async Elasticsearch client."""
    global _es_client
    _es_client = AsyncElasticsearch(settings.ELASTICSEARCH_URL)
    info = await _es_client.info()
    logger.info("Connected to Elasticsearch %s", info["version"]["number"])


async def close_es():
    """Close the Elasticsearch client connection."""
    global _es_client
    if _es_client:
        await _es_client.close()
        _es_client = None
        logger.info("Elasticsearch connection closed")


def get_es() -> AsyncElasticsearch:
    """Return the active ES client. Raises if not initialized."""
    if _es_client is None:
        raise RuntimeError("Elasticsearch client not initialized")
    return _es_client


async def search_shows(
    query: str,
    city: str | None = None,
    limit: int = 8,
) -> list[dict]:
    """Search shows using Elasticsearch multi_match with fuzziness."""
    es = get_es()

    must_clause = {
        "multi_match": {
            "query": query,
            "fields": ["title^3", "description", "language"],
            "fuzziness": "AUTO",
            "type": "best_fields",
        }
    }

    filter_clauses = [{"term": {"status": "ACTIVE"}}]

    body = {
        "query": {
            "bool": {
                "must": [must_clause],
                "filter": filter_clauses,
            }
        },
        "size": limit,
        "_source": ["title", "duration_minutes", "price", "language", "rating"],
    }

    resp = await es.search(index=SHOWS_INDEX, body=body)
    results = []
    for hit in resp["hits"]["hits"]:
        doc = hit["_source"]
        doc["id"] = int(hit["_id"])
        results.append(doc)
    return results


async def search_venues(
    query: str,
    city: str | None = None,
    limit: int = 8,
) -> list[dict]:
    """Search venues using Elasticsearch multi_match with fuzziness."""
    es = get_es()

    must_clause = {
        "multi_match": {
            "query": query,
            "fields": ["name^3", "location", "city"],
            "fuzziness": "AUTO",
            "type": "best_fields",
        }
    }

    filter_clauses = [{"term": {"status": "ACTIVE"}}]
    if city:
        filter_clauses.append({"term": {"city.keyword": city}})

    body = {
        "query": {
            "bool": {
                "must": [must_clause],
                "filter": filter_clauses,
            }
        },
        "size": limit,
        "_source": ["name", "location", "city", "opening_time", "closing_time"],
    }

    resp = await es.search(index=VENUES_INDEX, body=body)
    results = []
    for hit in resp["hits"]["hits"]:
        doc = hit["_source"]
        doc["id"] = int(hit["_id"])
        results.append(doc)
    return results


async def get_cities(limit: int = 100) -> list[str]:
    """Get distinct active venue cities using a terms aggregation."""
    es = get_es()

    body = {
        "size": 0,
        "query": {"term": {"status": "ACTIVE"}},
        "aggs": {
            "unique_cities": {
                "terms": {
                    "field": "city.keyword",
                    "size": limit,
                    "order": {"_key": "asc"},
                }
            }
        },
    }

    resp = await es.search(index=VENUES_INDEX, body=body)
    buckets = resp.get("aggregations", {}).get("unique_cities", {}).get("buckets", [])
    return [bucket["key"] for bucket in buckets if bucket["key"]]


async def index_document(index: str, doc_id: int, body: dict):
    """Index (upsert) a single document into ES."""
    es = get_es()
    await es.index(index=index, id=str(doc_id), body=body)
    logger.info("Indexed document %s in '%s'", doc_id, index)


async def delete_document(index: str, doc_id: int):
    """Delete a single document from ES. Ignores 404."""
    es = get_es()
    await es.delete(index=index, id=str(doc_id), ignore=[404])
    logger.info("Deleted document %s from '%s'", doc_id, index)

