# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2014 Pexego (<http://www.pexego.es>).
#    $Omar Castiñeira Saavedra$
#    $Alejandro Núñez Liz$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

class Usuario(models.Model):
    code = models.CharField(_(u'Codigo'), max_length = 200)
    name = models.CharField(_(u'Usuario'), max_length = 200)
    project = models.CharField(_(u"Proyecto"), max_length = 200, blank=True, null=True)
    pr_name = models.CharField(_(u"Pr Nombre"), max_length = 200, blank=True,
                         null=True)
    task = models.CharField(_(u"Tarea"), max_length = 200, blank=True, null=True)
    start = models.DateTimeField(auto_now_add=True, editable=False)
    end = models.DateTimeField(_(u"Fin"), blank=True, null=True)
    
    def __unicode__(self):
        return self.code
		
    class Meta():
        verbose_name= "usuario"
        verbose_name_plural = "usuarios"
