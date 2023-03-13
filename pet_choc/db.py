import datetime
import string
from random import random

from sqlalchemy import *
from sqlalchemy.orm import *

engine = create_engine("postgresql+psycopg2://test:root@localhost/pet_choc")
session = Session(bind=engine)
BASE_DIR = '/home/avgust/Документы/py_shit/pet_choc/'

Base = declarative_base()


class Sweets(Base):
    __tablename__ = 'sweets'
    id = Column(Integer, primary_key=True)
    name = Column(String(15), nullable=False)
    descr = Column(String(500), nullable=False)
    packaging = Column(String(15), nullable=False)
    price = Column(Integer, nullable=False)
    picture_path = Column(Text, nullable=False)
    status_presence = Column(Boolean, default=True)


class Reviews(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(15), nullable=False)
    email = Column(String(20), nullable=False)
    comm = Column(String(250), nullable=False)


class Basket(Base):
    __tablename__ = 'basket'
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_sweet = Column(Integer)
    count = Column(Integer)
    user_id = Column(Integer)


class User(Base):
    __tablename__ = 'user_choc'
    id = Column(Integer, primary_key=True, autoincrement=True)
    cookie_user = Column(String(100))
    ip_user = Column(String(100))


class Order(Base):
    __tablename__ = 'orders_shop'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20))
    email = Column(String(25))
    phone = Column(String(25))
    list_products = Column(ARRAY(String))
    comment = Column(String(200))
    status = Column(String(20))  # new, paid, cooking, awaiting delivery, delivery, finished
    data_of_create = Column(Date, default=datetime.datetime.utcnow())
    total_price = Column(Integer)


# Base.metadata.create_all(engine)


def create_review(name, email, comm):
    review = Reviews(name=name, email=email, comm=comm)
    session.add(review)
    session.commit()


def get_reviews():
    """Get all reviews"""
    res = session.query(Reviews.name, Reviews.comm, Reviews.id).all()
    return res


def delete_rev(id):
    r = session.query(Reviews).get(id)
    session.delete(r)
    session.commit()
    return None


def delete_sw(id):
    """Delete one product"""
    r = session.query(Sweets).get(id)
    session.delete(r)
    session.commit()
    return None


def create_sweet(name, price, desc, pic, pack):
    """Create one product"""
    img_path = f'{BASE_DIR}pet_choc_files/assets/images/'
    destination = open(f'{img_path}{pic.filename}', 'wb')
    destination.write(pic.file.read())
    destination.close()
    file_path = f'{pic.filename}'
    sweet = Sweets(name=name, price=int(price), descr=desc, picture_path=file_path, packaging=pack)
    session.add(sweet)
    session.commit()


def get_sweets_panel():
    """Get all products for panel"""
    res = session.query(Sweets.name, Sweets.id).all()
    return res


def get_sweets():
    res = session.query(Sweets).filter(Sweets.status_presence == True)
    res = res.all()
    list_sweet = []
    for r in res:
        list_sweet.append((r.id, r.name, r.descr, r.packaging, r.picture_path, r.price, r.status_presence))
    return list_sweet


def switch_sweet(id):
    """Change status of order, it can be:
        new, paid, cooking, awaiting delivery, delivery, finished;
        If status 'finished', then delete the order.
        """
    i = session.query(Sweets).get(id)
    i.status_presence = not i.status_presence
    session.add(i)
    session.commit()


def create_user(ip, cook):
    us = User(cookie_user=cook, ip_user=ip)
    session.add(us)
    session.commit()
    return us.id


def add_sw_basket(id, cookie):
    """Adding new product in basket of user"""
    id_user_q = session.query(User).filter(User.cookie_user == str(cookie))
    for r in id_user_q:
        id_user = r.id
    b = Basket(id_sweet=id, count=1, user_id=id_user)
    session.add(b)
    session.commit()


def is_have_sw(cookie, id_sw):
    """Checking if a user has a product record"""
    id_user_q = session.query(User).filter(User.cookie_user == str(cookie))
    id_basket = 0
    for r in id_user_q:
        id_user = r.id
    res = session.query(Basket).filter(Basket.id_sweet == id_sw, Basket.user_id == int(id_user))
    for r in res:
        id_basket = r.id
    if id_basket:
        return True
    else:
        return False


