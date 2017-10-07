from django.db import models
#from django.contrib.gis.db import models

# Create your models here.


class GDSEModel(models.Model):
    """Base class for the GDSE Models"""

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

class CaseStudy(GDSEModel):
    name = models.TextField()


class UserAP12(GDSEModel):
    case_study = models.ForeignKey(CaseStudy)
    name = models.TextField()


class UserAP34(GDSEModel):
    case_study = models.ForeignKey(CaseStudy)
    name = models.TextField()


class Unit(GDSEModel):
    name = models.TextField()


class StakeholderCategory(GDSEModel):
    case_study = models.ForeignKey(CaseStudy)
    name = models.TextField()
    class Meta:
        unique_together = ("case_study", "name")


class Stakeholder(GDSEModel):
    stakeholder_category = models.ForeignKey(StakeholderCategory)
    name = models.TextField()

    #def validate_unique(self, *args, **kwargs):
        #super().validate_unique(*args, **kwargs)
        #qs = type(self).objects.filter(name=self.name)
        #if qs.filter(stakeholder_category__case_study=self.stakeholder_category__case_study).exists():
            #raise ValidationError({'name':['Name must be unique per CaseStudy',]})


class SolutionCategory(GDSEModel):
    case_study = models.ForeignKey(CaseStudy)
    user_ap12 = models.ForeignKey(UserAP12)
    name = models.TextField()
    class Meta:
        unique_together = ("case_study", "user_ap12", 'name')


class Solution(GDSEModel):
    case_study = models.ForeignKey(CaseStudy)
    user_ap12 = models.ForeignKey(UserAP12)
    solution_category = models.ForeignKey(SolutionCategory)
    name = models.TextField()
    description = models.TextField()
    one_unit_equals = models.TextField()


class SolutionQuantity(GDSEModel):
    solution = models.ForeignKey(Solution)
    unit = models.ForeignKey(Unit)
    name = models.TextField()


class SolutionRatioOneUnit(GDSEModel):
    solution = models.ForeignKey(Solution)
    name = models.TextField()
    value = models.FloatField()
    unit = models.ForeignKey(Unit)


class Implementation(GDSEModel):
    case_study = models.ForeignKey(CaseStudy)
    user = models.ForeignKey(UserAP34)
    name = models.TextField()
    coordinating_stakeholder = models.ForeignKey(Stakeholder)
    solutions = models.ManyToManyField(Solution,
                                       through='SolutionInImplementation')


class SolutionInImplementation(GDSEModel):
    solution = models.ForeignKey(Solution)
    implementation = models.ForeignKey(Implementation)

    def __str__(self):
        text = '{s} in {i}'
        return text.format(s=self.solution, i=self.implementation,)


class SolutionInImplementationNote(GDSEModel):
    sii = models.ForeignKey(SolutionInImplementation, default=1)
    note = models.TextField()

    def __str__(self):
        text = 'Note for {s}:\n{n}'
        return text.format(s=self.sii, n=self.note)


class SolutionInImplementationQuantity(GDSEModel):
    sii = models.ForeignKey(SolutionInImplementation, default=1)
    quantity = models.ForeignKey(SolutionQuantity, default=1)
    value = models.FloatField()

    def __str__(self):
        text = '{s} has {v} {q}'
        return text.format(s=self.sii,
                           v=self.value, q=self.quantity)


class SolutionInImplementationGeometry(GDSEModel):
    sii = models.ForeignKey(SolutionInImplementation, default=1)
    name = models.TextField(blank=True)
    geom = models.TextField(blank=True)
    #geom = models.GeometryField(verbose_name='geom')

    def __str__(self):
        text = 'location {n} for {s} at {g}'
        return text.format(s=self.sii,
                           n=self.name, g=self.geom)


class Strategy(GDSEModel):
    case_study = models.ForeignKey(CaseStudy)
    user = models.ForeignKey(UserAP34)
    name = models.TextField()
    coordinator = models.ForeignKey(Stakeholder, default=1)
    implementations = models.ManyToManyField(Implementation)

    class Meta:
        unique_together = ("case_study", "user", 'name')

