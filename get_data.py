import ssdb
import threading
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlite3
import time

async def getcount(table_name):
    query=table_name.select()
    co=await ssdb.database.fetch_all(query)
    count=len(co)
    return count

async def memuid(unitid):
    query=ssdb.member_master.select().where(ssdb.member_master.c.unit_id==unitid and ssdb.member_master.c.add_by is None)
    muid=await ssdb.database.fetch_one(query)
    return muid[1]

async def notyread(userid):
    query=ssdb.notification_master.select().where(ssdb.notification_master.c.reciver_id==userid)
    nodata=await ssdb.database.fetch_all(query)
    return nodata

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
    
async def securitysoc(id):
    await ssdb.database.connect()
    
    try:
        query = ssdb.security_master.select().where(ssdb.security_master.c.user_id==id)
        dresult=await ssdb.database.fetch_one(query)
        query = ssdb.security_shift_master.select().where(ssdb.security_shift_master.c.security_id==dresult[0])
        dresult=await ssdb.database.fetch_one(query)

    finally:
        await ssdb.database.disconnect()

    if dresult:
        return dresult[1]
    else:
        return None
    
async def demo():
        while True:
            query = ssdb.notification_master.delete()
            dresult=await ssdb.database.fetch_one(query)
            time.sleep(60)

async def nsid(uid):
        query=ssdb.notification_master.select().where(ssdb.notification_master.c.reciver_id==uid)
        notifi=await ssdb.database.fetch_one(query)
        return notifi