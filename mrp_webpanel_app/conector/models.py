# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

class Usuario(models.Model):
    code = models.CharField(_(u'codigo'), max_length = 200)
    name = models.CharField(_(u'usuario'), max_length = 200)
    created = models.DateTimeField(auto_now_add=True, editable=False)
	
    def __unicode__(self):
        return self.code
		
    class Meta():
        verbose_name= "usuario"
        verbose_name_plural = "usuarios"
