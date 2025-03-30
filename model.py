from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor
class Worker:
    def __init__(self, id: int, service_id: int, surname: str, special_code: int,
                 age: Optional[int], specialization: Optional[str], experience: Optional[int]):
        self.id = id
        self.service_id = service_id
        self.surname = surname
        self.special_code = special_code
        self.age = age
        self.specialization = specialization
        self.experience = experience

class WorkerFactory:
    @staticmethod
    def get_worker_by_surname(surname: str, conn):
        # SQL-запрос для получения данных из таблиц stuff и stuff_info
        query = """
        SELECT s.id, s.service_id, s.surname, s.special_code,
               si.age, si.specialization, si.experience
        FROM stuff s
        LEFT JOIN stuff_info si ON s.id = si.id
        WHERE LOWER(s.surname) LIKE LOWER(%s)
        LIMIT 1;
        """

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (f"%{surname}%",))
            result = cursor.fetchone()

        if not result:
            return None

        # Создаем объект Worker
        worker = Worker(
            id=result['id'],
            service_id=result['service_id'],
            surname=result['surname'],
            special_code=result['special_code'],
            age=result['age'],
            specialization=result['specialization'],
            experience=result['experience']
        )

        return worker