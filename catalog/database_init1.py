from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
from database_setup1 import *

engine = create_engine('sqlite:///television.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Delete BykesCompanyName if exisitng.
session.query(Television).delete()
# Delete BykeName if exisitng.
session.query(Tvlist).delete()
# Delete User if exisitng.
session.query(GmailUser).delete()

# Create sample users data
user1 = GmailUser(
    name="ch jahnavi", email="chjahnavi80@gmail.com")
session.add(user1)
session.commit()
print ("Successfully Add First gmail User")
# Create sample television companys
TvCompany1 = Television(
    name="samsung", user_id=1)
session.add(TvCompany1)
session.commit()

TvCompany2 = Television(
    name="sony", user_id=1)
session.add(TvCompany2)
session.commit

TvCompany3 = Television(
    name="panasonic", user_id=1)
session.add(TvCompany3)
session.commit()


# Populare a bykes with models for testing
# Using different users for bykes names year also
item1 = Tvlist(
    tvtypes="lcd",
    description="picture clarity",
    price="2500", rating="superb", inches="15", date=datetime.datetime.now(),
    televisionid=1,
    user_id=1)
session.add(item1)
session.commit()

item2 = Tvlist(
    tvtypes="led",
    description="picture clearence",
    price="260",
    rating="superb",
    inches="12",
    date=datetime.datetime.now(),
    televisionid=2,
    user_id=1)
session.add(item2)
session.commit()

print("Your television database has been inserted!")
