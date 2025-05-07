import os
from dotenv import load_dotenv
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from database import async_session
from models import Base, User, Group, Teacher, Audience, Discipline, DayOfWeek, Couple, Schedule
from sqlalchemy import select


load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TEACHER_PASSWORD = os.getenv("TEACHER_PASSWORD")

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# === FSM состояния ===
class AddScheduleState(StatesGroup):
    day_name = State()
    pair_number = State()
    start_time = State()
    end_time = State()
    audience_number = State()
    discipline_name = State()
    teacher_name = State()
    group_name = State()

class GetScheduleState(StatesGroup):
    group_name = State()

class RegisterTeacher(StatesGroup):
    waiting_for_password = State()

# === Команда /start ===
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.reply(
        "Добро пожаловать!\n"
        "Используйте:\n"
        "/register_teacher — Зарегистрироваться как преподаватель\n"
        "/register_student — Зарегистрироваться как студент\n"
        "/add_schedule — Добавить занятие (только для учителей)\n"
        "/get_schedule — Получить расписание"
    )

# Команда для регистрации учителя
@dp.message(Command("register_teacher"))
async def register_teacher(message: types.Message, state: FSMContext):
    telegram_id = str(message.from_user.id)

    async with async_session() as session:
        # Проверяем, не зарегистрирован ли уже пользователь
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalars().first()

        if user and user.user_type == 'teacher':
            await message.reply("Вы уже зарегистрированы как учитель.")
            return

    # Переходим в состояние ожидания пароля
    await message.reply("Введите пароль для регистрации:")
    await state.set_state(RegisterTeacher.waiting_for_password)  # Устанавливаем состояние

