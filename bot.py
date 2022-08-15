import asyncio
from functools import wraps
from dotenv import dotenv_values

from telegram import (
    Bot, Update, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, Defaults, ContextTypes,
    MessageHandler, ConversationHandler, CommandHandler,
    Updater, CallbackContext, CallbackQueryHandler,
)
from telegram.ext.filters import TEXT
from telegram.error import BadRequest

from game import Roshambo, FIGURES_LIST

config = dotenv_values(".env")


def delay(class_method):
    """Block handler until previuos event is processed,
    to avoid race conditions
    """
    DELAY = 500
    @wraps(class_method)
    async def wrapper(*args, **kwargs):
        result = await class_method(*args, **kwargs)
        await asyncio.sleep(DELAY / 1000)
        return result
    return wrapper


class RoshamboMixin:
    DELAY = 500  # ms
    NEXT_MOVE, GAME_OVER = range(2)  # conversation state codes
    ROUNDS = range(1, 6)
    CANCEL: int = -1
    CONVERSATIONS = {}

    def get_cancel_keyboard(self):
        return [InlineKeyboardButton("Отмена", callback_data=self.CANCEL)]

    def options_list_buttons_markup(self, list_, cancel=True):
        reply_keyboard = [InlineKeyboardButton(
            value, callback_data=key
        ) for key, value in enumerate(list_)]
        cancel_keyboard = self.get_cancel_keyboard() if cancel else []
        return InlineKeyboardMarkup([reply_keyboard, cancel_keyboard])

    @staticmethod
    def get_score(list_):
        return f"<b><i>{' : '.join(map(str, list_))}</i></b>"

    @staticmethod
    def get_greeting(user_name):
            return f'''Привет, {user_name}!
Сыграй в "Камень-ножницы-бумага" с ботом!
Выбери счёт по раундам для победы:'''

    def get_tableau(self):
        return '\n'.join([
            f"Счёт - {self.get_score(self.game.attempts_score)}",
            f"По раундам - {self.get_score(self.game.rounds_score)}",
            *([f"\nВы: {self.game.player_move or ''}",
            f"Компьютер: {self.game.opponent_move or ''}"] if self.game.player_move else []),
            *([f"""\nВ {self.game.rounds_count} раунде {
                'победили Вы' if self.game.round_winner == 0 else 'победил компьютер'
            }."""] if self.game.round_winner is not None else []),
            *([] if self.game.game_winner is not None else ["\nВаш ход:"]),
        ])

    def get_game_over(self):
        return f"""{self.get_tableau()}
\nИГРА ОКОНЧЕНА! {'Победили Вы' if self.game.game_winner == 0 else 'Победил компьютер'}.\n/start, чтоб начать заново"""

    @staticmethod
    def get_cancel_text():
        return "Игра прервана.\n/start, чтоб начать заново"

    @delay
    async def start(self, update: Updater, context: CallbackContext) -> int:
        user = update.effective_user
        user_name = user.first_name
        reply_markup = self.options_list_buttons_markup(self.ROUNDS)
        await update.message.reply_text(
            self.get_greeting(user_name),
            reply_markup=reply_markup)
        self.game = None
        return self.NEXT_MOVE

    @delay
    async def next_move(self, update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        await query.answer()
        data = int(query.data)
        if data == self.CANCEL:
            return await self.cancel(update, context)
        move = None
        if self.game:
            move = data
            try:
                move = FIGURES_LIST[move]
                self.game.next_move(move)
            except IndexError:
                pass
        else:
            rounds = data + 1
            self.game = Roshambo(rounds)
        if self.game.game_winner is not None:
            return self.GAME_OVER
        reply_markup = self.options_list_buttons_markup(FIGURES_LIST)
        try:
            await query.edit_message_text(
                text=self.get_tableau(),
                reply_markup=reply_markup,
            )
        except BadRequest:
            return ConversationHandler.END
        return self.NEXT_MOVE

    async def game_over(self, update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text=self.get_game_over(),
        )
        return ConversationHandler.END

    async def cancel(self, update: Updater, context: CallbackContext) -> int:
        query = update.callback_query
        if query:
            await query.edit_message_text(
                text=self.get_cancel_text())
        else:
            await update.message.reply_text(
                text=self.get_cancel_text()
            )
        return ConversationHandler.END

    def get_handlers(self):
        return [
            ConversationHandler(
                entry_points=[CommandHandler('start', self.start)],
                states={
                    self.NEXT_MOVE: [CallbackQueryHandler(self.next_move)],
                    self.GAME_OVER: [CallbackQueryHandler(self.game_over)],
                },
                fallbacks=[CommandHandler('cancel', self.cancel)],
                conversation_timeout=60,
                # allow_reentry=True,
            ),
            *super().get_handlers()
        ]


class TelegramBot:
    def __init__(self):
        self.create_bot()
        self.add_handlers()
        self.bot.run_polling()

    def create_bot(self):
        self.bot = ApplicationBuilder().token(
            token=config.get("TOKEN")
        ).defaults(Defaults(
            parse_mode="HTML"
        )).build()

    def add_handlers(self):
        handlers = self.get_handlers()
        self.bot.add_handlers(handlers)

    def get_handlers(self):
        # Echo as default
        return [MessageHandler(TEXT, self.do_echo)]

    def get_message_details(self, update):
        return (
            update.message.from_user,
            update.message.text,
        )

    async def do_echo(self, update: Update, context: CallbackContext):
        from_user, text  = self.get_message_details(update)
        await update.message.reply_text(
            text=f"{from_user.first_name}, Вы написали:\n<i>{text}</i>")


class RoshamboBot(RoshamboMixin, TelegramBot):
    pass


if __name__ == "__main__":
    bot = RoshamboBot()
