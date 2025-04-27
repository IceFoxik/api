import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import async_session
from models import Group, Audience, Discipline, Teacher, DayOfWeek, Schedule
from sqlalchemy import select

API_TOKEN = '8040196337:AAHM-ekXN0XOzj9TGTfPBe_pMWKnUMNiiMI'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Определение состояний для FSM
class AddScheduleState(StatesGroup):
    group_name = State()
    audience_number = State()
    discipline_name = State()
    teacher_name = State()
    day_name = State()
    pair_number = State()

class GetScheduleState(StatesGroup):
    group_name = State()
# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.reply(
        "Добро пожаловать! Используйте следующие команды:\n"
        "/add_schedule — Добавить расписание\n"
        "/get_schedule — Получить расписание"
    )

# Добавление расписания
@dp.message(Command("add_schedule"))
async def add_schedule_start(message: types.Message, state: FSMContext):
    await message.reply("Введите название группы:")
    await state.set_state(AddScheduleState.group_name)

@dp.message(AddScheduleState.group_name)
async def process_group_name(message: types.Message, state: FSMContext):
    await state.update_data(group_name=message.text)
    await message.reply("Введите номер аудитории:")
    await state.set_state(AddScheduleState.audience_number)

@dp.message(AddScheduleState.audience_number)
async def process_audience_number(message: types.Message, state: FSMContext):
    await state.update_data(audience_number=message.text)
    await message.reply("Введите название предмета:")
    await state.set_state(AddScheduleState.discipline_name)

@dp.message(AddScheduleState.discipline_name)
async def process_discipline_name(message: types.Message, state: FSMContext):
    await state.update_data(discipline_name=message.text)
    await message.reply("Введите имя преподавателя:")
    await state.set_state(AddScheduleState.teacher_name)

@dp.message(AddScheduleState.teacher_name)
async def process_teacher_name(message: types.Message, state: FSMContext):
    await state.update_data(teacher_name=message.text)
    await message.reply("Введите день недели (например, Понедельник):")
    await state.set_state(AddScheduleState.day_name)

@dp.message(AddScheduleState.day_name)
async def process_day_name(message: types.Message, state: FSMContext):
    await state.update_data(day_name=message.text)
    await message.reply("Введите номер пары (от 1 до 6):")
    await state.set_state(AddScheduleState.pair_number)

@dp.message(AddScheduleState.pair_number)
async def process_pair_number(message: types.Message, state: FSMContext):
    try:
        pair_number = int(message.text)
        if not (1 <= pair_number <= 6):
            raise ValueError("Номер пары должен быть от 1 до 6.")
        
        data = await state.get_data()

        async with async_session() as session:
            # Создаем или находим записи в связанных таблицах
            group = await session.execute(select(Group).filter_by(group_name=data['group_name']))
            group = group.scalars().first()
            if not group:
                group = Group(group_name=data['group_name'])
                session.add(group)
                await session.commit()

            audience = await session.execute(select(Audience).filter_by(audience_number=data['audience_number']))
            audience = audience.scalars().first()
            if not audience:
                audience = Audience(audience_number=data['audience_number'])
                session.add(audience)
                await session.commit()

            discipline = await session.execute(select(Discipline).filter_by(discipline_name=data['discipline_name']))
            discipline = discipline.scalars().first()
            if not discipline:
                discipline = Discipline(discipline_name=data['discipline_name'])
                session.add(discipline)
                await session.commit()

            teacher = await session.execute(select(Teacher).filter_by(teacher_name=data['teacher_name']))
            teacher = teacher.scalars().first()
            if not teacher:
                teacher = Teacher(teacher_name=data['teacher_name'])
                session.add(teacher)
                await session.commit()

            day = await session.execute(select(DayOfWeek).filter_by(day_name=data['day_name']))
            day = day.scalars().first()
            if not day:
                day = DayOfWeek(day_name=data['day_name'])
                session.add(day)
                await session.commit()

            # Создаем запись в расписании
            schedule = Schedule(
                group_id=group.id,
                audience_id=audience.id,
                discipline_id=discipline.id,
                teacher_id=teacher.id,
                day_id=day.id,
                pair_number=pair_number
            )
            session.add(schedule)
            await session.commit()

        await message.reply("Расписание успешно добавлено!")
        await state.clear()

    except ValueError as e:
        await message.reply(str(e))

# Команда /get_schedule
@dp.message(Command("get_schedule"))
async def get_schedule_start(message: types.Message, state: FSMContext):
    await message.reply("Введите название группы:")
    await state.set_state(GetScheduleState.group_name)

@dp.message(GetScheduleState.group_name)
async def process_get_schedule(message: types.Message, state: FSMContext):
    group_name = message.text

    async with async_session() as session:
        # Находим группу
        group = await session.execute(select(Group).filter_by(group_name=group_name))
        group = group.scalars().first()
        if not group:
            await message.reply("Группа не найдена.")
            await state.clear()
            return

        # Запрашиваем расписание
        result = await session.execute(
            select(Schedule, DayOfWeek, Audience, Discipline, Teacher)
            .join(DayOfWeek, Schedule.day_id == DayOfWeek.id)
            .join(Audience, Schedule.audience_id == Audience.id)
            .join(Discipline, Schedule.discipline_id == Discipline.id)
            .join(Teacher, Schedule.teacher_id == Teacher.id)
            .filter(Schedule.group_id == group.id)
        )

        schedules = result.all()

    if not schedules:
        await message.reply("Расписание не найдено.")
        await state.clear()
        return

    response = "Расписание:\n"
    for schedule, day, audience, discipline, teacher in schedules:
        response += (
            f"День: {day.day_name}\n"
            f"Пара: {schedule.pair_number}\n"
            f"Аудитория: {audience.audience_number}\n"
            f"Предмет: {discipline.discipline_name}\n"
            f"Преподаватель: {teacher.teacher_name}\n"
            f"---\n"
        )

    await message.reply(response)
    await state.clear()

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())