# Обработчик ввода пароля
@dp.message(RegisterTeacher.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    # Заранее установленный пароль (можно хранить в переменной окружения)
    correct_password = TEACHER_PASSWORD # Замените на реальный пароль

    if message.text != correct_password:
        await message.reply("Неверный пароль. Регистрация отменена.")
        await state.clear()  # Сбрасываем состояние
        return

    telegram_id = str(message.from_user.id)

    async with async_session() as session:
        # Создаём нового пользователя
        new_user = User(telegram_id=telegram_id, user_type='teacher')
        session.add(new_user)
        await session.commit()

    await message.reply("Вы успешно зарегистрированы как преподаватель.")
    await state.clear()  # Сбрасываем состояние

# === Регистрация студента ===
@dp.message(Command("register_student"))
async def register_student(message: types.Message, state: FSMContext):
    await message.reply("Введите название вашей группы:")
    await state.set_state(RegisterStudentState.group_name)

class RegisterStudentState(StatesGroup):
    group_name = State()

@dp.message(RegisterStudentState.group_name)
async def process_register_student(message: types.Message, state: FSMContext):
    group_name = message.text.strip()
    telegram_id = str(message.from_user.id)

    async with async_session() as session:
        # Проверяем, существует ли группа
        result = await session.execute(select(Group).where(Group.name == group_name))
        group = result.scalars().first()
        if not group:
            await message.reply("Группа не найдена.")
            return

        # Проверяем, не зарегистрирован ли уже пользователь
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        existing_user = result.scalars().first()
        if existing_user:
            await message.reply("Вы уже зарегистрированы.")
            return

        # Создаем нового студента
        new_user = User(
            telegram_id=telegram_id,
            user_type="student",
            group_id=group.id
        )
        session.add(new_user)
        await session.commit()

    await message.reply(f"Вы зарегистрированы как студент из группы {group.name}.")
    await state.clear()

# === Добавление расписания (доступно только учителям) ===
@dp.message(Command("add_schedule"))
async def add_schedule_start(message: types.Message, state: FSMContext):
    telegram_id = str(message.from_user.id)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalars().first()

        if not user or user.user_type != "teacher":
            await message.reply("Эта команда доступна только преподавателям.")
            return

    await message.reply("Введите день недели (например, Понедельник):")
    await state.set_state(AddScheduleState.day_name)

@dp.message(AddScheduleState.day_name)
async def process_day_name(message: types.Message, state: FSMContext):
    await state.update_data(day_name=message.text)
    await message.reply("Введите номер пары (1–6):")
    await state.set_state(AddScheduleState.pair_number)

@dp.message(AddScheduleState.pair_number)
async def process_pair_number(message: types.Message, state: FSMContext):
    try:
        pair_number = int(message.text)
        if not 1 <= pair_number <= 6:
            raise ValueError("Номер пары должен быть от 1 до 6.")
        await state.update_data(pair_number=pair_number)
        await message.reply("Введите время начала пары (например, 09:00):")
        await state.set_state(AddScheduleState.start_time)
    except ValueError as e:
        await message.reply(str(e))

@dp.message(AddScheduleState.start_time)
async def process_start_time(message: types.Message, state: FSMContext):
    await state.update_data(start_time=message.text)
    await message.reply("Введите время окончания пары (например, 10:30):")
    await state.set_state(AddScheduleState.end_time)

@dp.message(AddScheduleState.end_time)
async def process_end_time(message: types.Message, state: FSMContext):
    await state.update_data(end_time=message.text)
    await message.reply("Введите номер аудитории:")
    await state.set_state(AddScheduleState.audience_number)

@dp.message(AddScheduleState.audience_number)
async def process_audience(message: types.Message, state: FSMContext):
    await state.update_data(audience_number=message.text)
    await message.reply("Введите название предмета:")
    await state.set_state(AddScheduleState.discipline_name)

@dp.message(AddScheduleState.discipline_name)
async def process_discipline(message: types.Message, state: FSMContext):
    await state.update_data(discipline_name=message.text)
    await message.reply("Введите имя преподавателя:")
    await state.set_state(AddScheduleState.teacher_name)

@dp.message(AddScheduleState.teacher_name)
async def process_teacher_name(message: types.Message, state: FSMContext):
    await state.update_data(teacher_name=message.text)
    await message.reply("Введите название группы:")
    await state.set_state(AddScheduleState.group_name)

@dp.message(AddScheduleState.group_name)
async def process_group_name(message: types.Message, state: FSMContext):
    await state.update_data(group_name=message.text)
    data = await state.get_data()

    async with async_session() as session:
        # Найти или создать день недели
        day = await session.execute(select(DayOfWeek).where(DayOfWeek.day_name == data['day_name']))
        day = day.scalars().first()
        if not day:
            day = DayOfWeek(day_name=data['day_name'])
            session.add(day)
            await session.commit()

        # Найти или создать пару
        couple = await session.execute(
            select(Couple).where(
                Couple.pair_number == data['pair_number'],
                Couple.start_time == data['start_time'],
                Couple.end_time == data['end_time']
            )
        )
        couple = couple.scalars().first()
        if not couple:
            couple = Couple(
                pair_number=int(data['pair_number']),
                start_time=data['start_time'],
                end_time=data['end_time']
            )
            session.add(couple)
            await session.commit()

        # Найти или создать аудиторию
        audience = await session.execute(select(Audience).where(Audience.audience_number == data['audience_number']))
        audience = audience.scalars().first()
        if not audience:
            audience = Audience(audience_number=data['audience_number'])
            session.add(audience)
            await session.commit()

        # Найти или создать дисциплину
        discipline = await session.execute(select(Discipline).where(Discipline.discipline_name == data['discipline_name']))
        discipline = discipline.scalars().first()
        if not discipline:
            discipline = Discipline(discipline_name=data['discipline_name'])
            session.add(discipline)
            await session.commit()

        # Найти или создать преподавателя
        teacher = await session.execute(select(Teacher).where(Teacher.name == data['teacher_name']))
        teacher = teacher.scalars().first()
        if not teacher:
            teacher = Teacher(name=data['teacher_name'])
            session.add(teacher)
            await session.commit()

        # Найти или создать группу
        group = await session.execute(select(Group).where(Group.name == data['group_name']))
        group = group.scalars().first()
        if not group:
            group = Group(name=data['group_name'])
            session.add(group)
            await session.commit()

        # Добавляем запись в расписание
        schedule = Schedule(
            day_id=day.id,
            couple_id=couple.id,
            audience_id=audience.id,
            discipline_id=discipline.id,
            teacher_id=teacher.id,
            group_id=group.id
        )
        session.add(schedule)
        await session.commit()

    await message.reply("Расписание успешно добавлено!")
    await state.clear()

# === Получение расписания ===
@dp.message(Command("get_schedule"))
async def get_schedule(message: types.Message, state: FSMContext):
    telegram_id = str(message.from_user.id)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalars().first()

        if not user:
            await message.reply("Вы не зарегистрированы.")
            return

        if user.user_type == "student" and user.group:
            # Студент видит расписание своей группы
            group = user.group
            schedules = await session.execute(
                select(Schedule, DayOfWeek, Couple, Audience, Discipline, Teacher)
                .join(DayOfWeek, Schedule.day_id == DayOfWeek.id)
                .join(Couple, Schedule.couple_id == Couple.id)
                .join(Audience, Schedule.audience_id == Audience.id)
                .join(Discipline, Schedule.discipline_id == Discipline.id)
                .join(Teacher, Schedule.teacher_id == Teacher.id)
                .where(Schedule.group_id == group.id)
            )
        else:
            # Учитель должен указать группу
            await message.reply("Введите название группы:")
            await state.set_state(GetScheduleState.group_name)
            return

    response = "📅 Расписание:\n"
    for s, d, c, a, di, t in schedules.all():
        response += (
            f"День: {d.day_name}\n"
            f"Пара: {c.pair_number} ({c.start_time} - {c.end_time})\n"
            f"Аудитория: {a.audience_number}\n"
            f"Предмет: {di.discipline_name}\n"
            f"Преподаватель: {t.name}\n"
            "---\n"
        )

    if not schedules.first():
        await message.reply("Расписание не найдено.")
        return

    await message.reply(response)
    await state.clear()

@dp.message(GetScheduleState.group_name)
async def process_get_schedule(message: types.Message, state: FSMContext):
    group_name = message.text.strip()

    async with async_session() as session:
        result = await session.execute(select(Group).where(Group.name == group_name))
        group = result.scalars().first()
        if not group:
            await message.reply("Группа не найдена.")
            return

        schedules = await session.execute(
            select(Schedule, DayOfWeek, Couple, Audience, Discipline, Teacher)
            .join(DayOfWeek, Schedule.day_id == DayOfWeek.id)
            .join(Couple, Schedule.couple_id == Couple.id)
            .join(Audience, Schedule.audience_id == Audience.id)
            .join(Discipline, Schedule.discipline_id == Discipline.id)
            .join(Teacher, Schedule.teacher_id == Teacher.id)
            .where(Schedule.group_id == group.id)
        )

        schedules = schedules.all()

    if not schedules:
        await message.reply("Расписание для этой группы не найдено.")
        return

    response = f"📅 Расписание для группы {group.name}:\n\n"
    for s, d, c, a, di, t in schedules:
        response += (
            f"День: {d.day_name}\n"
            f"Пара: {c.pair_number} ({c.start_time} - {c.end_time})\n"
            f"Аудитория: {a.audience_number}\n"
            f"Предмет: {di.discipline_name}\n"
            f"Преподаватель: {t.name}\n"
            "---\n"
        )

    await message.reply(response)
    await state.clear()

# === Запуск бота ===
async def main():
    # Удалить webhook, если он был установлен
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())