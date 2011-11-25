from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from numpy import linspace,pi,zeros,cos,sin
from ibo.customfields import VectorField

class BanditProblem(models.Model):
    description = models.CharField(max_length=100)
    length_scale = models.FloatField(default=0.25)
    noise_magnitude = models.FloatField(default=0.01)
    xi = models.FloatField(default=0) # increase to gain exploration
    class Meta:
        abstract = True

class ParametricArtProblem(BanditProblem):
    # these would be something like a,b,c,t: a*cos(b*t)+c
    yp = models.CharField(max_length=200)
    xp = models.CharField(max_length=200)
    parameters = models.CharField(max_length=20)
    renderable_points = models.PositiveIntegerField(default=500)
    start = models.FloatField(default=0)
    end = models.FloatField(default=2*pi)
    def generate(self, context):
        xfunc = eval('lambda t,' + str(self.parameters) + ': ' + str(self.xp))
        yfunc = eval('lambda t,' + str(self.parameters) + ': ' + str(self.yp))
        Npts = min(1000,self.renderable_points)
        pts = zeros((Npts, 2))
        for i,t in enumerate(linspace(self.start,self.end,Npts)):
            pts[i,0] = xfunc(t,*context)
            pts[i,1] = yfunc(t,*context)
        return pts

class BanditProblemSession(models.Model):
    date = models.DateTimeField(auto_now=True)
    # generic foreign keys -- refer to http://tinyurl.com/6fcx6y9
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    problem = generic.GenericForeignKey('content_type','object_id')

class BanditContext(models.Model):
    dimension = models.PositiveIntegerField()
    vector = VectorField(blank=True,unique=True,max_length=255)

class PairedComparison(models.Model):
    preferred_context = models.ForeignKey(BanditContext,related_name='+')
    unpreferred_context = models.ForeignKey(BanditContext,related_name='+')
    session = models.ForeignKey(BanditProblemSession, related_name='comparisons')
    date = models.DateTimeField(auto_now=True)
