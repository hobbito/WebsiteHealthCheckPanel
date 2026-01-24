import asyncio
import json
from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from app.domains.auth.models import User
from app.core.security import get_current_user
from app.core.event_bus import event_bus

router = APIRouter()


@router.get("/updates")
async def stream_updates(current_user: User = Depends(get_current_user)):
    """
    Server-Sent Events endpoint for real-time check updates.

    Streams events for the current user's organization.
    """

    async def event_generator():
        # Subscribe to organization's channel
        channel = f'org:{current_user.organization_id}'
        queue = event_bus.subscribe(channel)

        try:
            # Send initial connection event
            yield {
                "event": "connected",
                "data": json.dumps({
                    "message": "Connected to real-time updates",
                    "organization_id": current_user.organization_id
                })
            }

            # Stream events
            while True:
                # Wait for next event (blocks until available)
                data = await queue.get()

                yield {
                    "event": data.get("type", "update"),
                    "data": json.dumps(data)
                }

        except asyncio.CancelledError:
            # Client disconnected
            event_bus.unsubscribe(channel, queue)
            raise

    return EventSourceResponse(event_generator())
