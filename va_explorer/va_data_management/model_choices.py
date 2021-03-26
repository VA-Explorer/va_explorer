from django.db import models
from django.utils.translation import gettext_lazy as _


class AgeGroup(models.TextChoices):
    NEONATE = 'neonate', _('Neonate')
    CHILD = 'child', _('Child')
    ADULT = 'adult', _('Adult')


class YesNoSimilar(models.TextChoices):
    YES = 'yes', _('Yes')
    NO = 'no', _('No')
    DONT_KNOW = 'dk', _('Doesn\'t know')
    REFUSE = 'ref', _('Refused to answer')
