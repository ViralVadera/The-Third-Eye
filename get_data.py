import ssdb
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlite3
import pandas as pd

# Define function to append CSV data to an existing table
def append_csv_to_table(csv_data, table_name):
    DATABASE_URL = "sqlite:///the_third_eye.sqlite"
    connection = sqlite3.connect(DATABASE_URL)
    cursor = connection.cursor()
    
    # Assuming the first row of the CSV contains column names
    df = pd.read_csv(csv_data)
    df.to_sql(table_name, connection, if_exists='append', index=False)

    connection.commit()
    connection.close()

def delete_sequence_value(table_name):
    try:
        conn = sqlite3.connect('the_third_eye.sqlite')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sqlite_sequence WHERE name=?", (table_name,))
        
        conn.commit()
        conn.close()
        
    except sqlite3.Error as e:
        print("Error deleting sequence value:", e)



async def select_table(table_name):
   
    
 
        # Construct the SQL query with placeholders
        query = getattr(ssdb, table_name).select()
        
        # Execute the query and fetch the result set
        dresult=await ssdb.database.fetch_all(query)
 
        return dresult
   

async def select_tablename(table_name,name):
    await ssdb.database.connect()
    
    try:
        # Construct the SQL query with placeholders
        query = ssdb.user_master.select().where(ssdb.user_master.c.f_name==name)
        
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
        query = ssdb.user_master.select().where(ssdb.user_master.c.email==name)
        
        # Execute the query and fetch the result set
        dresult=await ssdb.database.fetch_all(query)
    finally:
        await ssdb.database.disconnect()
    
    return dresult[0][0]

async def select_tableuname(table_name,name):
    await ssdb.database.connect()
    
    try:
        # Construct the SQL query with placeholders
        query = table_name.select().where(table_name.c.email==name)
        
        # Execute the query and fetch the result set
        dresult=await ssdb.database.fetch_all(query)
    finally:
        await ssdb.database.disconnect()
    return dresult

async def select_tableid(table_name,id):
    await ssdb.database.connect()
    
    try:
        # Construct the SQL query with placeholders
        query = table_name.select().where(table_name.c.user_id==id)
        
        # Execute the query and fetch the result set
        dresult=await ssdb.database.fetch_one(query)
    finally:
        await ssdb.database.disconnect()

    if dresult:
        return dresult[1]
    else:
        return None