from firebase_admin import messaging
from users.models import FCMToken

def send_push_notification(users, title, body, data=None):
    tokens = FCMToken.objects.filter(
        user__in=users
    ).values_list("token", flat=True)

    if not tokens:
        return

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},
        tokens=list(tokens),
    )

    messaging.send_multicast(message)