def update_basket_count(cookie, id_sw):
    id_user_q = session.query(User).filter(User.cookie_user == cookie)
    id_basket_1 = 0
    for r in id_user_q:
        id_user = r.id
    res = session.query(Basket).filter(Basket.id_sweet == id_sw, Basket.user_id == id_user)
    for r in res:
        id_basket_1 = r.id
    i = session.query(Basket).get(id_basket_1)
    i.count += 1
    session.add(i)
    session.commit()


def minus_basket_count(cookie, id_sw):
    id_user_q = session.query(User).filter(User.cookie_user == cookie)
    id_basket_1 = 0
    for r in id_user_q:
        id_user = r.id
    res = session.query(Basket).filter(Basket.id_sweet == id_sw, Basket.user_id == id_user)
    for r in res:
        id_basket_1 = r.id
    i = session.query(Basket).get(id_basket_1)
    if i.count >= 2:
        i.count -= 1
        session.add(i)
        session.commit()
    else:
        session.delete(i)
        session.commit()


def get_basket_list(cookie):
    """Get all records of those products that the user added."""
    id_user_q = session.query(User).filter(User.cookie_user == cookie)
    id_user = 0
    list_bas = []
    for r in id_user_q:
        id_user = r.id
    users_bas = session.query(Basket).filter(Basket.user_id == id_user)
    for r in users_bas:
        id_sw = r.id_sweet
        count = r.count
        sweet_info = session.query(Sweets).filter(Sweets.id == id_sw)
        for i in sweet_info:
            print(i.name)
            list_bas.append((i.id, i.name, i.descr, i.price, i.picture_path, count))

    return list_bas


def is_empty_basket(cookie):
    id_user_q = session.query(User).filter(User.cookie_user == cookie)
    id_user = 0
    for r in id_user_q:
        id_user = r.id
    if session.query(Basket).filter(Basket.user_id == id_user).count() > 0:
        return False
    else:
        return True


def total_price(cookie):
    """Calculation of the amount of added products from the user in the basket."""
    id_user_q = session.query(User).filter(User.cookie_user == cookie)
    id_user = 0
    total = 0
    for r in id_user_q:
        id_user = r.id
    basket = session.query(Basket).filter(Basket.user_id == id_user)
    for b in basket:
        count = b.count
        sweet = session.query(Sweets).filter(Sweets.id == b.id_sweet)
        for s in sweet:
            total += s.price * count
    return total


def create_order(cookie, name, email, phone, details):
    """Create an order. At the beginning, it is given the new status."""
    id_user_q = session.query(User).filter(User.cookie_user == cookie)
    id_user = 0
    total = 0
    for r in id_user_q:
        id_user = r.id
    list_sweets = []
    basket = session.query(Basket).filter(Basket.user_id == id_user)
    for b in basket:
        list_sweets.append([b.id_sweet, b.count])
        count = b.count
        sweet = session.query(Sweets).filter(Sweets.id == b.id_sweet)
        for s in sweet:
            total += s.price * count

    order = Order(name=name, email=email, phone=phone, list_products=list_sweets, comment=details, status='new',
                  total_price=total)
    session.add(order)
    session.commit()


def get_orders():
    list_order = []
    orders = session.query(Order).filter(not_(Order.status == 'finished')).order_by(desc(Order.data_of_create)).all()
    for n in orders:
        list_order.append(
            (n.id, n.name, n.email, n.phone, n.list_products, n.comment, n.status, n.data_of_create, n.total_price))

    return list_order

def get_one_order(pk):
    n = session.query(Order).get(pk)
    order = [n.id, n.name, n.email, n.phone, n.list_products, n.comment, n.status, n.data_of_create, n.total_price]
    prods = n.list_products
    list_prod = []
    for p in prods:
        sweet = session.query(Sweets).get(int(p[0]))
        list_prod.append(f'{sweet.name} * {p[1]} pieces')

    return order, list_prod

def change_st(pk):
    n = session.query(Order).get(pk)
    line_ages = ['new', 'paid', 'cooking', 'awaiting delivery', 'delivery', 'finished']
    for l in range(len(line_ages)):
        if n.status == line_ages[l]:
            n.status = line_ages[l+1]
            print(line_ages[l+1])
            session.add(n)
            session.commit()
            return None

def delete_order_db(id):
    r = session.query(Order).get(id)
    session.delete(r)
    session.commit()
    return None