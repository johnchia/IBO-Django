from django.http import HttpResponse
from django.template import Context, loader
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect
import json

from ibo.models import *

from ego.gaussianprocess import GaussianProcess, PrefGaussianProcess, GaussianKernel_iso
from ego.acquisition.gallery import fastUCBGallery

# TODO
# - support other problem classes (e.g. WhiteBalanceProblems)
# - support top-K retrieval

def clear(request,problem_id):
    pcs = PairedComparison.objects.filter(
        content_type=ContentType.objects.get_for_model(ParametricArtProblem),
        object_id=problem_id).delete()
    return redirect('/learn/' + str(problem_id))

def index(request):
    problems_art = ParametricArtProblem.objects.all()
    problems_wb = WhiteBalanceProblem.objects.all()
    session = None
    if request.session.has_key('session_id'):
        session = BanditProblemSession.objects.get(id=request.session['session_id'])
    # ...
    t = loader.get_template('index.html')
    c = Context({
        'session': session,
        'problems_art': problems_art,
        'problems_wb': problems_wb,
    })
    return HttpResponse(t.render(c))

def sessions(request,problem_id,session_id=None,action=None,module_name='ParametricArtProblem'):
    module = eval(module_name)
    # set up
    problem = module.objects.get(id=problem_id)
    sessions = BanditProblemSession.objects.select_related().filter(
        content_type=ContentType.objects.get_for_model(module),
        object_id=problem.id,
    )
    if action is not None:
        if action == 'start':
            session = BanditProblemSession.objects.create(
                content_type=ContentType.objects.get_for_model(module),
                object_id=problem.id,
            )
            session_id = session.id
        if session_id is None: raise Exception('Bad! Session ID is None!!!')
        request.session['session_id'] = session.id;
        return redirect('/learn/')
    # ...
    t = loader.get_template('sessions.html')
    c = Context({
        'problem': problem,
        'sessions': sessions,
    })
    return HttpResponse(t.render(c))

def learn(request,pref=None,unpref=None,canvas_size=400):
    # set up
    if not request.session.has_key('session_id'):
        raise Exception('session_id not found in request.session')
    session = BanditProblemSession.objects.get(id=request.session['session_id'])
    problem = session.problem

    # push to database if needed
    if pref is not None and unpref is not None:
        pref = BanditContext.objects.get(id=pref)
        unpref = BanditContext.objects.get(id=unpref)
        pc = PairedComparison.objects.create(
            unpreferred_context=unpref,
            preferred_context=pref,
            session=session,
        )

    # now pull historical preferences
    gp = PrefGaussianProcess(GaussianKernel_iso([problem.length_scale, problem.noise_magnitude]))
    pcs = session.comparisons.all()
    if pcs is not None and len(pcs) > 0:
        gp.addPreferences([
            (pc.preferred_context.vector, pc.unpreferred_context.vector, 0)
            for pc in pcs ])

    # generate art (it just sounds wrong!!!)
    gal_db = {}
    gallery = fastUCBGallery(gp, [[0,1]]*problem.dim(), 2, useBest=True, xi=problem.xi,passback=gal_db)
    ctx1,_ = BanditContext.objects.get_or_create(dimension=len(gallery[0]),vector=gallery[0].tolist())
    ctx2,_ = BanditContext.objects.get_or_create(dimension=len(gallery[1]),vector=gallery[1].tolist())

    left_choice = problem.generate(ctx1.vector, id='left')
    right_choice = problem.generate(ctx2.vector, id='right')

    plots = _make_plots_from_gallery_passback(problem,gal_db)

    # ...
    t = loader.get_template('compare.html')
    c = Context({
        'left_choice': left_choice,
        'right_choice': right_choice,
        'context_1': ctx1,
        'context_2': ctx2,
        'problem': problem,
        'plots': json.dumps(plots),
    })
    return HttpResponse(t.render(c))

from numpy import linspace,sqrt
def _make_plots_from_gallery_passback(problem,gal_db):
    if problem.dim() > 1: return []
    ut = gal_db['utility']
    x = linspace(0,1,1/problem.length_scale*10)
    utf = [-ut.negf(i) for i in x]
    print utf
    # get gp data
    gp = gal_db['hallucGP']
    p_gp = {}
    m,v = gp.posteriors(x)
    xdata = gp.X.tolist()
    ydata = gp.Y.tolist()
    m = m.tolist()
    v = v.tolist()
    vfill = []
    vfill += [[x[i],m[i]+2*sqrt(v[i])] for i in range(len(m))]
    vfill += [[x[-1-i],m[-1-i]-2*sqrt(v[-1-i])] for i in range(len(m))]
    return [ 
        { 'data': zip(x,utf), 'label': 'Utility', 'color': 'green', 'yaxis': 2 },
        { 'data': zip(x,m), 'label': 'Posterior mean', 'color': 'blue' },
        { 'data': zip(xdata,ydata), 'label': 'Observations', 'color': 'blue', 'points': { 'show': True } } ,
        { 'data': vfill, 'label': 'Posterior 85%', 'lines': {  'lineWidth': 0, 'show': True, 'fill': 0.1 }, 'color': 'blue' },
    ]
        #{ 'data': [[gp.X[-1].tolist(),gp.Y[-1].tolist()]], 'label': 'Selected point', 'color': 'red', 'points': { 'show': True } } ,

def render_raw(request, problem_id, temperature=0.5):
    problem = WhiteBalanceProblem.objects.get(id=problem_id)
    #temperature = float(temperature)*5000.0 + 2000.0
    return HttpResponse(problem.render_jpeg(temperature), mimetype='image/jpeg')
