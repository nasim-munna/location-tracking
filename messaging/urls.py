from django.urls import path
from .views import (
    SendMessageAPIView,
    InboxAPIView,
    ConversationAPIView,
    MarkMessageReadAPIView,
    UnreadCountAPIView,
    MarkConversationReadAPIView,
    DivisionBroadcastAPIView,
)

urlpatterns = [
    path("send/", SendMessageAPIView.as_view()),
    path("inbox/", InboxAPIView.as_view()),
    path("conversation/<uuid:user_id>/", ConversationAPIView.as_view()),
    path("read/<int:message_id>/",MarkMessageReadAPIView.as_view(),name="message-read"),
    path("unread-count/",UnreadCountAPIView.as_view(),name="unread-count"),
    path("conversation/<uuid:user_id>/read/",MarkConversationReadAPIView.as_view(),name="conversation-read"),
    path("broadcast/division/",DivisionBroadcastAPIView.as_view(),name="division-broadcast"),
]
