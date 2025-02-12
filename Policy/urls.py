from django.views.generic import TemplateView
from django.urls import path

urlpatterns = [
    path("privacy/", TemplateView.as_view(template_name="privacy.html")),
    path("service/", TemplateView.as_view(template_name="service.html")),
]