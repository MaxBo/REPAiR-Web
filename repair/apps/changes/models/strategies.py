
from django.db.models import signals
from django.contrib.gis.db import models
from repair.apps.login.models import (GDSEModel,
                                      UserInCasestudy)
from repair.apps.asmfa.models import KeyflowInCasestudy, Actor

from repair.apps.studyarea.models import Stakeholder
from repair.apps.changes.models.solutions import (Solution,
                                                  SolutionPart,
                                                  ImplementationQuestion)
from repair.apps.utils.protect_cascade import PROTECT_CASCADE


class Strategy(GDSEModel):
    '''
    there should only be one per user
    '''
    user = models.ForeignKey(UserInCasestudy, on_delete=models.CASCADE)
    keyflow = models.ForeignKey(KeyflowInCasestudy,
                                on_delete=models.CASCADE)
    name = models.TextField()
    coordinating_stakeholder = models.ForeignKey(Stakeholder,
                                                 on_delete=PROTECT_CASCADE,
                                                 null=True)
    solutions = models.ManyToManyField(Solution,
                                       through='SolutionInStrategy')

    @property
    def participants(self):
        """
        look for all stakeholders that participate in any of the solutions
        """
        # start with the coordinator
        participants = {self.coordinating_stakeholder}
        for solution in self.solutioninstrategy_set.all():
            for participant in solution.participants.all():
                participants.add(participant)
        return participants


class SolutionInStrategy(GDSEModel):
    '''
    implementation of a solution by a user
    '''
    solution = models.ForeignKey(Solution, on_delete=PROTECT_CASCADE)
    strategy = models.ForeignKey(Strategy,
                                 on_delete=PROTECT_CASCADE)
    participants = models.ManyToManyField(Stakeholder)
    note = models.TextField(blank=True, null=True)
    geom = models.GeometryCollectionField(verbose_name='geom', null=True)
    priority = models.IntegerField(default=0)

    def __str__(self):
        text = '{s} in {i}'
        return text.format(s=self.solution, i=self.strategy,)


class ActorInSolutionPart(GDSEModel):
    solutionpart = models.ForeignKey(SolutionPart, on_delete=PROTECT_CASCADE,
                                     related_name='targetactor')
    actor = models.ForeignKey(Actor, on_delete=PROTECT_CASCADE)
    implementation = models.ForeignKey(SolutionInStrategy,
                                       on_delete=models.CASCADE)


class ImplementationQuantity(GDSEModel):
    '''
    answer by user to a implementation question
    '''
    implementation = models.ForeignKey(SolutionInStrategy,
                                       on_delete=models.CASCADE)
    question = models.ForeignKey(ImplementationQuestion,
                                 on_delete=PROTECT_CASCADE)
    value = models.FloatField()

def trigger_implementationquantity_sii(sender, instance,
                                       created, **kwargs):
    """
    Create ImplementationQuantity for each ImplementationQuestion
    each time a SolutionInStrategy is created.
    """
    if created:
        sii = instance
        solution = Solution.objects.get(pk=sii.solution.id)
        for question in solution.question.all():
            new, is_created = ImplementationQuantity.objects.\
                get_or_create(implementation=sii, question=question, value=0)
            if is_created:
                new.save()

signals.post_save.connect(
    trigger_implementationquantity_sii,
    sender=SolutionInStrategy,
    weak=False,
    dispatch_uid='models.trigger_implementationquantity_sii')



