from transport.models import Notification

def notifications_processor(request):
    if not request.user.is_authenticated:
        return {}
    try:
        unread = Notification.objects.filter(is_read=False)
        return {
            "unread_notifications_count": unread.count(),
            "recent_notifications": Notification.objects.all()[:6],
        }
    except Exception:
        return {}
