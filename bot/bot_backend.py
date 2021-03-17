import datetime
from telegram import (
    Bot, Update, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    MessageHandler, ConversationHandler, CommandHandler,
    Updater, Filters, CallbackContext, CallbackQueryHandler,
)
from telegram.utils.request import Request
from telegram.error import BadRequest

from django.conf import settings as _
from bot.models import Profile, Message
from .game import Roshambo, FIGURES_LIST


class RoshamboMixin:
    NEXT_MOVE, GAME_OVER = range(2)  # conversation state codes
    rounds = range(1, 6)

    def options_list_buttons(self, list_):
        return [InlineKeyboardButton(
            value, callback_data=key
        ) for key, value in enumerate(list_)]

    def score(self, list_):
        return ':'.join(map(str, list_))

    def tableau(self):
        return '\n'.join([
            f"Счёт в текущем раунде - {self.score(self.game.attempts_score)}",
            f"Счёт по раундам - {self.score(self.game.rounds_score)}",
            *([f"Вы {self.game.player_move or ''} -> <- {self.game.opponent_move or ''} Компьютер"] if self.game.player_move else []),
            *([f"""В {self.game.rounds_count} раунде {
                'победили Вы' if self.game.round_winner == 0 else 'победил компьютер'
            }."""] if self.game.round_winner is not None else []),
            *([] if self.game.game_winner is not None else ["Ваш следующй ход:"]),
        ])

    def start(self, update: Updater, context: CallbackContext) -> int:
        reply_keyboard = [self.options_list_buttons(self.rounds)]
        reply_markup = InlineKeyboardMarkup(reply_keyboard)
        update.message.reply_text(
            "Максимальный счёт по раундам", reply_markup=reply_markup)
        self.game = None
        return self.NEXT_MOVE

    def next_move(self, update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        query.answer()
        move = None
        if self.game:
            move = int(query.data)
            move = FIGURES_LIST[move]
            self.game.next_move(move)
        else:
            rounds = int(query.data) + 1
            self.game = Roshambo(rounds)
        if self.game.game_winner is not None:
            return self.GAME_OVER
        reply_keyboard = [self.options_list_buttons(FIGURES_LIST)]
        reply_markup = InlineKeyboardMarkup(reply_keyboard)
        try:
            query.edit_message_text(
                text=self.tableau(),
                reply_markup=reply_markup
            )
        except BadRequest:
            pass
        return self.NEXT_MOVE

    def game_over(self, update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        query.answer()
        query.edit_message_text(
            text=f"""{self.tableau()}
ИГРА ОКОНЧЕНА! {'Победили Вы' if self.game.game_winner == 0 else 'Победил компьютер'}.""")
        return ConversationHandler.END

    def get_handler(self):
        return ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                self.NEXT_MOVE: [CallbackQueryHandler(self.next_move)],
                self.GAME_OVER: [CallbackQueryHandler(self.game_over)],
            },
            fallbacks=[CommandHandler('cancel', self.game_over)]
        )


class TelegramBot:
    def __init__(self):
        self.create_bot()
        self.set_updater()

    def create_bot(self):
        request = Request(
            connect_timeout=1.5,
            read_timeout=1.5,
            con_pool_size=8
        )
        self.bot = Bot(
            request=request,
            token=_.TELEGRAM_BOT_TOKEN,
            # base_url=_.TELEGRAM_PROXY_URL,
        )

    def set_updater(self):
        updater = Updater(bot=self.bot)
        updater.dispatcher.add_handler(
            self.get_handler())
        updater.start_polling()
        updater.idle()

    def get_handler(self):
        # Echo as default
        return MessageHandler(Filters.text, self.do_echo)

    def get_message_details(self, update):
        return (
            update.message.chat_id,
            update.message.text,
            update.message.from_user
        )

    def do_echo(self, update: Update, context: CallbackContext):
        chat_id, text, from_user = self.get_message_details(update)
        update.message.reply_text(
            text=f"{chat_id}\n\n{text}\n{from_user.first_name}")


class RoshamboBot(RoshamboMixin, TelegramBot):
    pass
