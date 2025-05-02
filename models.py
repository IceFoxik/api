from sqlalchemy import Column, Integer, String, ForeignKey, Time
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False)
    user_type = Column(String, nullable=False)  # 'teacher' или 'student'

    teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=True)

    teacher = relationship("Teacher", back_populates="user")
    group = relationship("Group", back_populates="students")

class Teacher(Base):
    __tablename__ = 'teachers'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    user = relationship("User", back_populates="teacher")
    schedules = relationship("Schedule", back_populates="teacher")

class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    students = relationship("User", back_populates="group")
    schedules = relationship("Schedule", back_populates="group")

class Audience(Base):
    __tablename__ = 'audiences'
    id = Column(Integer, primary_key=True)
    audience_number = Column(String, nullable=False, unique=True)
    schedules = relationship("Schedule", back_populates="audience")

class Discipline(Base):
    __tablename__ = 'disciplines'
    id = Column(Integer, primary_key=True)
    discipline_name = Column(String, nullable=False, unique=True)
    schedules = relationship("Schedule", back_populates="discipline")

class DayOfWeek(Base):
    __tablename__ = 'days_of_the_week'
    id = Column(Integer, primary_key=True)
    day_name = Column(String, nullable=False, unique=True)
    schedules = relationship("Schedule", back_populates="day")

class Couple(Base):
    __tablename__ = 'couples'
    id = Column(Integer, primary_key=True)
    pair_number = Column(Integer, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    schedules = relationship("Schedule", back_populates="couple")

class Schedule(Base):
    __tablename__ = 'schedule'
    id = Column(Integer, primary_key=True)

    day_id = Column(Integer, ForeignKey('days_of_the_week.id'), nullable=False)
    couple_id = Column(Integer, ForeignKey('couples.id'), nullable=False)
    audience_id = Column(Integer, ForeignKey('audiences.id'), nullable=False)
    discipline_id = Column(Integer, ForeignKey('disciplines.id'), nullable=False)
    teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=False)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)

    day = relationship("DayOfWeek", back_populates="schedules")
    couple = relationship("Couple", back_populates="schedules")
    audience = relationship("Audience", back_populates="schedules")
    discipline = relationship("Discipline", back_populates="schedules")
    teacher = relationship("Teacher", back_populates="schedules")
    group = relationship("Group", back_populates="schedules")