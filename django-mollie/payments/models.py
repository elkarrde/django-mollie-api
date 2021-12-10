# -*- coding: utf-8 -*-

import json
import re
import uuid

from datetime import datetime
from django.conf import settings
from django.urls import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Amount:
    __value: float = 0
    __currency: str = 'EUR'
    __allowed_currencies = {'AED', 'AUD', 'BGN', 'BRL', 'CAD', 'CHF', 'CZK', 'DKK', 'EUR', 'GBP', 'HKD', 'HRK', 'HUF',
                            'ILS', 'ISK', 'JPY', 'MXN', 'MYR', 'NOK', 'NZD', 'PHP', 'PLN', 'RON', 'RUB', 'SEK', 'SGD',
                            'THB', 'TWD', 'USD', 'ZAR'}

    def __init__(self, amount: float, currency: str = 'EUR'):
        self.value = amount
        self.currency = currency

    @property
    def value(self):
        if not self.__value:
            return None
        return '%.2f' % self.__value

    @property
    def currency(self):
        return self.__currency

    @value.setter
    def value(self, value: float):
        if not value:
            raise ValueError('Value has to exist.')
        if not isinstance(value, (float, int)):
            raise TypeError('Value is not acceptable type.')
        if isinstance(value, bool):
            raise TypeError('Value cannot be Boolean.')
        if value < 0.001:
            raise ValueError('Value out of bounds.')
        self.__value = value

    @currency.setter
    def currency(self, currency: str = 'EUR'):
        if currency not in self.__allowed_currencies:
            raise ValueError('Currency not allowed.')
        self.__currency = currency.upper()

    def json(self):
        return json.dumps({
            'value': self.value,
            'currency': self.currency
        })

    def __repr__(self):
        return f"MollieAmount({self.currency}, {self.value})"

    def __str__(self):
        return f"{self.currency} {self.value}"


class Payment:
    __id: uuid = None
    __amount: Amount
    __description: str
    __redirect_url: str
    __webhook_url: str = None
    __method: str = None
    __metadata: dict = None
    __locale: str = 'en_US'

    __payment_id: str = None
    __payment_metadata = None

    __allowed_methods = {'applepay', 'creditcard', 'banktransfer', 'paypal'}
    __allowed_locales = {'en_US', 'nl_NL', 'nl_BE', 'fr_FR', 'fr_BE', 'de_DE', 'de_AT', 'de_CH', 'es_ES', 'ca_ES',
                         'pt_PT', 'it_IT', 'nb_NO', 'sv_SE', 'fi_FI', 'da_DK', 'is_IS', 'hu_HU', 'pl_PL', 'lv_LV',
                         'lt_LT'}
    __url_regex = r"^https?:\/\/[\w-]{1,}\.[\w]{2,}\/?(?:[\w\.?=&\/-]{1,})?$"

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
        return self.__description

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

    @property
    def locale(self):
        return self.__locale

    @property
    def payment_id(self):
        return self.__payment_id

    @property
    def payment_metadata(self):
        return self.__payment_metadata

    @amount.setter
    def amount(self, amount: Amount):
        self.__amount = amount

    @description.setter
    def description(self, description: str):
        if len(description) < 3:
            raise ValueError('Description needs to be 3 characters or longer.')
        self.__description = description

    @redirect_url.setter
    def redirect_url(self, url: str):
        matches = re.findall(self.__url_regex, url)
        if not matches:
            raise ValueError('Redirect URL is not a valid URL.')
        self.__redirect_url = url

    @webhook_url.setter
    def webhook_url(self, url: str):
        matches = re.findall(self.__url_regex, url)
        if not matches:
            raise ValueError('Webhook URL is not a valid URL.')
        self.__webhook_url = url

    @method.setter
    def method(self, method: str):
        if method not in self.__allowed_methods:
            raise ValueError('Method not available.')
        self.__method = method

    @metadata.setter
    def metadata(self, meta: dict):
        self.__metadata = meta

    @locale.setter
    def locale(self, locale: str):
        if locale not in self.__allowed_locales:
            raise ValueError('Locale not available.')
        self.__locale = locale

    @payment_id.setter
    def payment_id(self, f_id):
        self.__payment_id = f_id

    @payment_metadata.setter
    def payment_metadata(self, f_response):
        self.__payment_metadata = json.loads(f_response)

    def get_object(self):
        output = {
            'amount': json.loads(self.amount.json()),
            'description': self.description,
            'redirectUrl': self.redirect_url
        }
        if self.webhook_url:
            output['webhookUrl'] = self.webhook_url
        if self.method:
            output['method'] = self.method
        if self.locale:
            output['locale'] = self.locale

        f_id = {'felloz_id': self.id.hex}
        if self.metadata:
            output['metadata'] = f_id | self.metadata
        else:
            output['metadata'] = f_id

        if self.payment_id:
            output['payment_id'] = self.payment_id
        if self.payment_metadata:
            output['payment_metadata'] = self.payment_metadata
        # self.id.hex

        return output

    def pretty_json(self):
        return json.dumps(self.get_object(), indent=4)

    def __repr__(self):
        return f"MolliePayment({self.amount}, {self.description}, F#{self.id}, rURL:{self.redirect_url}, whURL:{self.webhook_url})"


