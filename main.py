from fastapi import FastAPI,Cookie, Form, Request, Depends, HTTPException, status,File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import csv
import io
import uvicorn
from typing import Any, Optional
from datetime import datetime, date
from passlib.context import CryptContext
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import ssdb
import secrets
import get_data
import auth
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table, Boolean, Date, ForeignKey, ForeignKeyConstraint, update, join, select

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


# Initialize Passlib's CryptContext
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

@app.on_event("startup")
async def startup_db():
    await ssdb.database.connect()

@app.on_event("shutdown")
async def shutdown_db():
    await ssdb.database.disconnect()


templates = Jinja2Templates(directory="templates")


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("home/index.html", {"request": request})

@app.get("/hello")
def read_hm(request: Request):
    return templates.TemplateResponse("home/index.html", {"request": request})

@app.get("/logout/")
async def logout(request: Request,session_token: str = Cookie(None)):
    if session_token in auth.session_storage:
        del auth.session_storage[session_token]
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    else:
        raise HTTPException(status_code=400, detail="Invalid session token")
    
@app.post("/upload-csv/")
async def upload_csv(csv_file: UploadFile = File(...), table_name: str = "your_table_name"):
    # Read the contents of the uploaded CSV file
    contents = await csv_file.read()

    # Pass the CSV data and table name to append_csv_to_table function to append data to existing table
    get_data.append_csv_to_table(contents.decode(), table_name)

    return {"filename": csv_file.filename, "status": "appended to table successfully"}

@app.route("/admin", methods=['GET', 'POST'])
async def admin(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)

    return templates.TemplateResponse("AdminDashboard/index.html", {"request": request, "user": use})
    

