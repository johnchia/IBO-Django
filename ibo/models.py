from subprocess import check_call
from tempfile import NamedTemporaryFile
from os import remove
from django.template import Context, loader
from django.conf import settings
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
    start = models.FloatField(default=0)
    end = models.FloatField(default=2*pi)
    class Meta:
        abstract = True

class WhiteBalanceProblem(BanditProblem):
    raw_image = models.FileField(upload_to='wb-bandit/%Y/%m/%d')
    def render_jpeg(self, temperature):
        filename = settings.MEDIA_ROOT + "/" + self.raw_image.name
        tempfile = NamedTemporaryFile()
        check_call("DYLD_LIBRARY_PATH=~/Dropbox/src/ufraw-mac/lib ~/Dropbox/src/ufraw-mac/bin/ufraw-batch --size=800 --out-type=jpg --output=%s --overwrite --temperature=%s %s" % (tempfile.name, temperature, filename), shell=True)
        return open(tempfile.name, 'r').read()
    def generate(self, context, id='default', csize=400):
        temperature = context[0]*5000 + 2000
        return ("<img width=\"%s\" src=\"/render-raw/%d/%f\" alt=\"%s/\">" % (csize,self.id, temperature, temperature))
    def dim(self):
        return 1

class ParametricArtProblem(BanditProblem):
    # these would be something like a,b,c,t: a*cos(b*t)+c
    yp = models.CharField(max_length=200)
    xp = models.CharField(max_length=200)
    parameters = models.CharField(max_length=20)
    renderable_points = models.PositiveIntegerField(default=500)
    def dim(self):
        return len(self.parameters.split(','))
    def generate(self, context, id='default', csize=400):
        xfunc = eval('lambda t,' + str(self.parameters) + ': ' + str(self.xp))
        yfunc = eval('lambda t,' + str(self.parameters) + ': ' + str(self.yp))
        Npts = min(1000,self.renderable_points)
        pts = zeros((Npts, 2))
        for i,t in enumerate(linspace(self.start,self.end,Npts)):
            pts[i,0] = xfunc(t,*context)
            pts[i,1] = yfunc(t,*context)
        pts = 0.5*csize*(1+pts)
        t = loader.get_template('parametric_art.html')
        c = Context({ 'point_list': pts.tolist(), 'id': id, 'width':csize, 'height':csize })
        return t.render(c)
        


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
