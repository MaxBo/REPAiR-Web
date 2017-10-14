from django.db import models
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.db.models import signals
# from django.contrib.gis.db import models


class GDSEModel(models.Model):
    """Base class for the GDSE Models"""

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class GDSEUniqueNameModel(GDSEModel):
    """Base class for the GDSE Models"""

    class Meta:
        abstract = True

    def validate_unique(self, *args, **kwargs):
        super().validate_unique(*args, **kwargs)

        qs = self.__class__._default_manager.filter(
            name=self.name
        )

        if qs.exists():
            for row in qs:
                if row.casestudy == self.casestudy:
                    raise ValidationError('{cl} {n} already exists in casestudy {c}'.format(
                            cl=self.__class__.__name__, n=self.name, c=self.casestudy,))

    def save(self, *args, **kwargs):
        """Call :meth:`full_clean` before saving."""
        if self.pk is None:
            self.full_clean()
        super(GDSEUniqueNameModel, self).save(*args, **kwargs)


class CaseStudy(GDSEModel):
    name = models.TextField()

    @property
    def solution_categories(self):
        """
        look for all solution categories created by the users of the casestudy
        """
        solution_categories = set()
        for uic in self.userincasestudy_set.all():
            for solution_category in uic.solutioncategory_set.all():
                solution_categories.add(solution_category)
        return solution_categories


class User(GDSEModel):
    name = models.TextField()
    casestudies = models.ManyToManyField(CaseStudy, through='UserInCasestudy')


class UserInCasestudy(GDSEModel):
    user = models.ForeignKey(User)
    casestudy = models.ForeignKey(CaseStudy)

    def __str__(self):
        text = '{u} ({c})'
        return text.format(u=self.user, c=self.casestudy,)


class Unit(GDSEModel):
    name = models.TextField()


class StakeholderCategory(GDSEUniqueNameModel):
    case_study = models.ForeignKey(CaseStudy)
    name = models.TextField()

    @property
    def casestudy(self):
        return self.case_study


class Stakeholder(GDSEUniqueNameModel):
    stakeholder_category = models.ForeignKey(StakeholderCategory)
    name = models.TextField()

    @property
    def casestudy(self):
        return self.stakeholder_category.casestudy


class SolutionCategory(GDSEUniqueNameModel):
    user = models.ForeignKey(UserInCasestudy)
    name = models.TextField()

    @property
    def casestudy(self):
        return self.user.casestudy


class Solution(GDSEUniqueNameModel):
    user = models.ForeignKey(UserInCasestudy)
    solution_category = models.ForeignKey(SolutionCategory)
    name = models.TextField()
    description = models.TextField()
    one_unit_equals = models.TextField()

    @property
    def casestudy(self):
        return self.user.casestudy


class SolutionQuantity(GDSEModel):
    solution = models.ForeignKey(Solution)
    unit = models.ForeignKey(Unit)
    name = models.TextField()

    def __str__(self):
        text = '{n} [{u}]'
        return text.format(n=self.name, u=self.unit,)


class SolutionRatioOneUnit(GDSEModel):
    solution = models.ForeignKey(Solution)
    name = models.TextField()
    value = models.FloatField()
    unit = models.ForeignKey(Unit)