class Response:
    __id: str
    __felloz_id: str
    __amount: Amount
    __description: str = None
    __method: str = None
    __status: str = None
    __resource: str = None
    __mode: str = None
    __metadata: dict = None
    __payment_metadata: dict
    __checkout_url: str = None
    __dashboard_url: str = None
    __expired_at = None

    def __init__(self, response):
        self.payment_metadata = response
        self.__id = response['id']
        self.__felloz_id = response['metadata']['felloz_id']
        self.__amount = Amount(
            float(response['amount']['value']),
            response['amount']['currency']
        )
        self.status = response['status']

        self.__description = response['description']
        self.__method = response['method']
        self.__resource = response['resource']
        self.__mode = response['mode']
        self.__metadata = response['metadata']
        self.__checkout_data = response['_links']['checkout']
        self.__dashboard_data = response['_links']['dashboard']
        self.__expires_at = datetime.fromisoformat(response['expiresAt'])
        self.__checkout_url = response['_links']['checkout']['href']
        self.__dashboard_url = response['_links']['dashboard']['href']

    @property
    def id(self):
        return self.__id

    @property
    def felloz_id(self):
        return self.__felloz_id

    @property
    def amount(self):
        return self.__amount

    @property
    def description(self):
        return self.__description

    @property
    def method(self):
        return self.__method

    @property
    def status(self):
        return self.__status

    @property
    def resource(self):
        return self.__resource

    @property
    def mode(self):
        return self.__mode

    @property
    def metadata(self):
        return self.__metadata

    @property
    def payment_metadata(self):
        return self.__payment_metadata

    @property
    def expires_at(self):
        return self.__expires_at

    @property
    def checkout_url(self):
        return self.__checkout_url

    @property
    def dashboard_url(self):
        return self.__dashboard_url

    @status.setter
    def status(self, status: str):
        self.__status = status

    @payment_metadata.setter
    def payment_metadata(self, data: dict):
        self.__payment_metadata = data

    def get_object(self):
        output = {
            'id': self.id,
            'felloz_id': self.felloz_id,
            'amount': self.amount,
            'description': self.description,
            'method': self.method,
            'status': self.status,
            'resource': self.resource,
            'mode': self.mode,
            'metadata': self.metadata,
            'expires_at': self.expires_at,
            'checkout_url': self.checkout_url,
            'dashboard_url': self.dashboard_url,
            'payment_metadata': self.payment_metadata,
        }
        return output

    def __repr__(self):
        return f"MollieResponse(#{self.id}, F#{self.felloz_id}, {self.amount}, ST:{self.status}, chkURL:{self.checkout_url})"


