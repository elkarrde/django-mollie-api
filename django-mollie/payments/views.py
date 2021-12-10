import logging
import time
# from webapp.donation_project.models.project import Project
# from flask import Response
# from rest_framework import status
import flask
from django.views.generic import TemplateView
import models
from .helpers import init_client

log = logging.getLogger(__name__)


class CreatePayment(TemplateView):
    def post(self, request):
        print('CPX', request)

        mp = models.Payment()
        # print('New MolliePayment ID:', mp.id)
        mp.amount = models.Amount(100, 'HRK')
        d_id = int(time.time())
        mp.description = 'Donation #' + str(d_id) + ', ' + mp.amount.currency + ' ' + mp.amount.value
        # print('MP Amount:', mp.amount.currency, mp.amount.value)
        # print('MP Data:', mp.description)
        mp.redirect_url = 'http://felloz.com/donation-confirm/734'
        mp.webhook_url = 'https://api.felloz.com/v1/webhook/donation&id=734'
        mp.method = 'creditcard'
        our_data = {
            'donation_id': 734,
            'user_id': 1148,
            'project_id': 7
        }
        mp.metadata = our_data

        client = init_client()
        raw_payment = client.payments.create(mp.get_object())
        payment_response = models.Response(raw_payment)
        print('CPX-R', payment_response)
        return flask.redirect(payment_response.checkout_url)


class PaymentConfirmed(TemplateView):
    def post(self, request):
        print('CFX', request)
        return 'IsConfirmed'


class PaymentFailed(TemplateView):
    def post(self, request):
        print('FLX', request)
        return 'IsFailed'


class PaymentUpdate(TemplateView):
    def post(self, request):
        print('UPDX', request)
        return 'GotUpdate'