@app.route("/admin/ausers-profile", methods=['GET', 'POST'])
def auser(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    return templates.TemplateResponse("AdminDashboard/users-profile.html", {"request": request})
    
@app.route("/admin/asocieties", methods=['GET', 'POST'])
async def asocieties(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    email = current_user["email"]
    society=await get_data.select_table('society_master')
    use=await get_data.select_tableuname(ssdb.user_master,email)

    return templates.TemplateResponse("AdminDashboard/societies.html", {"request": request,"society": society,"user": use})

  
@app.route("/admin/asocieties_insert", methods=['GET', 'POST'])
async def asocieties_insert(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    queryy=ssdb.user_master.select()
    usern = await ssdb.database.fetch_all(queryy)
    quey=ssdb.city_master.select()
    city = await ssdb.database.fetch_all(quey)
    return templates.TemplateResponse("AdminDashboard/society_insert.html", {"request": request, "users": usern, "cityy": city})

@app.route("/admin/asocieties_upload", methods=['GET', 'POST'])
async def asocieties_upload(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("AdminDashboard/soc_upload.html", {"request": request,"user": use})
@app.post("/societiesupload")
async def asocieties_upload(request: Request, csvfile: UploadFile = File(...)):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    email = current_user["email"]
    if not csvfile.filename.endswith('.csv'):
        return templates.TemplateResponse(
                "AdminDashboard/soc_upload.html",
                {"request": request, "pop_up_message": "Please upload .CSV file."}
            )
    # Read and parse the CSV file
    contents = await csvfile.read()
    csv_data = io.StringIO(contents.decode('utf-8'))
    csv_reader = csv.reader(csv_data)
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    next(csv_reader, None) #removing header
    for row in csv_reader:
        try:
            registration_date_str = row[10]
            registration_date = datetime.strptime(registration_date_str, '%d-%m-%Y').date()
            date=registration_date.strftime('%Y-%m-%d')
            date=datetime.strptime(date, "%Y-%m-%d").date()
            buildername=row[7]
            user=await get_data.select_tablename(ssdb.user_master,buildername)
            society = ssdb.society_master.insert().values(
                society_name=row[1],
                builder_firm=row[7],
                address_line1=row[2],
                address_line2=row[3],
                road=row[5],
                city=row[6],
                landmark=row[4],
                build_by=user,
                registration_no=row[9],
                registration_year=date,
                created_by=createdby,
                updated_by=createdby
            )
            await ssdb.database.execute(society)
        except ValueError as e:
            print(f"Error converting date for row {row}: {e}")

    return RedirectResponse('/admin/asocieties')

@app.post("/admin/socinsert")
async def adminsocinsert(request: Request, Society_name : str = Form(...), builderName : str = Form(...), builderfirm_name: str = Form(...), regnumber: str = Form(...), regdate: str = Form(...), address_1: str = Form(...), address_2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...)):
  try:
    current_user = auth.verify_session(request)
    email = current_user["email"]
    user=await get_data.select_tablename(ssdb.user_master,builderName)
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    date =datetime.strptime(regdate, '%Y-%m-%d')
    registration_years = date.strftime('%d-%m-%Y')
    registration_years = date.date()
    society = ssdb.society_master.insert().values(
        society_name=Society_name,
        builder_firm=builderfirm_name,
        address_line1=address_1,
        address_line2=address_2,
        road=Road,
        city=citys,
        landmark=landmarks,
        build_by=user,
        registration_no=regnumber,
        registration_year=registration_years,
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(society)
    
    return RedirectResponse('/admin/asocieties')
  
  except Exception as e:
        # Handle database-related errors
        return templates.TemplateResponse(
                "AdminDashboard/society_insert.html",
                {"request": request, "pop_up_message": "Error occurred, Please Verify all Input"})
  
@app.get("/admin/socedit/{soc_id}")
async def adminsocedit(request: Request, soc_id: int):
 
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    queryy=ssdb.user_master.select()
    usern = await ssdb.database.fetch_all(queryy)
    quey=ssdb.city_master.select()
    city = await ssdb.database.fetch_all(quey)
    query=ssdb.society_master.select().where(ssdb.society_master.c.society_id == soc_id)
    socc = await ssdb.database.fetch_one(query)
    bname=await get_data.select_tableid(ssdb.user_master,socc[7])
    
    return templates.TemplateResponse("AdminDashboard/society_edit.html", {"request": request, "soc": socc, "bname": bname, "users": usern, "cityy": city})


@app.post("/admin/socupd/{soc_id}")
async def adminsocedit(request: Request, soc_id: int, Society_name : str = Form(...), builderName : str = Form(...), builderfirm_name: str = Form(...), regnumber: str = Form(...), regdate: str = Form(...), address_1: str = Form(...), address_2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...)):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    email = current_user["email"]
    
    user=await get_data.select_tablename(ssdb.user_master,builderName)
    updby=await get_data.select_tableemail(ssdb.user_master,email)

    
    date =datetime.strptime(regdate, '%Y-%m-%d')
    registration_years = date.strftime('%d-%m-%Y')
    registration_years = date.date()
    udate=datetime.today().date()
    
    query = ssdb.society_master.update().where(ssdb.society_master.c.society_id == soc_id).values(
        society_name=Society_name,
        builder_firm=builderfirm_name,
        address_line1=address_1,
        address_line2=address_2,
        road=Road,
        city=citys,
        landmark=landmarks,
        build_by=user,
        registration_no=regnumber,
        registration_year=registration_years,
        updated_by=updby,
        updated_date=udate
    )
    dresult=await ssdb.database.fetch_one(query)
    if dresult is None:
        return RedirectResponse(url="/admin/asocieties")

@app.get("/admin/socdel/{soc_id}")
async def adminsocdel(request: Request, soc_id: int):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    query=ssdb.society_master.delete().where(ssdb.society_master.c.society_id == soc_id)
    result = await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Society/Appartment_Master')
    if result is None:
        return RedirectResponse(url="/admin/asocieties")
    

@app.route("/admin/asecurityagency", methods=['GET', 'POST'])
async def asecurityagency(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    secagency=await get_data.select_table('security_agency_master')

    return templates.TemplateResponse("AdminDashboard/security_agency.html", {"request": request, "user": use, "agency": secagency})

@app.route("/admin/asecurityagencyinsert", methods=['GET', 'POST'])
async def asecurityagency(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    cit=ssdb.city_master.select()
    city=await ssdb.database.fetch_all(cit)
    sit=ssdb.state_master.select()
    stat=await ssdb.database.fetch_all(sit)
    return templates.TemplateResponse("AdminDashboard/securityagency_insert.html", {"request": request, "cit": city, "state": stat})
@app.post("/agencyinsert")
async def adminsocinsert(request: Request, agency_name : str = Form(...), licenum : int = Form(...), agencytyps: str = Form(...), emaill: str = Form(...), pswd: str = Form(...), address_1: str = Form(...), address_2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), statess:str = Form(...)):
  try:
    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    cit=ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    cityid=await ssdb.database.fetch_one(cit)
    sit=ssdb.state_master.select().where(ssdb.state_master.c.state_name==statess)
    statid=await ssdb.database.fetch_one(sit)
    hashed_pass=auth.encrypt_password(pswd)
    
    agency = ssdb.security_agency_master.insert().values(
        security_agency_name=agency_name,
        agency_license_no=licenum,
        agency_address_line1=address_1,
        agency_address_line2=address_2,
        landmark=landmarks,
        road=Road,
        city_id=cityid[0],
        state_id=statid[0],
        contact_no=mobile,
        email=emaill,
        password=hashed_pass,
        agency_type=agencytyps,
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(agency)
    
    return RedirectResponse('/admin/asecurityagency')
  except Exception as e:
        # Handle database-related errors
        return templates.TemplateResponse(
                "AdminDashboard/securityagency_insert.html",
                {"request": request, "pop_up_message": "Error occurred, Please Verify all Input"})
  
@app.get("/admin/agencyedit/{agen_id}")
async def adminsocedit(request: Request, agen_id: int):
 
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    query=ssdb.security_agency_master.select().where(ssdb.security_agency_master.c.security_agency_id == agen_id)
    agency = await ssdb.database.fetch_one(query)
    cit=ssdb.city_master.select().where(ssdb.city_master.c.city_id==agency.city_id)
    city=await ssdb.database.fetch_one(cit)
    sit=ssdb.state_master.select().where(ssdb.state_master.c.state_id==agency.state_id)
    stat=await ssdb.database.fetch_one(sit)
    
    return templates.TemplateResponse("AdminDashboard/securityagency_edit.html", {"request": request, "agency": agency, "cit": city, "state": stat})
@app.post("/agencyediting/{agen_id}")
async def adminsocedit(request: Request, agen_id: int, agency_name : str = Form(...), licenum : int = Form(...), agencytyps: str = Form(...), emaill: str = Form(...), address_1: str = Form(...), address_2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), statess:str = Form(...)):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    email = current_user["email"]
    updby=await get_data.select_tableemail(ssdb.user_master,email)
    udate=datetime.today().date()
    cit=ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    cityid=await ssdb.database.fetch_one(cit)
    sit=ssdb.state_master.select().where(ssdb.state_master.c.state_name==statess)
    statid=await ssdb.database.fetch_one(sit)
    
    query = ssdb.security_agency_master.update().where(ssdb.security_agency_master.c.security_agency_id == agen_id).values(
        security_agency_name=agency_name,
        agency_license_no=licenum,
        agency_address_line1=address_1,
        agency_address_line2=address_2,
        landmark=landmarks,
        road=Road,
        city_id=cityid[0],
        state_id=statid[0],
        contact_no=mobile,
        email=emaill,
        agency_type=agencytyps,
        updated_by=updby,
        updated_date=udate
    )
    dresult=await ssdb.database.fetch_one(query)
    if dresult is None:
        return RedirectResponse(url="/admin/asecurityagency")
    
@app.get("/agencydel/{agen_id}")
async def adminsocdel(request: Request, agen_id: int):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    query=ssdb.security_agency_master.delete().where(ssdb.security_agency_master.c.security_agency_id == agen_id)
    result = await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Security_Agency_Master')
    if result is None:
        return RedirectResponse(url="/admin/asecurityagency")    
    
@app.route("/admin/agency_upload", methods=['GET', 'POST'])
async def asocieties_upload(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("AdminDashboard/security_agency_upload.html", {"request": request,"user": use})
@app.post("/agencyupload")
async def asocieties_upload(request: Request, csvfile: UploadFile = File(...)):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    email = current_user["email"]
    if not csvfile.filename.endswith('.csv'):
        return templates.TemplateResponse(
                "AdminDashboard/soc_upload.html",
                {"request": request, "pop_up_message": "Please upload .CSV file."}
            )
    # Read and parse the CSV file
    contents = await csvfile.read()
    csv_data = io.StringIO(contents.decode('utf-8'))
    csv_reader = csv.reader(csv_data)
    current_user = auth.verify_session(request)
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    next(csv_reader, None) #removing header
    
    for row in csv_reader:
        try:
            hashed_pass=auth.encrypt_password(row[11])
            cit=ssdb.city_master.select().where(ssdb.city_master.c.city_name==row[7])
            cityid=await ssdb.database.fetch_one(cit)
            print(cityid)
            sit=ssdb.state_master.select().where(ssdb.state_master.c.state_name==row[8])
            statid=await ssdb.database.fetch_one(sit)
            society = ssdb.security_agency_master.insert().values(
            security_agency_name=row[1],
            agency_license_no=row[2],
            agency_address_line1=row[3],
            agency_address_line2=row[4],
            landmark=row[5],
            road=row[6],
            city_id=cityid[0],
            state_id=statid[0],
            contact_no=row[0],
            email=row[10],
            password=hashed_pass,
            agency_type=row[12],
            created_by=createdby,
            updated_by=createdby
            )
            await ssdb.database.execute(society)
        except ValueError as e:
            print(f"Error converting date for row {row}: {e}")

    return RedirectResponse('/admin/asecurityagency')


@app.route("/admin/asecurityguard", methods=['GET', 'POST'])
async def asecurityguard(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    email=email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    query = select(
        ssdb.security_master.c.security_id,
        ssdb.user_master.c.f_name,
        ssdb.security_agency_master.c.security_agency_name,
        ssdb.security_master.c.join_date,
        ssdb.security_master.c.created_by,
        ssdb.security_master.c.updated_by,
        ssdb.security_master.c.created_date,
        ssdb.security_master.c.updated_date
    ).select_from(
    ssdb.security_master.join(
        ssdb.user_master,
        ssdb.security_master.c.user_id == ssdb.user_master.c.user_id
    ).join(
        ssdb.security_agency_master,
        ssdb.security_master.c.security_agency_id == ssdb.security_agency_master.c.security_agency_id
    )
    )

    gurds=await ssdb.database.fetch_all(query)

    return templates.TemplateResponse("AdminDashboard/security_guard.html", {"request": request, "user": use, "gurd": gurds})

@app.route("/admin/guardinsert", methods=['GET', 'POST'])
async def asecurityguard(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    query=ssdb.security_agency_master.select()
    agency_name= await ssdb.database.fetch_all(query)
    query=ssdb.city_master.select()
    city=await ssdb.database.fetch_all(query)

    return templates.TemplateResponse("AdminDashboard/security_guard_insert.html", {"request": request, "agency": agency_name, "city": city})
altmobile: Optional[str] = Form(None)
@app.post("/guardsinsert")
async def adminsocinsert(request: Request, firstname : str = Form(...), joindt: date = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: str = Form(...), altemail: Optional[str] = Form(None), pswd: str = Form(...), address_1: str = Form(...), address_2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), altmobile: Optional[str] = Form(None), secagencys:str = Form(...)):

    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    cit=ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    cityid=await ssdb.database.fetch_one(cit)
    print(cityid)
    sit=ssdb.security_agency_master.select().where(ssdb.security_agency_master.c.security_agency_name==secagencys)
    agid=await ssdb.database.fetch_one(sit)
    hashed_pass=auth.encrypt_password(pswd)
    
    user = ssdb.user_master.insert().values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        Gender=gender,
        address_line1=address_1,
        address_line2=address_2,
        landmark=landmarks,
        road=Road,
        city_id=cityid[0],
        email=emaill,
        alternate_email=altemail,
        password=hashed_pass,
        mobile_no=mobile,
        alternate_mobile_no=altmobile,
        user_type='security',
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(user)
    userid=await get_data.select_tableemail(ssdb.user_master,emaill)
    seecu = ssdb.security_master.insert().values(
        user_id=userid,
        security_agency_id=agid[0],
        join_date=joindt,
        created_by=createdby,
        updated_by=createdby
    )
    sresult =await ssdb.database.fetch_one(seecu)
    
    return RedirectResponse('/admin/asecurityguard')

@app.get("/admin/guardedit/{gurd_id}")
async def adminsocedit(request: Request, gurd_id: int):
 
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    query=ssdb.security_agency_master.select()
    agency= await ssdb.database.fetch_all(query)
    query=ssdb.city_master.select()
    city=await ssdb.database.fetch_all(query)
    query=ssdb.security_master.select().where(ssdb.security_master.c.security_id==gurd_id)
    gurd=await ssdb.database.fetch_one(query)
    query=ssdb.security_agency_master.select().where(ssdb.security_agency_master.c.security_agency_id==gurd[2])
    agency_name= await ssdb.database.fetch_one(query)
    query=ssdb.user_master.select().where(ssdb.user_master.c.user_id==gurd[1])
    user=await ssdb.database.fetch_one(query)
    query=ssdb.city_master.select().where(ssdb.city_master.c.city_id==user[14])
    cityy=await ssdb.database.fetch_one(query)

    return templates.TemplateResponse("AdminDashboard/security_guard_edit.html", {"request": request, "agency_name": agency_name, "city": city, "cityy": cityy, "user": user, "agency": agency, "gurd": gurd})
@app.post("/guardsedit/{gurd_id}")
async def admingurdedit(request: Request, gurd_id: int, firstname : str = Form(...), joindt: date = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: str = Form(...), altemail: Optional[str] = Form(None), address_1: str = Form(...), address_2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), altmobile: Optional[str] = Form(None), secagencys:str = Form(...)):

    current_user = auth.verify_session(request)
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    cit=ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    cityid=await ssdb.database.fetch_one(cit)
    print(cityid)
    sit=ssdb.security_agency_master.select().where(ssdb.security_agency_master.c.security_agency_name==secagencys)
    agid=await ssdb.database.fetch_one(sit)
    udate=datetime.today().date()
    userid=await get_data.select_tableemail(ssdb.user_master,emaill)
    
    user = ssdb.user_master.update().where(ssdb.user_master.c.user_id==userid).values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        Gender=gender,
        address_line1=address_1,
        address_line2=address_2,
        landmark=landmarks,
        road=Road,
        city_id=cityid[0],
        email=emaill,
        alternate_email=altemail,
        mobile_no=mobile,
        alternate_mobile_no=altmobile,
        updated_by=createdby,
        updated_date=udate
    )
    result =await ssdb.database.fetch_one(user)
    seecu = ssdb.security_master.update().where(ssdb.security_master.c.security_id==gurd_id).values(
        user_id=userid,
        security_agency_id=agid[0],
        join_date=joindt,
        updated_by=createdby
    )
    sresult =await ssdb.database.fetch_one(seecu)
    
    return RedirectResponse('/admin/asecurityguard')

@app.get("/guardsdelte/{gurd_id}")
async def gurddel(request: Request, gurd_id: int):
    qyery=ssdb.security_master.select().where(ssdb.security_master.c.security_id==gurd_id)
    uid=await ssdb.database.fetch_one(qyery)
    query=ssdb.user_master.delete().where(ssdb.user_master.c.user_id==uid[1])
    udel=await ssdb.database.fetch_one(query)
    query=ssdb.security_master.delete().where(ssdb.security_master.c.security_id==gurd_id)
    sdel=await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Security_Master')
    get_data.delete_sequence_value('User_Master')
    if sdel is None:
        return RedirectResponse(url='/admin/asecurityguard')

@app.route("/admin/gurd_upload", methods=['GET', 'POST'])
async def gurd_upload(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("AdminDashboard/security_guard_upload.html", {"request": request,"user": use})
@app.post("/gurdupload")
async def gurdupload(request: Request, csvfile: UploadFile = File()):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    if csvfile is None:
        return RedirectResponse('/admin/gurd_upload')
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    if not csvfile.filename.endswith('.csv'):
        return templates.TemplateResponse(
                "AdminDashboard/security_guard_upload.html",
                {"request": request, "pop_up_message": "Please upload .CSV file."}
            )
    udate=datetime.today().date()
    # Read and parse the CSV file
    contents = await csvfile.read()
    csv_data = io.StringIO(contents.decode('utf-8'))
    csv_reader = csv.reader(csv_data)
    current_user = auth.verify_session(request)
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    next(csv_reader, None) #removing header
    
    for row in csv_reader:
    
    
      try:
        date_str = row[4]
        date = datetime.strptime(date_str, '%d-%m-%Y').date()
        date=date.strftime('%Y-%m-%d')
        ddob=datetime.strptime(date, "%Y-%m-%d").date()
        date_str = row[17]
        date = datetime.strptime(date_str, '%d-%m-%Y').date()
        date=date.strftime('%Y-%m-%d')
        jdate=datetime.strptime(date, "%Y-%m-%d").date()
        sit=ssdb.security_agency_master.select().where(ssdb.security_agency_master.c.security_agency_name==row[16])
        agid=await ssdb.database.fetch_one(sit)
        hashed_pass=auth.encrypt_password(row[8])
        cit=ssdb.city_master.select().where(ssdb.city_master.c.city_name==row[15])
        cityid=await ssdb.database.fetch_one(cit)
        user = ssdb.user_master.insert().values(
        f_name=row[1],
        m_name=row[2],
        l_name=row[3],
        dob=ddob,
        Gender=row[5],
        address_line1=row[11],
        address_line2=row[12],
        landmark=row[13],
        road=row[14],
        city_id=cityid[0],
        email=row[6],
        alternate_email=row[7],
        password=hashed_pass,
        mobile_no=row[9],
        alternate_mobile_no=row[10],
        user_type='security',
        created_by=createdby,
        updated_by=createdby,
        updated_date=udate
        )
        result =await ssdb.database.fetch_one(user)
        userid=await get_data.select_tableemail(ssdb.user_master,row[6])
        seecu = ssdb.security_master.insert().values(
        user_id=userid,
        security_agency_id=agid[0],
        join_date=jdate,
        created_by=createdby,
        updated_by=createdby
        )
        sresult =await ssdb.database.fetch_one(seecu)
    
        return RedirectResponse('/admin/asecurityguard')

    
      except ValueError as e:
            print(f"Error converting date for row {row}: {e}")
    
@app.route("/admin/achairmanbuilder", methods=['GET', 'POST'])
async def achairmanbuilder(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    email=email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("AdminDashboard/chairman_builder.html", {"request": request, "user": use})
    
@app.route("/admin/amember", methods=['GET', 'POST'])
def amember(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    return templates.TemplateResponse("AdminDashboard/member.html", {"request": request})
    
@app.route("/admin/acaretaker", methods=['GET', 'POST'])
def acaretaker(request: Request):
   current_user = auth.verify_session(request)
   if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
   return templates.TemplateResponse("AdminDashboard/caretaker.html", {"request": request})
   
@app.route("/admin/aguest", methods=['GET', 'POST'])
def aguest(request: Request):
   current_user = auth.verify_session(request)
   if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
   return templates.TemplateResponse("AdminDashboard/guest.html", {"request": request})
    


@app.route("/chairman", methods=['GET', 'POST'])
def chairman(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    return templates.TemplateResponse("user_dashboard.html", {"request": request})
    
@app.route("/login", methods=["GET", "POST"])
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
   
    if request.method == "POST":
    
        # Retrieve form data
        form_data = await request.form()

        # Extract email and password from form data
        email = form_data.get("email", "")
        password = form_data.get("password", "")

        # Perform login verification logic here
        query = ssdb.user_master.select().where(ssdb.user_master.c.email == email)
        result = await ssdb.database.fetch_one(query)

        if result:
            hashed_password = result["password"]
            if bcrypt_context.verify(password, hashed_password):
                user_type = result["user_type"]
            
                if user_type == "admin":
                    session_token = secrets.token_urlsafe(32)
                    auth.session_storage[session_token] = {"username": email}
                    # Set the session token as a cookie in the response
                    response = RedirectResponse('/admin')
                    response.set_cookie("session_token", session_token)
                    return response
            
                elif user_type == "chairman":
                    session_token = secrets.token_urlsafe(32)
                    auth.session_storage[session_token] = {"username": email}
                    # Set the session token as a cookie in the response
                    response = RedirectResponse('/chairman')
                    response.set_cookie("session_token", session_token)
                    return response            
            else:
                 return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login failed. Invalid Password."}
            ) 

        else:
            # Failed login
            return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login failed. User Not Found."}
            )    
    # Handle GET request (render login form)

    return templates.TemplateResponse("home/login.html", {"request": request})