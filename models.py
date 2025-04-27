from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# Таблица "Группы"
class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True)
    group_name = Column(String, nullable=False, unique=True)

# Таблица "Аудитории"
class Audience(Base):
    __tablename__ = 'audiences'
    id = Column(Integer, primary_key=True)
    audience_number = Column(String, nullable=False, unique=True)

# Таблица "Предметы"
class Discipline(Base):
    __tablename__ = 'disciplines'
    id = Column(Integer, primary_key=True)
    discipline_name = Column(String, nullable=False, unique=True)

# Таблица "Преподаватели"
class Teacher(Base):
    __tablename__ = 'teachers'
    id = Column(Integer, primary_key=True)
    teacher_name = Column(String, nullable=False, unique=True)

# Таблица "Дни недели"
class DayOfWeek(Base):
    __tablename__ = 'days_of_the_week'
    id = Column(Integer, primary_key=True)
    day_name = Column(String, nullable=False, unique=True)

# Таблица "Расписание"
class Schedule(Base):
    __tablename__ = 'schedule'
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    audience_id = Column(Integer, ForeignKey('audiences.id'), nullable=False)
    discipline_id = Column(Integer, ForeignKey('disciplines.id'), nullable=False)
    teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=False)
    day_id = Column(Integer, ForeignKey('days_of_the_week.id'), nullable=False)
    pair_number = Column(Integer, nullable=False)  # Номер пары (от 1 до 6)

    # Связи
    group = relationship("Group", backref="schedules")
    audience = relationship("Audience", backref="schedules")
    discipline = relationship("Discipline", backref="schedules")
    teacher = relationship("Teacher", backref="schedules")
    day = relationship("DayOfWeek", backref="schedules")