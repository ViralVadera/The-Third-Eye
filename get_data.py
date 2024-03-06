import ssdb
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create an SQLAlchemy engine
engine = create_engine('sqlite:///ssdb.py')  # Replace 'your_database.db' with the path to your SQLite database file

# Create a session factory
Session = sessionmaker(bind=engine)

# Create a session
session = Session()


async def select_table(table_name):
    await ssdb.database.connect()
    
    try:
        # Construct the SQL query with placeholders
        query = getattr(ssdb, table_name).select()
        
        # Execute the query and fetch the result set
        dresult=await ssdb.database.fetch_all(query)
    finally:
        await ssdb.database.disconnect()
    
    return dresult

async def select_tablename(table_name,name):
    await ssdb.database.connect()
    
    try:
        # Construct the SQL query with placeholders
        query = table_name.select(table_name.c.user_id).where(table_name.c.f_name==name)
        
        # Execute the query and fetch the result set
        dresult=await ssdb.database.fetch_all(query)
    finally:
        await ssdb.database.disconnect()

    if dresult:
        return dresult[0][0]
    else:
        return None
    


async def select_tableemail(table_name,name):
    await ssdb.database.connect()
    
    try:
        # Construct the SQL query with placeholders
        query = table_name.select(table_name.c.user_id).where(table_name.c.email==name)
        
        # Execute the query and fetch the result set
        dresult=await ssdb.database.fetch_all(query)
    finally:
        await ssdb.database.disconnect()
    
    return dresult[0][0]
