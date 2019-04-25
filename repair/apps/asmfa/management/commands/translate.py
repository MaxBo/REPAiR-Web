import time
from django.core.management.base import BaseCommand, CommandError

from repair.apps.asmfa.models import Actor2Actor, ActorStock
from repair.apps.login.models import CaseStudy


def translate(*args, casestudy_id=None,
              ignore_stocks=False, ignore_flows=False):
    casestudy_ids = CaseStudy.objects.all().values_list('id', flat=True) \
        if casestudy_id is None else [casestudy_id]

    for casestudy_id in sorted(casestudy_ids):
        print('-' * 50)
        print(f'Processing Casestudy id {casestudy_id}')
        start = time.time()

        # convert stocks
        if not ignore_stocks:
            stocks = ActorStock.objects.filter(keyflow__casestudy__id=casestudy_id)
            length = len(stocks)
            print('\nTranslating actor-stocks to fraction-flows')
            i = 1
            for stock in stocks.iterator():
                stock.save()
                if i % 10 == 0:
                    end = time.time()
                    t = end - start
                    print(f'{i}/{length} stocks converted in {t}s')
                    start = time.time()
                i += 1
            print('done')

        # convert flows
        if not ignore_flows:
            flows = Actor2Actor.objects.filter(keyflow__casestudy__id=casestudy_id)
            length = len(flows)
            print('\nTranslating actor2actor-flows to fraction-flows')
            i = 1
            for flow in flows.iterator():
                flow.save()
                if i % 10 == 0:
                    end = time.time()
                    t = end - start
                    print(f'{i}/{length} flows converted in {t}s')
                    start = time.time()
                i += 1
            print('done')


class Command(BaseCommand):

    help = "translates all flows and stocks to fraction-flows (removing old ones)"

    def add_arguments(self, parser):
        parser.add_argument('--casestudy_id', action='append', type=int)
        parser.add_argument('--flows_only', action='store_true')
        parser.add_argument('--stocks_only', action='store_true')

    def handle(self, *args, **options):
        casestudy_ids = options['casestudy_id']
        flows_only = options['flows_only']
        stocks_only = options['stocks_only']
        if flows_only and stocks_only:
            raise Exception("flows_only excludes stocks_only")
        if casestudy_ids:
            for casestudy_id in casestudy_ids:
                translate(casestudy_id=casestudy_id,
                          ignore_flows=stocks_only,
                          ignore_stocks=flows_only)
        else:
            translate()

if __name__ == 'main':
    translate()
