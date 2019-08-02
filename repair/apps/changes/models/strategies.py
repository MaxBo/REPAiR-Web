
from django.db.models import signals
from django.contrib.gis.db import models
from repair.apps.login.models import (GDSEModel,
                                      UserInCasestudy)
from repair.apps.asmfa.models import KeyflowInCasestudy, Actor

from repair.apps.studyarea.models import Stakeholder
from repair.apps.changes.models.solutions import (
    Solution, SolutionPart, ImplementationQuestion, PossibleImplementationArea)
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
    # ToDo: enum for status
    # 0 - no calculation, 1 - calculating, 2 - ready
    status = models.IntegerField(default=0)
    # calculation started resp. finished
    date = models.DateTimeField(null=True)


class SolutionInStrategy(GDSEModel):
    '''
    implementation of a solution by a user
    '''
    solution = models.ForeignKey(Solution, on_delete=PROTECT_CASCADE)
    strategy = models.ForeignKey(Strategy,
                                 on_delete=PROTECT_CASCADE,
                                 related_name='solutioninstrategy')
    participants = models.ManyToManyField(Stakeholder)
    note = models.TextField(blank=True, null=True)

    # order of calculation, lowest first
    priority = models.IntegerField(default=0)

    def __str__(self):
        text = '{s} in {i}'
        return text.format(s=self.solution, i=self.strategy,)


class ImplementationQuantity(GDSEModel):
    '''
    answer by user to a implementation question
    '''
    implementation = models.ForeignKey(SolutionInStrategy,
                                       on_delete=models.CASCADE,
                                       related_name='implementation_quantity')
    question = models.ForeignKey(ImplementationQuestion,
                                 on_delete=models.CASCADE)
    value = models.FloatField()


class ImplementationArea(GDSEModel):
    '''
    answer by user to a implementation question
    '''
    implementation = models.ForeignKey(SolutionInStrategy,
                                       on_delete=models.CASCADE,
                                       related_name='implementation_area')
    possible_implementation_area = models.ForeignKey(
        PossibleImplementationArea, on_delete=models.CASCADE)
    geom = models.MultiPolygonField(null=True, srid=4326, blank=True)



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
                get_or_create(implementation=sii, question=question,
                              value=9958.0)
            if is_created:
                new.save()

signals.post_save.connect(
    trigger_implementationquantity_sii,
    sender=SolutionInStrategy,
    weak=False,
    dispatch_uid='models.trigger_implementationquantity_sii')