class Pricing:
    __id: int = None
    __description: str = None
    __fee_region: str = None
    __fixed_fee_value: float = None
    __fixed_fee_currency: str = None
    __fixed_fee: Amount = None
    __variable_fee: float = None

    def __init__(self, input_id, input_object):
        self.__id = input_id
        self.__description = input_object['description']
        self.__fee_region = input_object['feeRegion']
        self.__fixed_fee_currency = input_object['fixed']['currency']
        self.__fixed_fee_value = float(input_object['fixed']['value'])
        self.__fixed_fee = Amount(self.fixed_fee_value, self.fixed_fee_currency)
        self.__variable_fee = float(input_object['variable'])

    @property
    def id(self):
        return self.__id

    @property
    def description(self):
        return self.__description

    @property
    def fee_region(self):
        return self.__fee_region

    @property
    def fixed_fee_currency(self):
        return self.__fixed_fee_currency

    @property
    def fixed_fee_value(self):
        return self.__fixed_fee_value

    @property
    def fixed_fee(self):
        return self.__fixed_fee

    @property
    def variable_fee(self):
        return self.__variable_fee

    def fixed_fee_str(self):
        return f"{self.fixed_fee_currency} {self.fixed_fee_value}"

    def variable_fee_str(self):
        return f"{self.__variable_fee}%"

    def get_object(self, extended=False):
        output = {
            'id': self.__id,
            'description': self.description,
            'fee_region': self.fee_region,
            'fixed_fee_value': self.fixed_fee_value,
            'fixed_fee_currency': self.fixed_fee_currency,
            'variable_fee': self.variable_fee,
            'variable_fee_calc': 1 + self.variable_fee / 100
        }
        if extended:
            output['fixed_fee_str'] = self.fixed_fee_str()
            output['variable_fee_str'] = self.variable_fee_str()
        return output

    def __repr__(self):
        return f"MolliePricing({self.fee_region}, fee:{self.fixed_fee} + {self.variable_fee}%)"


class Method:
    __id: str = None
    __status: str = None
    __resource: str = None
    __description: str = None
    __amount_max: Amount = None
    __amount_min: Amount = None
    __amount_currency: str = None
    __max_amount: float = None
    __min_amount: float = None
    __pricing: [Pricing] = []
    __image_svg_url: str = None
    __image_png_url: str = None
    __image_png2x_url: str = None

    def __init__(self, input_object):
        self.__id = input_object['id']
        self.__status = input_object['status']
        self.__resource = input_object['resource']
        self.__description = input_object['description']
        self.__min_amount = float(input_object['minimumAmount']['value'])
        self.__max_amount = float(input_object['maximumAmount']['value'])
        self.__amount_currency = input_object['minimumAmount']['currency']
        self.__amount_min = Amount(self.amount_min, self.amount_currency)
        self.__amount_max = Amount(self.amount_max, self.amount_currency)
        try:
            for idx, itm in enumerate(input_object['pricing']):
                self.__pricing.append(Pricing(idx, itm))
        except AttributeError:
            pass
        self.__image_svg_url = input_object['image']['svg']
        self.__image_png_url = input_object['image']['size1x']
        self.__image_png2x_url = input_object['image']['size2x']

    @property
    def amount_min(self):
        return self.__min_amount

    @property
    def amount_max(self):
        return self.__max_amount

    @property
    def amount_currency(self):
        return self.__amount_currency

    def get_object(self, include_pricing=False, include_images=False):
        output = {
            'id': self.__id,
            'status': self.__status,
            'description': self.__description,
            'resource': self.__resource,
            'minimum_amount': self.__amount_min,
            'maximum_amount': self.__amount_max
        }
        if include_pricing:
            output['pricing'] = self.__pricing
        if include_images:
            output['image_png'] = self.__image_png_url
            output['image_png2x'] = self.__image_png2x_url
            output['image_svg'] = self.__image_svg_url
        return output

    def __repr__(self):
        return f"MollieMethod({self.__id}/{self.__description}, {self.__status}, <{self.__amount_min}, {self.__amount_max}>, P:{self.__pricing})"


class Methods:
    __method_list: [Method] = []

    def __init__(self, input_list):
        # TODO: check if arrays exists, once, maybe
        count = len(input_list['_embedded']['methods'])
        if count:
            for idx, itm in enumerate(input_list['_embedded']['methods']):
                self.__method_list.append(Method(itm))
        else:
            ValueError('No Methods detected')

    def get_list(self):
        return self.__method_list

    def __repr__(self):
        return f"MollieMethods(C:{len(self.__method_list)})"


class MolliePayment(models.Model):
    transaction_id = models.CharField(_('Transaction ID'), max_length=255)
    amount = models.DecimalField(_('Amount'), max_digits=64, decimal_places=2)
    bank_id = models.CharField(_('Bank ID'), max_length=4,
                               # choices=get_mollie_bank_choices(show_all_banks=True),
                               default='')
    description = models.CharField(_('Description'), max_length=29)
    timestamp = models.DateTimeField(_('Timestamp'), auto_now_add=True)
    consumer_account = models.CharField(_('Consumer account'), max_length=255, blank=True)
    consumer_name = models.CharField(_('Consumer name'), max_length=255, blank=True)
    consumer_city = models.CharField(_('Consumer city'), max_length=255, blank=True)

