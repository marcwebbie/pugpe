# -*- coding:utf-8 -*-
from django.views.generic import CreateView, ListView
from django.views.generic.base import TemplateView
from django.core.urlresolvers import reverse
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.shortcuts import redirect

from events.models import Event, EventTalk
from events.views import EventMixin

from .models import Talk
from .forms import TalkForm, VoteForm
from .utils import token_required


class SubmissionSuccess(EventMixin, TemplateView):
    template_name = "submission/success_submission.html"

    def get_context_data(self, **kwargs):
        kwargs = super(SubmissionSuccess, self).get_context_data()
        kwargs['event'] = Event.objects.get(slug=self.kwargs['event_slug'])
        return kwargs


class SubmissionView(EventMixin, CreateView):
    form_class = TalkForm
    template_name = 'submission/submission.html'
    model = Talk

    def get_success_url(self):
        return reverse('submission:success_submission', kwargs=self.kwargs)

    def get_form_kwargs(self):
        kwargs = super(SubmissionView, self).get_form_kwargs()
        kwargs['event'] = Event.objects.get(slug=self.kwargs['event_slug'])

        return kwargs

    def dispatch(self, *args, **kwargs):
        # necessário para o método get_context_data ser executado
        response = super(SubmissionView, self).dispatch(*args, **kwargs)

        event = self.get_context_data()['event']
        if event.submission_deadline < timezone.now():
            return redirect(reverse('submission:end', kwargs=self.kwargs))

        return response


class SubmissionListView(EventMixin, ListView):
    model = Talk
    template_name = 'submission/vote.html'
    context_object_name = 'talks'
    paginate_by = 1

    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(SubmissionListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        ets = EventTalk.objects.filter(talk__isnull=False)
        ets = ets.exclude(talk__type='light')
        ets = ets.filter(event=self.event)
        pks = list(ets.values_list('talk__pk', flat=1))

        return Talk.objects.filter(pk__in=pks)

    def post(self, request, *args, **kwargs):
        form = VoteForm(request.POST)
        if form.is_valid():
            form.save(request.session['email'])

        page = request.POST.get('page', None)
        if page is None:
            return redirect(reverse('submission:success', kwargs=self.kwargs))

        return redirect(
            reverse('submission:vote', kwargs=self.kwargs) +
            '?page={0}'.format(page),
        )
