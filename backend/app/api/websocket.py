from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.services.websocket_manager import manager
from app.services.notification import get_unread_count
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/notifications")
async def websocket_notifications(websocket: WebSocket, db: Session = Depends(get_db)):
    # Validate token from cookie
    token = websocket.cookies.get("access_token")
    if not token:
        await websocket.close(code=1008)
        return

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        await websocket.close(code=1008)
        return

    user_id = payload["sub"]

    await manager.connect(websocket, user_id)

    try:
        # Send initial unread notifications count
        unread_count = get_unread_count(db, user_id)
        await websocket.send_json(
            {"type": "connection.ready", "version": 1, "unread_count": unread_count}
        )

        while True:
            # Keep alive
            _ = await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket, user_id)
