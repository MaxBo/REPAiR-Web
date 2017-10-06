from django.db import models
#from django.contrib.gis.db import models

# Create your models here.

class CaseStudy(models.Model):
    name = models.TextField()


class UserAP12(models.Model):
    case_study_id = models.ForeignKey(CaseStudy)
    name = models.TextField()


class UserAP34(models.Model):
    case_study_id = models.ForeignKey(CaseStudy)
    name = models.TextField()


class Unit(models.Model):
    name = models.TextField()


class StakeholderCategory(models.Model):
    case_study_id = models.ForeignKey(CaseStudy)
    name = models.TextField()
    class Meta:
        unique_together = ("case_study_id", "name")


class Stakeholder(models.Model):
    case_study_id = models.ForeignKey(CaseStudy)
    stakeholder_category_id = models.ForeignKey(StakeholderCategory)
    name = models.TextField()

    class Meta:
        unique_together = ("case_study_id", 'name')


class SolutionCategory(models.Model):
    case_study_id = models.ForeignKey(CaseStudy)
    user_ap12_id = models.ForeignKey(UserAP12)
    name = models.TextField()
    class Meta:
        unique_together = ("case_study_id", "user_ap12_id", 'name')


class Solution(models.Model):
    case_study_id = models.ForeignKey(CaseStudy)
    user_ap12_id = models.ForeignKey(UserAP12)
    solution_category_id = models.ForeignKey(SolutionCategory)
    name = models.TextField()
    description = models.TextField()
    one_unit_equals = models.TextField()


class SolutionQuantity(models.Model):
    solution = models.ForeignKey(Solution)
    unit = models.ForeignKey(Unit)
    name = models.TextField()


class SolutionRatioOneUnit(models.Model):
    solution = models.ForeignKey(Solution)
    name = models.TextField()
    value = models.FloatField()
    unit = models.ForeignKey(Unit)


class Implementation(models.Model):
    case_study_id = models.ForeignKey(CaseStudy)
    user_id = models.ForeignKey(UserAP34)
    name = models.TextField()
    coordinating_stakeholder_id = models.ForeignKey(Stakeholder)
    solutions = models.ManyToManyField(Solution)

    class Meta:
        unique_together = ("case_study_id", "user_id", 'name')


class SolutionInImplementationNotes(models.Model):
    solution = models.ForeignKey(Solution)
    implementation = models.ForeignKey(Implementation)
    note = models.TextField()


class SolutionInImplementationQuantities(models.Model):
    solution = models.ForeignKey(Solution)
    implementation = models.ForeignKey(Implementation)
    quantity = models.ForeignKey(SolutionQuantity, default=1)
    value = models.FloatField()


class SolutionInImplementationGeometry(models.Model):
    solution = models.ForeignKey(Solution)
    implementation = models.ForeignKey(Implementation)
    name = models.TextField()
    geom = models.TextField()
    #geom = models.GeometryField(verbose_name='geom')


class SolutionInImplementation(models.Model):
    solution = models.ForeignKey(Solution)
    implementation = models.ForeignKey(Implementation)
    notes = models.ManyToManyField(SolutionInImplementationNotes)
    geometries = models.ManyToManyField(SolutionInImplementationGeometry)
    quantities = models.ManyToManyField(SolutionInImplementationQuantities)


class Strategy(models.Model):
    case_study_id = models.ForeignKey(CaseStudy)
    user_id = models.ForeignKey(UserAP34)
    name = models.TextField()
    class Meta:
        unique_together = ("case_study_id", "user_id", 'name')
    implementations = models.ManyToManyField(Implementation)

