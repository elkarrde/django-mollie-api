# -*- coding: utf-8 -*-

import json
import re
import uuid

from django.conf import settings
from django.urls import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Amount:
    __value: float = 0.00
    __currency: str = 'EUR'
    __allowed_currencies = {'AED', 'AUD', 'BGN', 'BRL', 'CAD', 'CHF', 'CZK', 'DKK', 'EUR', 'GBP', 'HKD', 'HRK', 'HUF',
                            'ILS', 'ISK', 'JPY', 'MXN', 'MYR', 'NOK', 'NZD', 'PHP', 'PLN', 'RON', 'RUB', 'SEK', 'SGD',
                            'THB', 'TWD', 'USD', 'ZAR'}

    def __init__(self, amount, currency):
        self.__value = amount
        self.__currency = currency

    @property
    def value(self):
        return '%.2f' % self.__value

    @property
    def currency(self):
        return self.__currency

    @value.setter
    def value(self, value: float):
        if value < 1:
            raise ValueError(_('Value too small.'))
        self.__value = value

    @currency.setter
    def currency(self, currency: str = 'EUR'):
        if currency not in self.__allowed_currencies:
            raise ValueError(_('Currency not allowed.'))
        self.__currency = currency.upper()


class Payment:
    __id: uuid
    __amount: Amount
    __description: str = ''
    __redirect_url: str = ''
    __webhook_url: str = ''
    __method: str = ''
    __metadata: json
    __allowed_methods = {'applepay', 'creditcard', 'banktransfer', 'paypal'}
    __url_regex = r"^https?:\/\/[\w-]{1,}\.[\w]{2,}\/?(?:[\w\.?=&]{1,})?$"

    def __init__(self):
        self.__id = uuid.uuid4()

    @property
    def id(self):
        return self.__id

    @property
    def amount(self):
        return self.__amount

    @property
    def description(self):
        return self.__amount

    @property
    def redirect_url(self):
        return self.__redirect_url

    @property
    def webhook_url(self):
        return self.__webhook_url

    @property
    def method(self):
        return self.__method

    @property
    def metadata(self):
        return self.__metadata

    @id.setter
    def id(self, val):
        raise ValueError(_('Payment ID can not be changed.'))

    @amount.setter
    def amount(self, amount: Amount):
        self.__amount = amount

    @description.setter
    def description(self, description: str):
        if len(description) < 3:
            raise ValueError(_('Description needs to be 3 letters or longer.'))
        self.__description = description

    @redirect_url.setter
    def redirect_url(self, url: str):
        matches = re.findall(self.__url_regex, url)
        if not matches:
            raise ValueError(_('Redirect URL is not an URL.'))
        self.__redirect_url = url

    @webhook_url.setter
    def webhook_url(self, url: str):
        matches = re.findall(self.__url_regex, url)
        if not matches:
            raise ValueError(_('Webhook URL is not an URL.'))
        self.__webhook_url = url

    @method.setter
    def method(self, method: str):
        if method not in self.__allowed_methods:
            raise ValueError(_('Method not available.'))
        self.__method = method

    @metadata.setter
    def metadata(self, meta: json):
        self.__metadata = meta


class MolliePayment(models.Model):
    transaction_id = models.CharField(_('Transaction ID'), max_length=255)
    amount = models.DecimalField(_('Amount'), max_digits=64, decimal_places=2)
    bank_id = models.CharField(_('Bank ID'), max_length=4,
                               choices=get_mollie_bank_choices(show_all_banks=True),
                               default='')
    description = models.CharField(_('Description'), max_length=29)
    timestamp = models.DateTimeField(_('Timestamp'), auto_now_add=True)
    consumer_account = models.CharField(_('Consumer account'), max_length=255, blank=True)
    consumer_name = models.CharField(_('Consumer name'), max_length=255, blank=True)
    consumer_city = models.CharField(_('Consumer city'), max_length=255, blank=True)

    class Meta:
        abstract = True
        verbose_name = _('Django Mollie payment')

    def get_order_url(self):
        """Sets up a payment with Mollie.nl and returns an order URL."""
        if settings.MOLLIE_REVERSE_URLS:
            reporturl = settings.MOLLIE_IMPLEMENTING_SITE_URL + reverse(settings.MOLLIE_REPORT_URL)
            returnurl = settings.MOLLIE_IMPLEMENTING_SITE_URL + reverse(settings.MOLLIE_RETURN_URL)
        else:
            reporturl = settings.MOLLIE_REPORT_URL
            returnurl = settings.MOLLIE_RETURN_URL
        request_dict = dict(
            a='fetch',
            amount=int(self.amount * 100),
            bank_id=self.bank_id,
            description=self.description,
            partnerid=settings.MOLLIE_PARTNER_ID,
            reporturl=reporturl,
            returnurl=returnurl
        )
        if settings.MOLLIE_PROFILE_KEY:
            request_dict.update(dict(
                profile_key=settings.MOLLIE_PROFILE_KEY
            ))
        parsed_xml = _get_mollie_xml(request_dict)
        order = parsed_xml.find('order')
        order_url = order.findtext('URL')
        self.transaction_id = order.findtext('transaction_id')
        self.save()
        return order_url

    fetch = get_order_url

    def is_paid(self):
        """Checks whether a payment has been made successfully."""
        request_dict = dict(
            a='check',
            partnerid=settings.MOLLIE_PARTNER_ID,
            transaction_id=self.transaction_id
        )
        parsed_xml = _get_mollie_xml(request_dict)
        order = parsed_xml.find('order')
        consumer = order.find('consumer')
        if consumer:
            self.consumer_account = consumer.findtext('consumerAccount')
            self.consumer_city = consumer.findtext('consumerCity')
            self.consumer_name = consumer.findtext('consumerName')
        if order.findtext('payed') == 'true':
            return True
        return False

    check = is_paid

    @property
    def bank_name(self):
        return self.get_bank_id_display()

    def __unicode__(self):
        return u'Mollie Payment ID: %d' % self.id
