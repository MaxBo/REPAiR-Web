import time
from django.core.management.base import BaseCommand, CommandError

from repair.apps.asmfa.models import Actor2Actor, ActorStock
from repair.apps.login.models import CaseStudy


def translate(*args, casestudy_id=None):
    casestudy_ids = CaseStudy.objects.all().values_list('id', flat=True) \
        if casestudy_id is None else [casestudy_id]

    for casestudy_id in sorted(casestudy_ids):
        print('-' * 50)
        print(f'Processing Casestudy id {casestudy_id}')
        # convert stocks
        stocks = ActorStock.objects.filter(keyflow__casestudy__id=casestudy_id)
        length = len(stocks)
        print('\nTranslating actor-stocks to fraction-flows')
        start = time.time()
        for i, stock in enumerate(stocks):
            stock.save()
            if i % 10 == 0:
                end = time.time()
                t = end - start
                print(f'{i}/{length} stocks converted in {t}s')
                start = time.time()
        print('done')

        # convert flows
        flows = Actor2Actor.objects.filter(keyflow__casestudy__id=casestudy_id)
        length = len(flows)
        print('\nTranslating actor2actor-flows to fraction-flows')
        for i, flow in enumerate(flows):
            flow.save()
            if i % 10 == 0:
                end = time.time()
                t = end - start
                print(f'{i}/{length} flows converted in {t}s')
                start = time.time()
        print('done')


class Command(BaseCommand):

    help = "translates all flows and stocks to fraction-flows (removing old ones)"

    def add_arguments(self, parser):
        parser.add_argument('casestudy_id', nargs='?', type=int, default=[])

    def handle(self, *args, **options):
        casestudy_ids = options['casestudy_id']
        if casestudy_ids:
            for casestudy_id in casestudy_ids:
                translate(casestudy=CaseStudy.objects.get(id=casestudy_id))
        else:
            translate()

if __name__ == 'main':
    translate()
