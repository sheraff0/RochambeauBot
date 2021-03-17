from django.core.management.base import BaseCommand, CommandError

from bot.bot_backend import RoshamboBot


class Command(BaseCommand):
    help = 'Configures and initiates Telegram Bot'

    def add_arguments(self, parser):
        # parser.add_argument('poll_ids', nargs='+', type=int)
        pass

    def handle(self, *args, **options):
        bot = RoshamboBot()
