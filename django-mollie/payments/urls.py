# from . import views, webhook
from django.urls import path
from .views import CreatePayment, PaymentConfirmed, PaymentFailed, PaymentUpdate


app_name = "mollie_integration"
urlpatterns = [
    path('payment_create', view=CreatePayment, name='payment_create'),
    path('payment_confirmed/<uuid:id>', view=PaymentConfirmed, name='payment_confirmed'),
    path('payment_failed/<uuid:id>', view=PaymentFailed, name='payment_failed'),
    path('payment_update/<str:id>', view=PaymentUpdate, name='payment_update')  # webhook
]
