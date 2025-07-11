# classroom/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/storybook/<int:storybook_id>/', consumers.SceneProgressConsumer.as_asgi()),
]
