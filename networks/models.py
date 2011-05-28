#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 Adriano Monteiro Marques
#
# Author: Piotrek Wasilewski <wasilewski.piotrek@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.contrib import admin
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext as _

class Host(models.Model):
    """The single host in the network"""
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    ipv4 = models.IPAddressField(verbose_name=_("IPv4 address"))
    ipv6 = models.CharField(max_length=39, verbose_name=_("IPv6 address"), blank=True)
    
    def __unicode__(self):
        if self.ipv4 and self.ipv6:
            return "<Host '%s' %s, %s>" % (self.name, self.ipv4, self.ipv6)
        else:
            return "<Host '%s' %s>" % (self.name, self.ipv4 or self.ipv6)
                            
    def get_absolute_url(self):
        return reverse('host_detail', args=[self.pk])
    
    def delete(self):
        related = NetworkHost.objects.filter(host=self)
        related.delete()
        super(Host, self).save(*args, **kwargs)

admin.site.register(Host)
    
class Network(models.Model):
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    
    def __unicode__(self):
        return "<Network '%s'>" % self.name
    
    def delete(self):
        related = NetworkHost.objects.filter(network=self)
        related.delete()
        super(Network, self).save(*args, **kwargs)
        
    def get_absolute_url(self):
        return reverse('network_detail', args=[self.pk])
        
    def get_hosts_count(self):
        return NetworkHost.objects.filter(network=self).count()
    
admin.site.register(Network)

class NetworkHost(models.Model):
    network = models.ForeignKey(Network)
    host = models.ForeignKey(Host)

admin.site.register(NetworkHost)
