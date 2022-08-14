import asyncio
from dotenv import dotenv_values

from telegram import (
    Bot, Update, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    MessageHandler, ConversationHandler, CommandHandler,
    Updater, CallbackContext, CallbackQueryHandler,
)
from telegram.ext.filters import TEXT
from telegram.error import BadRequest

from game import Roshambo, FIGURES_LIST

config = dotenv_values(".env")


class RoshamboMixin:
    NEXT_MOVE, GAME_OVER = range(2)  # conversation state codes
    rounds = range(1, 6)

    def options_list_buttons(self, list_):
        return [InlineKeyboardButton(
            value, callback_data=key
        ) for key, value in enumerate(list_)]

    def score(self, list_):
        return ' : '.join(map(str, list_))

    def tableau(self):
        return '\n'.join([
            f"Счёт в текущем раунде - {self.score(self.game.attempts_score)}",
            f"Счёт по раундам - {self.score(self.game.rounds_score)}",
            *([f"Вы ~ {self.game.player_move or ''} => <= {self.game.opponent_move or ''} ~ Компьютер"] if self.game.player_move else []),
            *([f"""В {self.game.rounds_count} раунде {
                'победили Вы' if self.game.round_winner == 0 else 'победил компьютер'
            }."""] if self.game.round_winner is not None else []),
            *([] if self.game.game_winner is not None else ["Ваш следующй ход:"]),
        ])

    async def start(self, update: Updater, context: CallbackContext) -> int:
        user = update.effective_user
        user_name = user.first_name
        reply_keyboard = [self.options_list_buttons(self.rounds)]
        reply_markup = InlineKeyboardMarkup(reply_keyboard)
        await update.message.reply_text(
            f'''Привет, {user_name}!
Сыграй в "Камень-ножницы-бумага" с ботом!
Выбери максимальный счёт по раундам:''',
            reply_markup=reply_markup)
        self.game = None
        return self.NEXT_MOVE

    async def next_move(self, update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        await query.answer()
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
            await query.edit_message_text(
                text=self.tableau(),
                reply_markup=reply_markup,
            )
        except BadRequest:
            pass
        return self.NEXT_MOVE

    async def game_over(self, update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text=f"""{self.tableau()}
ИГРА ОКОНЧЕНА! {'Победили Вы' if self.game.game_winner == 0 else 'Победил компьютер'}.""",
        )
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
        print(self.bot)
        self.add_handler()
        self.bot.run_polling()

    def create_bot(self):
        self.bot = ApplicationBuilder().token(
            config.get("TOKEN")).build()

    def add_handler(self):
        handler = self.get_handler()
        self.bot.add_handler(handler)

    def get_handler(self):
        # Echo as default
        return MessageHandler(TEXT, self.do_echo)

    def get_message_details(self, update):
        return (
            update.message.chat_id,
            update.message.text,
            update.message.from_user
        )

    async def do_echo(self, update: Update, context: CallbackContext):
        chat_id, text, from_user = self.get_message_details(update)
        await update.message.reply_text(
            text=f"{chat_id}\n\n{text}\n{from_user.first_name}")


class RoshamboBot(RoshamboMixin, TelegramBot):
    pass


if __name__ == "__main__":
    bot = RoshamboBot()
