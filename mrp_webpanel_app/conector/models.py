# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

class Usuario(models.Model):
    code = models.CharField(_(u'Codigo'), max_length = 200)
    name = models.CharField(_(u'Usuario'), max_length = 200)
    project = models.CharField(_(u"Proyecto"), max_length = 200, blank=True, null=True)
    start = models.DateTimeField(auto_now_add=True, editable=False)
    end = models.DateTimeField(_(u"Fin"), blank=True, null=True)
    
    def __unicode__(self):
        return self.code
		
    class Meta():
        verbose_name= "usuario"
        verbose_name_plural = "usuarios"
