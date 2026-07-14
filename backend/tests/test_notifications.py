from app.services.notification import (
    create_notification,
    get_notifications,
    mark_as_read,
    mark_all_as_read,
    get_unread_count,
)
from app.models.notification import Notification

def test_create_notification(test_user, db):
    """Test creating a notification."""
    notification = create_notification(
        db=db,
        user_id=test_user.id,
        title="Test Notification",
        body="This is a test notification",
        kind="alert"
    )
    
    assert notification is not None
    assert notification.id is not None
    assert notification.user_id == test_user.id
    assert notification.title == "Test Notification"
    assert notification.body == "This is a test notification"
    assert notification.kind == "alert"
    assert notification.status == "unread"
    assert notification.read_at is None

def test_get_notifications(test_user, db):
    """Test getting notifications with pagination."""
    # Create multiple notifications
    for i in range(5):
        create_notification(
            db=db,
            user_id=test_user.id,
            title=f"Notification {i}",
            body=f"Body {i}",
            kind="system_event"
        )
    
    # Get all
    notifications, total = get_notifications(db, test_user.id, skip=0, limit=10)
    assert total == 5
    assert len(notifications) == 5
    
    # Get with pagination
    notifications, total = get_notifications(db, test_user.id, skip=2, limit=2)
    assert total == 5
    assert len(notifications) == 2
    
    # Filter by status
    notifications, total = get_notifications(db, test_user.id, status="unread")
    assert total == 5
    assert len(notifications) == 5

def test_mark_as_read(test_user, db):
    """Test marking a notification as read."""
    notification = create_notification(
        db=db,
        user_id=test_user.id,
        title="Test",
        body="Test body",
        kind="alert"
    )
    
    # Mark as read
    updated = mark_as_read(db, test_user.id, notification.id)
    
    assert updated is not None
    assert updated.status == "read"
    assert updated.read_at is not None
    
    # Verify it's read in the database
    db.refresh(notification)
    assert notification.status == "read"

def test_mark_all_as_read(test_user, db):
    """Test marking all notifications as read."""
    # Create multiple notifications
    for i in range(3):
        create_notification(
            db=db,
            user_id=test_user.id,
            title=f"Test {i}",
            body=f"Body {i}",
            kind="system_event"
        )
    
    # Mark all as read
    count = mark_all_as_read(db, test_user.id)
    
    assert count == 3
    
    # Verify all are read
    notifications, total = get_notifications(db, test_user.id, status="read")
    assert total == 3

def test_get_unread_count(test_user, db):
    """Test getting unread notification count."""
    # Create some notifications
    for i in range(3):
        create_notification(
            db=db,
            user_id=test_user.id,
            title=f"Test {i}",
            body=f"Body {i}",
            kind="system_event"
        )
    
    count = get_unread_count(db, test_user.id)
    assert count == 3
    
    # Mark one as read
    notification = db.query(Notification).filter(Notification.user_id == test_user.id).first()
    mark_as_read(db, test_user.id, notification.id)
    
    count = get_unread_count(db, test_user.id)
    assert count == 2