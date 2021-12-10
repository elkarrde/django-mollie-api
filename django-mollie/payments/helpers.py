# -*- coding: utf-8 -*-

from mollie.api.client import Client
from .settings import FDA_MOLLIE_API_KEY
from django.utils.translation import ugettext_lazy as _


def init_client():
    mollie_client = Client()
    mollie_client.set_api_key(FDA_MOLLIE_API_KEY)
    return mollie_client
