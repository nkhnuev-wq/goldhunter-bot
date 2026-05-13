import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from config import BOT_TOKEN, ADMIN_ID
from db import add_user, get_users


# ================= BOT =================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ================= LINKS =================
TIKTOK_LINK = "https://www.tiktok.com/@goldhunter.nikita?_r=1&_t=ZS-96JdSs0wGG4"
TELEGRAM_GROUP = "https://t.me/goldhunternikita"


# ================= ADMIN PANEL =================
admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📈 BUY"), KeyboardButton(text="📉 SELL")],
        [KeyboardButton(text="🎯 TAKE PROFIT"), KeyboardButton(text="⚓️ BE")],
        [KeyboardButton(text="💵 TAKE 30%"), KeyboardButton(text="🤑 FULL PROFIT")],
        [KeyboardButton(text="👥 USERS")]
    ],
    resize_keyboard=True
)


# ================= STATES =================
class SignalState(StatesGroup):
    pair = State()
    entry = State()
    sl = State()
    tp = State()
    screenshot = State()


# ================= UTIL: BROADCAST =================
async def send_to_all_text(text: str):
    users = get_users()
    for u in users:
        try:
            await bot.send_message(chat_id=u[0], text=text)
        except:
            pass


async def send_to_all_photo(photo, caption=None):
    users = get_users()
    for u in users:
        try:
            await bot.send_photo(chat_id=u[0], photo=photo, caption=caption)
        except:
            pass


# ================= START =================
@dp.message(Command("start"))
async def start(message: Message):
    add_user(message.from_user.id)

    await message.answer(
        "Welcome to Goldhunter Nikita bot 📊\n\n"
        f"📲 TikTok: {TIKTOK_LINK}\n"
        f"💬 Telegram Group: {TELEGRAM_GROUP}\n\n"
        "Trading signals will be delivered directly to this bot"
    )


# ================= PANEL =================
@dp.message(Command("panel"))
async def panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer("Admin Panel 📊", reply_markup=admin_kb)


# ================= BUY =================
@dp.message(F.text == "📈 BUY")
async def buy(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await state.update_data(direction="📈 BUY")
    await state.set_state(SignalState.pair)
    await message.answer("Pair?")


# ================= SELL =================
@dp.message(F.text == "📉 SELL")
async def sell(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await state.update_data(direction="📉 SELL")
    await state.set_state(SignalState.pair)
    await message.answer("Pair?")


# ================= SIGNAL FLOW =================
@dp.message(SignalState.pair)
async def pair(message: Message, state: FSMContext):
    await state.update_data(pair=message.text.upper())
    await state.set_state(SignalState.entry)
    await message.answer("Entry 🚀")


@dp.message(SignalState.entry)
async def entry(message: Message, state: FSMContext):
    await state.update_data(entry=message.text)
    await state.set_state(SignalState.sl)
    await message.answer("Stop Loss ⛔️")


@dp.message(SignalState.sl)
async def sl(message: Message, state: FSMContext):
    await state.update_data(sl=message.text)
    await state.set_state(SignalState.tp)
    await message.answer("Take Profit 🎯")


@dp.message(SignalState.tp)
async def tp(message: Message, state: FSMContext):
    await state.update_data(tp=message.text)
    await state.set_state(SignalState.screenshot)
    await message.answer("Send screenshot 📸")


# ================= FINAL SIGNAL SEND =================
@dp.message(SignalState.screenshot)
async def screenshot(message: Message, state: FSMContext):

    if not message.photo:
        await message.answer("Send screenshot 📸")
        return

    data = await state.get_data()

    caption = (
        f"📊 {data['pair']}\n"
        f"{data['direction']}\n\n"
        f"🚀 Entry: {data['entry']}\n"
        f"⛔️ SL: {data['sl']}\n"
        f"🎯 TP: {data['tp']}"
    )

    photo = message.photo[-1].file_id

    await send_to_all_photo(photo, caption)

    await message.answer("Signal sent ✅")
    await state.clear()


# ================= ADMIN APDATES =================
@dp.message(F.text == "🎯 TAKE PROFIT")
async def take_profit(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await send_to_all_text("🎯 TAKE PROFIT REACHED")


@dp.message(F.text == "⚓️ BE")
async def be(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await send_to_all_text("⚓️ MOVE SL TO BREAK EVEN (BE)")


@dp.message(F.text == "💵 TAKE 30%")
async def tp30(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await send_to_all_text("💵 TAKE 30% PROFIT")


@dp.message(F.text == "🤑 FULL PROFIT")
async def full(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await send_to_all_text("🤑 FULL PROFIT - CLOSE ALL POSITIONS")


# ================= USERS =================
@dp.message(F.text == "👥 USERS")
async def users(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    users_list = get_users()
    await message.answer(f"👥 Users: {len(users_list)}")


# ================= RAW ADMIN BROADCAST (FIX CRITICAL) =================
@dp.message()
async def admin_raw(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    # НЕ ЛОМАЕМ FSM (сигналы)
    state = dp.fsm.get_context(bot=bot, chat_id=message.chat.id, user_id=message.from_user.id)
    if await state.get_state():
        return

    if message.photo:
        photo = message.photo[-1].file_id
        await send_to_all_photo(photo)
        return

    if message.text:
        await send_to_all_text(message.text)
        return


# ================= RUN =================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())