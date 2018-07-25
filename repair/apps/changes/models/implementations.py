
from django.db.models import signals
from django.contrib.gis.db import models
from repair.apps.login.models import (GDSEModel,
                                      UserInCasestudy)

from repair.apps.studyarea.models import Stakeholder
from .solutions import Solution, SolutionQuantity
from repair.apps.utils.protect_cascade import PROTECT_CASCADE


class Implementation(GDSEModel):
    user = models.ForeignKey(UserInCasestudy, on_delete=models.CASCADE)
    name = models.TextField()
    coordinating_stakeholder = models.ForeignKey(Stakeholder,
                                                 on_delete=PROTECT_CASCADE)
    solutions = models.ManyToManyField(Solution,
                                       through='SolutionInImplementation')

    @property
    def participants(self):
        """
        look for all stakeholders that participate in any of the solutions
        """
        # start with the coordinator
        participants = {self.coordinating_stakeholder}
        for solution in self.solutioninimplementation_set.all():
            for participant in solution.participants.all():
                participants.add(participant)
        return participants


class SolutionInImplementation(GDSEModel):
    solution = models.ForeignKey(Solution, on_delete=PROTECT_CASCADE)
    implementation = models.ForeignKey(Implementation,
                                       on_delete=PROTECT_CASCADE)
    participants = models.ManyToManyField(Stakeholder)
    note = models.TextField(blank=True, null=True)
    geom = models.GeometryCollectionField(verbose_name='geom', null=True)

    def __str__(self):
        text = '{s} in {i}'
        return text.format(s=self.solution, i=self.implementation,)


def trigger_solutioninimplementationquantity_sii(sender, instance,
                                                 created, **kwargs):
    """
    Create SolutionInImplementationQuantity
    for each SolutionQuantity
    each time a SolutionInImplementation is created.
    """
    if created:
        sii = instance
        solution = Solution.objects.get(pk=sii.solution.id)
        for solution_quantity in solution.solutionquantity_set.all():
            new, is_created = SolutionInImplementationQuantity.objects.\
                get_or_create(sii=sii, quantity=solution_quantity)
            if is_created:
                new.save()


def trigger_solutioninimplementationquantity_quantity(sender, instance,
                                                      created, **kwargs):
    """
    Create SolutionInImplementationQuantity
    for each SolutionQuantity
    each time a SolutionQuantity is created.
    """
    if created:
        solution_quantity = instance
        solution = solution_quantity.solution
        sii_set = SolutionInImplementation.objects.filter(
            solution_id=solution.id)
        for sii in sii_set.all():
            new, is_created = SolutionInImplementationQuantity.objects.\
                get_or_create(sii=sii, quantity=solution_quantity)
            if is_created:
                new.save()


signals.post_save.connect(
    trigger_solutioninimplementationquantity_sii,
    sender=SolutionInImplementation,
    weak=False,
    dispatch_uid='models.trigger_solutioninimplementationquantity_sii')

signals.post_save.connect(
    trigger_solutioninimplementationquantity_quantity,
    sender=SolutionQuantity,
    weak=False,
    dispatch_uid='models.trigger_solutioninimplementationquantity_quantity')


class SolutionInImplementationQuantity(GDSEModel):
    sii = models.ForeignKey(SolutionInImplementation,
                            on_delete=models.CASCADE)
    quantity = models.ForeignKey(SolutionQuantity,
                                 on_delete=models.CASCADE)
    value = models.FloatField(default=0)

    def __str__(self):
        text = '{v} {q}'
        return text.format(v=self.value, q=self.quantity)

