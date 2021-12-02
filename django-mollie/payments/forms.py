# -*- coding: utf-8 -*-

import decimal

from django import forms
from django.utils.translation import ugettext_lazy as _

from .helpers import get_mollie_bank_choices
from .models import MolliePayment
from .settings import MOLLIE_MIN_AMOUNT


class MolliePaymentForm(forms.ModelForm):
    amount = forms.DecimalField(min_value=decimal.Decimal(MOLLIE_MIN_AMOUNT),
                                max_digits=64, decimal_places=2)
    bank_id = forms.ChoiceField(choices=get_mollie_bank_choices(),
                                label=_('Bank'))

    class Meta:
        model = MolliePayment
