from django.http import HttpResponse
from django.template import Context, loader
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect

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
    problems = ParametricArtProblem.objects.all()
    session = None
    if request.session.has_key('session_id'):
        session = BanditProblemSession.objects.get(id=request.session['session_id'])
    # ...
    t = loader.get_template('index.html')
    c = Context({
        'session': session,
        'problems': problems,
    })
    return HttpResponse(t.render(c))

def sessions(request,problem_id,session_id=None,action=None):
    # set up
    problem = ParametricArtProblem.objects.get(id=problem_id)
    sessions = BanditProblemSession.objects.select_related().filter(
        content_type=ContentType.objects.get_for_model(ParametricArtProblem),
        object_id=problem.id,
    )
    if action is not None:
        if action == 'start':
            session = BanditProblemSession.objects.create(
                content_type=ContentType.objects.get_for_model(ParametricArtProblem),
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
    Ndim = len(problem.parameters.split(','))

    # push to database if needed
    if pref is not None and unpref is not None:
        pref = BanditContext.objects.get(id=pref)
        unpref = BanditContext.objects.get(id=unpref)
        pc,_ = PairedComparison.objects.get_or_create(
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
    gallery = fastUCBGallery(gp, [[0,1]]*Ndim, 2, useBest=False, xi=problem.xi)
    ctx1,_ = BanditContext.objects.get_or_create(dimension=len(gallery[0]),vector=gallery[0].tolist())
    ctx2,_ = BanditContext.objects.get_or_create(dimension=len(gallery[1]),vector=gallery[1].tolist())

    choice_1 = canvas_size/2.0*(1+problem.generate(ctx1.vector))
    choice_2 = canvas_size/2.0*(1+problem.generate(ctx2.vector))

    # ...
    t = loader.get_template('compare.html')
    c = Context({
        'choice_1': choice_1.tolist(),
        'choice_2': choice_2.tolist(),
        'context_1': ctx1,
        'context_2': ctx2,
        'problem': problem,
    })
    return HttpResponse(t.render(c))

def render_raw(request, problem_id, temperature=4500):
    problem = WhiteBalanceProblem.objects.get(id=problem_id)
    print temperature
    return HttpResponse(problem.render_jpeg(temperature), mimetype='image/jpeg')
