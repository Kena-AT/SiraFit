import json
import logging
import asyncio
from typing import Any, Dict
import redis.asyncio as redis
from app.core.config import settings
from app.schemas.realtime import RealtimeEvent
from app.services.websocket_manager import manager as ws_manager

logger = logging.getLogger(__name__)

# Single Redis client instance for publishing
_redis_client = None
_subscriber_task = None
_pubsub = None

async def init_redis():
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            logger.info("Realtime Redis client initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Realtime Redis client: {e}")

async def close_redis():
    global _redis_client, _subscriber_task, _pubsub
    
    if _pubsub:
        await _pubsub.close()
    
    if _subscriber_task:
        _subscriber_task.cancel()
        try:
            await _subscriber_task
        except asyncio.CancelledError:
            pass
            
    if _redis_client:
        await _redis_client.aclose()
        logger.info("Realtime Redis client closed.")
        
    _redis_client = None

async def publish_event(user_id: str, event_type: str, payload: Dict[str, Any]):
    """Publish a realtime event to Redis."""
    if not _redis_client:
        # Silently fail if redis isn't configured/connected. Realtime delivery is best effort.
        logger.warning(f"Skipping publish_event {event_type} - Redis not initialized")
        return
        
    try:
        event = RealtimeEvent(type=event_type, payload=payload)
        channel = f"realtime:user:{user_id}"
        await _redis_client.publish(channel, event.model_dump_json())
    except Exception as e:
        logger.error(f"Failed to publish event {event_type} to user {user_id}: {e}")

async def run_subscriber():
    """Background task to subscribe to Redis and push to local WebSocket manager."""
    global _pubsub
    if not _redis_client:
        logger.warning("Cannot start subscriber: Redis not initialized")
        return
        
    while True:
        try:
            _pubsub = _redis_client.pubsub()
            await _pubsub.psubscribe("realtime:user:*")
            logger.info("Redis subscriber listening for realtime events.")
            
            async for message in _pubsub.listen():
                if message["type"] == "pmessage":
                    channel = message["channel"]
                    user_id = channel.split(":")[-1]
                    try:
                        data = json.loads(message["data"])
                        await ws_manager.broadcast_to_user(user_id, data)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse event data from Redis: {message['data']}")
        
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Redis subscriber error: {e}. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)
