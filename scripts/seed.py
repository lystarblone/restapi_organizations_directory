import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.database import SQLALCHEMY_DATABASE_URL
from app.models import Building, Activity, Organization

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True, connect_args={"check_same_thread": False})

def get_db_session():
    return Session(bind=engine)

def seed_data():
    session = get_db_session()
    try:
        session.query(Organization).delete()
        session.query(Activity).delete()
        session.query(Building).delete()
        session.commit()

        building1 = Building(
            address="г. Москва, ул. Ленина 1, офис 3",
            latitude=55.7558,
            longitude=37.6173
        )
        building2 = Building(
            address="г. Москва, ул. Блюхера 32/1",
            latitude=55.7650,
            longitude=37.5900
        )
        session.add_all([building1, building2])
        session.commit()

        eda = Activity(name="Еда")
        avto = Activity(name="Автомобили")
        session.add_all([eda, avto])
        session.commit()

        myasnaya = Activity(name="Мясная продукция", parent=eda)
        molochnaya = Activity(name="Молочная продукция", parent=eda)
        gruzovye = Activity(name="Грузовые", parent=avto)
        legkovye = Activity(name="Легковые", parent=avto)
        session.add_all([myasnaya, molochnaya, gruzovye, legkovye])
        session.commit()

        zapchasti = Activity(name="Запчасти", parent=legkovye)
        aksessuary = Activity(name="Аксессуары", parent=legkovye)
        session.add_all([zapchasti, aksessuary])
        session.commit()

        org1 = Organization(
            name="ООО “Рога и Копыта”",
            phone_numbers=["2-222-222", "3-333-333"],
            building=building1,
            activities=[eda, myasnaya]
        )
        org2 = Organization(
            name="ООО “МолокоДел”",
            phone_numbers=["8-923-666-13-13"],
            building=building1,
            activities=[eda, molochnaya]
        )
        org3 = Organization(
            name="ООО “Грузовики Плюс”",
            phone_numbers=["1-111-111"],
            building=building2,
            activities=[avto, gruzovye]
        )
        org4 = Organization(
            name="АвтоЗапчасти",
            phone_numbers=["4-444-444"],
            building=building2,
            activities=[avto, legkovye, zapchasti]
        )
        session.add_all([org1, org2, org3, org4])
        session.commit()

        print("✅ Тестовые данные успешно добавлены!")
        print(f"   - Зданий: {session.query(Building).count()}")
        print(f"   - Деятельностей: {session.query(Activity).count()} (с деревом до 3 уровней)")
        print(f"   - Организаций: {session.query(Organization).count()}")

    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка при заполнении: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_data()