from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InputFile

from crud_functions import initiate_db, get_all_products, add_products, add_user, is_included
initiate_db()
add_products()

api = "7501195936:AAFX38VsGr1Birsl-ieYcuT6wv3TJCnKoTE"
bot = Bot(token=api)
dp = Dispatcher(bot, storage=MemoryStorage())
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("Рассчитать"), KeyboardButton("Информация"))
keyboard.add(KeyboardButton("Купить"), KeyboardButton("Регистрация"))
inline_kb = InlineKeyboardMarkup(row_width=1)
inline_kb.add(InlineKeyboardButton("Рассчитать норму калорий", callback_data='calories'),
              InlineKeyboardButton("Формулы расчёта", callback_data='formulas'))

class UserState(StatesGroup):
    age = State()
    growth = State()
    weight = State()

class RegistrationState(StatesGroup):
    username = State()
    email = State()
    age = State()
    balance = 1000

@dp.message_handler(commands=['start'])
async def start(message: types.Message):

    await message.answer(
        "Привет! Я бот, помогающий твоему здоровью.\nНажмите 'Рассчитать', чтобы начать расчет нормы калорий.",
        reply_markup=keyboard
    )

@dp.message_handler(lambda message: message.text.lower() == 'регистрация')
async def sing_up(message: types.Message):
    await message.answer("Введите имя пользователя (только латинский алфавит):")
    await RegistrationState.username.set()

@dp.message_handler(state=RegistrationState.username)
async def set_username(message: types.Message, state: FSMContext):
    username = message.text
    if is_included(username):
        await message.answer("Пользователь существует, введите другое имя")
    else:
        await state.update_data(username=username)
        await message.answer("Введите свой email:")
        await RegistrationState.email.set()

@dp.message_handler(state=RegistrationState.email)
async def set_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    await message.answer("Введите свой возраст:")
    await RegistrationState.age.set()

@dp.message_handler(state=RegistrationState.age)
async def set_age(message: types.Message, state: FSMContext):
    age = int(message.text)
    data = await state.get_data()
    add_user(data['username'], data['email'], age)
    await message.answer("Регистрация прошла успешно.")
    await state.finish()

@dp.message_handler(lambda message: message.text.lower() == 'рассчитать')
async def main_menu(message: types.Message):
    await message.answer("Выберите опцию:", reply_markup=inline_kb)

@dp.callback_query_handler(lambda call: call.data == 'formulas')
async def get_formulas(call: types.CallbackQuery):
    formula_message = ("Формула Миффлина-Сан Жеора:\n"
                           "Для женщин: 10 * вес (кг) + 6.25 * рост (см) - 5 * возраст (лет) - 161")
    await call.message.answer(formula_message)

@dp.callback_query_handler(lambda call: call.data == 'calories')
async def set_age(call: types.CallbackQuery):
    await call.message.answer("Введите свой возраст:")
    await UserState.age.set()

@dp.message_handler(state=UserState.age)
async def set_growth(message: types.Message, state: FSMContext):
    await state.update_data(age=int(message.text))
    await message.answer("Введите свой рост (в см):")
    await UserState.growth.set()

@dp.message_handler(state=UserState.growth)
async def set_weight(message: types.Message, state: FSMContext):
    await state.update_data(growth=int(message.text))
    await message.answer("Введите свой вес (в кг):")
    await UserState.weight.set()

@dp.message_handler(state=UserState.weight)
async def send_calories(message: types.Message, state: FSMContext):
    await state.update_data(weight=int(message.text))
    data = await state.get_data()
    age = data['age']
    growth = data['growth']
    weight = data['weight']
    # Формула для женщин
    calories = 10 * weight + 6.25 * growth - 5 * age - 161
    await message.answer(f"Ваша норма калорий: {calories:.2f} ккал в сутки.")
    await state.finish()

@dp.message_handler(lambda message: message.text.lower() == 'купить')
async def get_buying_list(message: types.Message):
    products = get_all_products()

    for product in products:
        long_string = f"Название: {product[1]} | Описание: {product[2]} | Цена: {product[3]}"
        image_path = f"./image{product[0]}.png"
        await message.answer_photo(photo=InputFile(image_path), caption=long_string)

    inline_kb = InlineKeyboardMarkup()
    inline_kb.row(*(InlineKeyboardButton(product[1], callback_data='product_buying') for product in products))

    await message.answer("Выберите продукт для покупки:", reply_markup=inline_kb)

@dp.callback_query_handler(lambda call: call.data == 'product_buying')
async def send_confirm_message(call: types.CallbackQuery):
    await call.message.answer("Вы успешно приобрели продукт!")

@dp.message_handler()
async def all_messages(message: types.Message):
    await message.answer("Введите команду /start, чтобы начать общение.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

