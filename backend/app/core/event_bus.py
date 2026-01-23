import asyncio
from typing import Dict, Set, Any
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """
    In-memory pub/sub event bus for SSE (no Redis needed).
    Perfect for single-instance DigitalOcean Apps deployment.

    If horizontal scaling is needed, migrate to PostgreSQL LISTEN/NOTIFY.
    """

    def __init__(self):
        self._subscribers: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def publish(self, channel: str, data: Dict[str, Any]):
        """
        Publish event to all subscribers of channel.

        Args:
            channel: Channel name (e.g., "org:123", "check_result")
            data: Event data to publish
        """
        async with self._lock:
            if channel in self._subscribers:
                # Send to all subscribers on this channel
                dead_queues = set()
                for queue in self._subscribers[channel]:
                    try:
                        await queue.put(data)
                    except Exception as e:
                        logger.error(f"Error publishing to queue on channel {channel}: {e}")
                        dead_queues.add(queue)

                # Clean up dead queues
                if dead_queues:
                    self._subscribers[channel] -= dead_queues

                logger.debug(f"Published to channel '{channel}': {len(self._subscribers[channel])} subscribers")

    def subscribe(self, channel: str) -> asyncio.Queue:
        """
        Subscribe to channel, returns queue for receiving events.

        Args:
            channel: Channel name to subscribe to

        Returns:
            asyncio.Queue that will receive events
        """
        queue = asyncio.Queue(maxsize=100)  # Prevent memory issues with slow consumers
        self._subscribers[channel].add(queue)
        logger.debug(f"New subscriber to channel '{channel}'. Total: {len(self._subscribers[channel])}")
        return queue

    def unsubscribe(self, channel: str, queue: asyncio.Queue):
        """
        Unsubscribe from channel.

        Args:
            channel: Channel name
            queue: Queue to remove from subscribers
        """
        if channel in self._subscribers:
            self._subscribers[channel].discard(queue)
            logger.debug(f"Unsubscribed from channel '{channel}'. Remaining: {len(self._subscribers[channel])}")

            # Clean up empty channels
            if not self._subscribers[channel]:
                del self._subscribers[channel]

    def get_subscriber_count(self, channel: str) -> int:
        """Get number of subscribers for a channel"""
        return len(self._subscribers.get(channel, set()))

    def get_all_channels(self) -> list[str]:
        """Get list of all active channels"""
        return list(self._subscribers.keys())


# Global event bus instance
event_bus = EventBus()
