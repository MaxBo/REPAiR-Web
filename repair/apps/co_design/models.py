from django.db import models

# Create your models here.

class CaseStudy(models.Model):
    name = models.TextField()


class User(models.Model):
    case_study_id = models.ForeignKey(CaseStudy)
    name = models.TextField()


class UserAP12(models.Model):
    case_study_id = models.ForeignKey(CaseStudy)
    name = models.TextField()


class Unit(models.Model):
    name = models.TextField()


class StakeholderCategory(models.Model):
    case_study_id = models.ForeignKey(CaseStudy)
    name = models.TextField()


class Stakeholder(models.Model):
    case_study_id = models.ForeignKey(CaseStudy)
    stakeholder_category_id = models.ForeignKey(StakeholderCategory)
    name = models.TextField()


class SolutionCategory(models.Model):
    case_study_id = models.ForeignKey(CaseStudy)
    user_ap12_id = models.ForeignKey(UserAP12)
    name = models.TextField()


class Solution(models.Model):
    case_study_id = models.ForeignKey(CaseStudy)
    user_ap12_id = models.ForeignKey(UserAP12)
    solution_category_id = models.ForeignKey(SolutionCategory)
    name = models.TextField()
    description = models.TextField()
    one_unit_equals = models.TextField()

