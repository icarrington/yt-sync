from django.urls import re_path
from syncapp.routing import websocket_urlpatterns as app_ws
websocket_urlpatterns = [*app_ws]
