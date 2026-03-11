from django.urls import path
from . import views

app_name = "plants"

urlpatterns = [
    path("api/v1/plants/", views.plant_list_view, name="plant_list"),
    path("api/v1/plants/<uuid:plant_id>/", views.plant_detail_view, name="plant_detail"),
]
