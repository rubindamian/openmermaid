from django.urls import path

from studio.api import diagram_collection, diagram_detail, diagram_save, me
from studio.public import public_png

urlpatterns = [
    path("api/me/", me, name="me"),
    path("api/diagrams/", diagram_collection, name="diagram-collection"),
    path("api/diagrams/<str:diagram_id>/save/", diagram_save, name="diagram-save"),
    path("api/diagrams/<str:diagram_id>/", diagram_detail, name="diagram-detail"),
    path("p/<str:token>.png", public_png, name="public-png"),
]
