from django.test import TestCase
from django.urls import reverse
from test_plus import APITestCase
from django.contrib.gis.geos import Point, MultiPoint, LineString

from repair.tests.test import BasicModelPermissionTest, BasicModelReadTest
from repair.apps.changes.models import (
    SolutionInStrategyQuantity,
    SolutionQuantity,
    )

from repair.apps.changes.factories import (
    SolutionFactory,
    SolutionQuantityFactory,
    StrategyFactory,
    SolutionInStrategyFactory,
    SolutionInStrategyQuantityFactory)

from repair.apps.studyarea.factories import StakeholderFactory
from repair.apps.login.factories import UserInCasestudyFactory


class ModelSolutionInStrategy(TestCase):

    def test01_new_solutioninstrategy(self):
        """Test the new solution strategy"""

        # Create a solution with two quantities
        solution = SolutionFactory()
        solution_quantity1 = SolutionQuantityFactory(
            solution=solution, name='q1')
        solution_quantity2 = SolutionQuantityFactory(
            solution=solution, name='q2')

        # add solution to an strategy
        strategy = StrategyFactory()
        solution_in_strategy = SolutionInStrategyFactory(
            solution=solution,
            strategy=strategy)

        # check, if the SolutionInStrategyQuantity contains
        # now the 2 quantities

        solution_in_strategy_quantities = SolutionInStrategyQuantity.\
            objects.filter(sii=solution_in_strategy)
        solution_names = solution_in_strategy_quantities.values_list(
            'quantity__name', flat=True)
        assert len(solution_names) == 2
        assert set(solution_names) == {'q1', 'q2'}

        # create a solution that requires 3 quantities

        # add to the solution a third quantity
        solution_quantity3 = SolutionQuantityFactory(solution=solution,
                                                     name='q3')

        # check if the new quantity has been added to the related table
        solution_in_strategy_quantities = SolutionInStrategyQuantity.\
            objects.filter(sii=solution_in_strategy)
        solution_names = solution_in_strategy_quantities.values_list(
            'quantity__name', flat=True)
        assert len(solution_names) == 3
        assert set(solution_names) == {'q1', 'q2', 'q3'}

        # remove a solution quantity
        to_delete = SolutionQuantity.objects.filter(solution=solution,
                                                    name='q2')
        solution_id, deleted = to_delete.delete()
        # assert that 1 row in changes.SolutionInStrategyQuantity
        # are deleted
        assert deleted.get('changes.SolutionInStrategyQuantity') == 1

        # check the related SolutionInStrategyQuantity
        solution_in_strategy_quantities = SolutionInStrategyQuantity.\
            objects.filter(sii=solution_in_strategy)
        solution_names = solution_in_strategy_quantities.values_list(
            'quantity__name', flat=True)
        assert len(solution_names) == 2
        assert set(solution_names) == {'q1', 'q3'}

        # remove the solution_in_strategy
        sii_id, deleted = solution_in_strategy.delete()
        # assert that 2 rows in changes.SolutionInStrategyQuantity
        # are deleted
        assert deleted.get('changes.SolutionInStrategyQuantity') == 2
        solution_in_strategy_quantities = SolutionInStrategyQuantity.\
            objects.filter(sii=sii_id)
        assert not solution_in_strategy_quantities


class SolutionInStrategyInCasestudyTest(BasicModelPermissionTest, APITestCase):

    casestudy = 17
    keyflow = 23
    user = 20
    strategy = 30
    solution = 20
    solutioncategory = 56
    solution_strategy = 40

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.solution_url = cls.baseurl + \
            reverse('solution-detail',
                    kwargs=dict(casestudy_pk=cls.casestudy,
                                solutioncategory_pk=cls.solutioncategory,
                                keyflow_pk=cls.keyflow,
                                pk=cls.solution))
        cls.strategy_url = cls.baseurl + \
            reverse('strategy-detail',
                    kwargs=dict(casestudy_pk=cls.casestudy,
                                keyflow_pk=cls.keyflow,
                                pk=cls.strategy))
        cls.post_urls = [cls.solution_url, cls.strategy_url]
        cls.sol_set = []
        cls.url_key = "solutioninstrategy"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           strategy_pk=cls.strategy,
                           keyflow_pk=cls.keyflow)
        cls.url_pk = dict(pk=cls.solution)
        cls.post_data = dict(solution=cls.solution,
                             strategy=cls.strategy_url)
        cls.put_data = dict(solution=cls.solution,
                            strategy=cls.strategy_url)
        cls.patch_data = dict(solution=cls.solution,
                              strategy=cls.strategy_url)

    def setUp(self):
        super().setUp()
        self.obj = SolutionInStrategyFactory(
            solution__user=self.uic,
            solution__solution_category__user=self.uic,
            solution__id=self.solution,
            strategy__user=self.uic,
            strategy__id=self.strategy,
            strategy__keyflow=self.kic,
            solution__solution_category__id=self.solutioncategory,
            solution__solution_category__keyflow=self.kic,
            id=self.solution_strategy)


class QuantityInSolutionInStrategyInCasestudyTest(BasicModelReadTest,
                                                  APITestCase):
    """
    Test is not working:
    - delete is not allowed
    - post is not possible via Browser api
    """
    casestudy = 17
    keyflow = 3
    user = 20
    strategy = 30
    solution = 20
    solutioncategory = 56
    solution_strategy = 40
    quantity = 25

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sol_set = []
        cls.url_key = "solutioninstrategyquantity"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           strategy_pk=cls.strategy,
                           solution_pk=cls.solution_strategy,
                           keyflow_pk=cls.keyflow)
        cls.quantity_url = cls.baseurl + \
            reverse('solutionquantity-detail',
                    kwargs=dict(casestudy_pk=cls.casestudy,
                                solutioncategory_pk=cls.solutioncategory,
                                solution_pk=cls.solution,
                                keyflow_pk=cls.keyflow,
                                pk=cls.quantity))
        cls.post_urls = [cls.quantity_url]
        cls.url_pk = dict(pk=cls.quantity)
        cls.put_data = dict(value=1000.12)
        cls.patch_data = dict(value=222.333)

    def setUp(self):
        super().setUp()
        self.obj = SolutionInStrategyQuantityFactory(
            sii__solution__user=self.uic, sii__solution__id=self.solution,
            sii__strategy__user=self.uic,
            sii__strategy__id=self.strategy,
            sii__strategy__keyflow=self.kic,
            sii__solution__solution_category__id=self.solutioncategory,
            sii__id=self.solution_strategy,
            id=self.quantity)
