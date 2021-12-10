# -*- coding: utf-8 -*-

import decimal

from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import MolliePayment


class MolliePaymentForm(forms.ModelForm):
    amount = forms.DecimalField(min_value=decimal.Decimal(0.01),
                                max_digits=64, decimal_places=2)
    bank_id = forms.ChoiceField(choices=[],
                                label=_('Bank'))

    class Meta:
        model = MolliePayment