class Implementation(GDSEModel):
    user = models.ForeignKey(UserInCasestudy)
    name = models.TextField()
    coordinating_stakeholder = models.ForeignKey(Stakeholder, default=1)
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
    solution = models.ForeignKey(Solution)
    implementation = models.ForeignKey(Implementation)
    participants = models.ManyToManyField(Stakeholder)

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
    each time a SolutionInImplementation is created.
    """
    if created:
        quantity = instance
        solution = quantity.solution
        sii_set = SolutionInImplementation.objects.filter(solution_id=solution.id)
        for sii in sii_set.all():
            new, is_created = SolutionInImplementationQuantity.objects.\
                get_or_create(sii=sii, quantity=quantity)
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


class SolutionInImplementationNote(GDSEModel):
    sii = models.ForeignKey(SolutionInImplementation, default=1)
    note = models.TextField()

    def __str__(self):
        text = 'Note for {s}:\n{n}'
        return text.format(s=self.sii, n=self.note)


class SolutionInImplementationQuantity(GDSEModel):
    sii = models.ForeignKey(SolutionInImplementation, default=1)
    quantity = models.ForeignKey(SolutionQuantity, default=1)
    value = models.FloatField(default=0)

    def __str__(self):
        text = '{v} {q}'
        return text.format(v=self.value, q=self.quantity)


class SolutionInImplementationGeometry(GDSEModel):
    sii = models.ForeignKey(SolutionInImplementation, default=1)
    name = models.TextField(blank=True)
    geom = models.TextField(blank=True)
    #geom = models.GeometryField(verbose_name='geom')

    def __str__(self):
        text = 'location {n} at {g}'
        return text.format(n=self.name, g=self.geom)


class Strategy(GDSEUniqueNameModel):
    user = models.ForeignKey(UserInCasestudy)
    name = models.TextField()
    coordinator = models.ForeignKey(Stakeholder, default=1)
    implementations = models.ManyToManyField(Implementation)

    @property
    def participants(self):
        """
        look for all stakeholders that participate in any of the implementations
        """
        # start with the coordinator
        participants = {self.coordinator}
        for implementation in self.implementations.all():
            for participant in implementation.participants:
                participants.add(participant)
        return participants

    @property
    def casestudy(self):
        return self.user.casestudy


####################                #########################
#################### AS-MFA classes #########################
####################                #########################

class DataEntry(models.Model):

    # this I am leaving empty for now - we have to agree at the consortium how we define users and data sources
    #user =
    #source =
    #date =
    pass


class Geolocation(models.Model):

    # same as for DataEntry, also geometry will have to be included later
    #street =
    #building =
    #postcode =
    #country =
    #city =
    #geom =
    pass

class Node(models.Model):  # should there be a separate model for the AS-MFA?

    # all the data for the Node class tables will be known in advance, the users will not have to fill that in
    source = models.BooleanField(default=False)  # if true - there is no input, should be introduced as a constraint later
    sink = models.BooleanField(default=False)  # if true - there is no output, same

    class Meta:
        abstract = True


class ActivityGroup(Node):

    # activity groups are predefined and same for all flows and case studies
    activity_group_choices = (("P1", "Production"),
                              ("P2", "Production of packaging"),
                              ("P3", "Packaging"),
                              ("D", "Distribution"),
                              ("S", "Selling"),
                              ("C", "Consuming"),
                              ("SC", "Selling and Cosuming"),
                              ("R", "Return Logistics"),
                              ("COL", "Collection"),
                              ("W", "Waste Management"),
                              ("imp", "Import"),  # 'import' and 'export' are "special" types of activity groups/activities/actors
                              ("exp", "Export"))
    code = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255, choices=activity_group_choices)


class Activity(Node):

    nace = models.CharField(max_length=255, primary_key=True)  # NACE code, unique for each activity
    name = models.CharField(max_length=255)  # not sure about the max length, leaving everywhere 255 for now

    own_activitygroup = models.ForeignKey(ActivityGroup, on_delete=models.CASCADE,
                                          related_name='Activities')


class Actor(Node):

    BvDid = models.CharField(max_length=255, primary_key=True) #unique actor identifier in ORBIS database
    name = models.CharField(max_length=255)

    # locations also let's leave out for now, we can add them later
    #operationalLocation = models.ForeignKey('Geolocation', on_delete=models.CASCADE, related_name='operationalLocation')
    #administrativeLocation = models.ForeignKey('Geolocation', on_delete=models.CASCADE, related_name='administrativeLocation')
    consCode = models.CharField(max_length=255)
    year = models.PositiveSmallIntegerField()
    revenue = models.PositiveIntegerField()
    employees = models.PositiveSmallIntegerField()
    BvDii = models.CharField(max_length=255)
    website = models.CharField(max_length=255)

    own_activity = models.ForeignKey(Activity, on_delete=models.CASCADE,
                                     related_name='Actors')


class Flow(models.Model):

    # users will have to add data about flows, that will relate two of the nodes
    # again, there will be limited material and quality choices, we should determine the exact ones later
    material_choices = (("PET", "PET plastic"),
                        ("Org", "Organic"),
                        ("PVC", "PVC plastic"))
    quality_choices = (("1", "High"),
                       ("2", "Medium"),
                       ("3", "Low"),
                       ("4", "Waste"))

    material = models.CharField(max_length=255, choices=material_choices, blank=True)
    amount = models.PositiveIntegerField(blank=True)
    quality = models.CharField(max_length=255, choices=quality_choices, blank=True)

    class Meta:
        abstract = True


class Group2Group(Flow):

    destination = models.ForeignKey(ActivityGroup, on_delete=models.CASCADE,
                                    related_name='Inputs')
    origin = models.ForeignKey(ActivityGroup, on_delete=models.CASCADE,
                               related_name='Outputs')


class Activity2Activity(Flow):

    destination = models.ForeignKey(Activity, on_delete=models.CASCADE,
                                    related_name='Inputs')
    origin = models.ForeignKey(Activity, on_delete=models.CASCADE,
                               related_name='Outputs')


class Actor2Actor(Flow):

    destination = models.ForeignKey(Actor, on_delete=models.CASCADE,
                                    related_name='Inputs')
    origin = models.ForeignKey(Actor, on_delete=models.CASCADE,
                               related_name='Outputs')


class Stock(models.Model):

    # stocks relate to only one node, also data will be entered by the users
    material = models.CharField(max_length=255, choices=Flow.material_choices, blank=True)
    amount = models.PositiveIntegerField(blank=True)
    quality = models.CharField(max_length=255, choices=Flow.quality_choices, blank=True)

    class Meta:
        abstract = True


class GroupStock(Stock):

        origin = models.ForeignKey(ActivityGroup, on_delete=models.CASCADE,
                                   related_name='Stocks')


class ActivityStock(Stock):

        origin = models.ForeignKey(Activity, on_delete=models.CASCADE,
                                   related_name='Stocks')


class ActorStock(Stock):

        origin = models.ForeignKey(Actor, on_delete=models.CASCADE,
                                   related_name='Stocks')
