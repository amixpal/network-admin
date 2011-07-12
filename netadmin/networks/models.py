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
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext as _

from netadmin.permissions.models import ObjectPermission


class NetworkObject(models.Model):
    """
    Abstract model class for objects like host or network.
    Every object belongs to specified user
    """
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, blank=False, null=False)
    
    def __unicode__(self):
        return self.name
    
    def get_short_description(self, word_limit=15, char_limit=150):
        words = self.description.split()
        if len(words) > word_limit:
            return '%s...' % ' '.join(words[:word_limit])
        elif len(self.description) > char_limit:
            return '%s...' % self.description[:char_limit]
        else:
            return self.description
    short_description = property(get_short_description)
    
    def _sharing_users(self):
        ct = ContentType.objects.get_for_model(self.__class__)
        perms = ObjectPermission.objects.filter(content_type=ct,
                                                object_id=self.pk)
        return [(perm.user, perm.edit) for perm in perms]
    sharing_users = property(_sharing_users)
    
    class Meta:
        abstract = True

class Host(NetworkObject):
    """The single host in the network"""
    ipv4 = models.IPAddressField(verbose_name=_("IPv4 address"))
    ipv6 = models.CharField(max_length=39, verbose_name=_("IPv6 address"), 
                            blank=True)
                            
    def get_absolute_url(self):
        return reverse('host_detail', args=[self.pk])
    
    def delete(self, *args, **kwargs):
        # delete all events related to this host
        events = self.events
        events.delete()
        
        # delete network-host relations
        related = NetworkHost.objects.filter(host=self)
        related.delete()
        
        super(Host, self).delete(*args, **kwargs)
        
    def _events(self):
        return self.event_set.all().order_by('-timestamp')
    events = property(_events)
    
    def _latest_event(self):
        events = self.events.order_by('-timestamp')
        return events[0] if events else None
    latest_event = property(_latest_event)
    
    def _networks(self):
        nethost = self.networkhost_set.all().only('id')
        nets = [nh.network.pk for nh in nethost]
        return Network.objects.filter(pk__in=nets)
    network = property(_networks)
    
    def in_network(self, network):
        try:
            nh = self.networkhost_set.get(network=network)
        except NetworkHost.DoesNotExist:
            return False
        return True

class Network(NetworkObject):
    
    def get_absolute_url(self):
        return reverse('network_detail', args=[self.pk])
    
    def delete(self, *args, **kwargs):
        related = NetworkHost.objects.filter(network=self)
        related.delete()
        super(Network, self).delete(*args, **kwargs)
    
    def _hosts(self):
        """Returns all hosts in the network"""
        rels = NetworkHost.objects.filter(network=self)
        hosts_ids = [rel.host.pk for rel in rels]
        return Host.objects.filter(pk__in=hosts_ids)
    hosts = property(_hosts)
    
    def _hosts_count(self):
        return self.hosts.count()
    hosts_count = property(_hosts_count)
    
    def has_host(self, host):
        return True if host in self.hosts else False
    
    def _events(self):
        from netadmin.events.models import Event
        events = Event.objects.filter(source_host__in=list(self.hosts))
        return events.order_by('-timestamp') 
    events = property(_events)
    
    def _latest_event(self):
        events = self.events.order_by('-timestamp')
        return events[0] if events else None
    latest_event = property(_latest_event)
    
class NetworkHost(models.Model):
    """
    Since one cannot use ManyToManyField type in GAE [1], we have to
    write extra model that will provide application with many-to-many
    relationship between networks and hosts.
    
    To ensure that after deleting host or network its relations will
    be removed too, we have to override delete() method for both
    Host and Network classes. Those methods should look like that:
    
    def delete(self, *args, **kwargs):
        related = NetworkHost.objects.filter(network=self)
        related.delete()
        super(Network, self).delete(*args, **kwargs)
        
    for Network class, and:
    
    def delete(self, *args, **kwargs):
        related = NetworkHost.objects.filter(host=self)
        related.delete()
        super(Host, self).delete(*args, **kwargs)
        
    for Host class. 
    
    [1] http://www.allbuttonspressed.com/projects/djangoappengine
    """
    network = models.ForeignKey(Network)
    host = models.ForeignKey(Host)

#class HostAdmin(admin.ModelAdmin):
#    list_display = ('name', 'ipv4', 'ipv6', 'user')
#admin.site.register(Host)
#
#class NetworkAdmin(admin.ModelAdmin):
#    list_display = ('name', 'user')
#admin.site.register(Network, NetworkAdmin)
#
#admin.site.register(NetworkHost)