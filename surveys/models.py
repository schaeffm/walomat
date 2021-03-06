from django.db import models
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from modeltranslation.admin import TranslationAdmin, TranslationTabularInline
from PIL import Image


class Election(models.Model):
    title = models.CharField(_('title'), max_length=255)
    accessible_from = models.DateTimeField(_('accessible from'),
                                           default=timezone.now)
    accessible_to = models.DateTimeField(_('accessible to'),
                                         default=timezone.now)

    def __str__(self):
        return self.title

    @staticmethod
    def get_current():
        return Election.objects.filter(
            accessible_from__lt=timezone.now(),
            accessible_to__gt=timezone.now()).first()

    def first_thesis(self):
        return self.thesis_set.all().first()

    def all_theses(self):
        return self.thesis_set.all()

    def all_parties(self):
        return self.party_set.all()

    class Meta:
        verbose_name = _('election')
        verbose_name_plural = _('elections')


class Party(models.Model):
    election = models.ForeignKey('Election',
                                 verbose_name=_('election'),
                                 on_delete=models.CASCADE)
    short_name = models.CharField(_('short name'), max_length=127)
    full_name = models.CharField(_('full name'), max_length=255)
    image = models.ImageField(_('image'),
                              upload_to='parties/',
                              null=True,
                              blank=True)

    def __str__(self):
        return self.short_name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            img = Image.open(self.image.path)
            output_size = (200, 200)
            img.thumbnail(output_size)
            img.save(self.image.path)

    def all_answers(self):
        return self.answer_set.filter(
            election_id=self.election.id).order_by('id').all()

    class Meta:
        verbose_name = _('party')
        verbose_name_plural = _('parties')


class Thesis(models.Model):
    election = models.ForeignKey('Election',
                                 verbose_name=_('election'),
                                 on_delete=models.CASCADE)
    topic = models.CharField(_('topic'), max_length=127)
    thesis = models.TextField(_('text'))

    def __str__(self):
        return self.topic

    def next(self):
        return self.election.thesis_set.filter(
            id__gt=self.id).order_by('id').first()

    def position(self):
        return self.election.thesis_set.filter(id__lte=self.id).count()

    class Meta:
        verbose_name = _('thesis')
        verbose_name_plural = _('theses')


class Answer(models.Model):
    STANCE_PRO = '1'
    STANCE_NEUTRAL = '2'
    STANCE_AGAINST = '3'
    STANCE_OPTIONS = (
        (STANCE_PRO, _('agree')),
        (STANCE_NEUTRAL, _('neutral')),
        (STANCE_AGAINST, _('disagree')),
    )

    election = models.ForeignKey('Election',
                                 verbose_name=_('election'),
                                 on_delete=models.CASCADE)
    party = models.ForeignKey('Party',
                              verbose_name=_('party'),
                              on_delete=models.CASCADE)
    thesis = models.ForeignKey('Thesis',
                               verbose_name=_('thesis'),
                               on_delete=models.CASCADE)
    stance = models.CharField(_('stance'),
                              max_length=1,
                              choices=STANCE_OPTIONS)
    reasoning = models.TextField(_('reasoning'))

    def __str__(self):
        (value, stance) = self.STANCE_OPTIONS[int(self.stance) - 1]
        return _('{} on {}: {}').format(self.party, self.thesis, stance)

    def short_reasoning(self):
        return self.reasoning[:80] + " ..." if len(
            self.reasoning) > 80 else self.reasoning

    class Meta:
        verbose_name = _('answer')
        verbose_name_plural = _('answers')


class PartyInline(admin.TabularInline):
    model = Party


class ThesisInline(TranslationTabularInline):
    model = Thesis


class AnswerInline(TranslationTabularInline):
    model = Answer


class ElectionAdmin(TranslationAdmin):
    inlines = [PartyInline, ThesisInline, AnswerInline]


class PartyAdmin(admin.ModelAdmin):
    list_display = (
        'election',
        'short_name',
    )
    list_display_links = ('short_name', )


class ThesisAdmin(TranslationAdmin):
    list_display = (
        'election',
        'topic',
    )
    list_display_links = ('topic', )


class AnswerAdmin(TranslationAdmin):
    list_display = (
        'election',
        'party',
        'thesis',
        'short_reasoning',
        'stance',
    )
    list_display_links = (
        'short_reasoning',
        'stance',
    )
