from fastapi import FastAPI,Cookie, Form, Request, Response, Depends, HTTPException, status,File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import csv
import io
import uvicorn
import asyncio
from sqlalchemy.exc import SQLAlchemyError
from typing import Any, Optional
from datetime import datetime, date
from passlib.context import CryptContext
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import ssdb
import secrets
import get_data
import otp
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

def todaydate():
    return datetime.today().date()


#ROOT
@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("home/index.html", {"request": request})

@app.get("/hello")
def read_hm(request: Request):
    return templates.TemplateResponse("home/index.html", {"request": request})

#logout logic
@app.get("/logout/")
async def logout(request: Request,session_token: str = Cookie(None)):
    if session_token in auth.session_storage:
        del auth.session_storage[session_token]
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "You are logged out."}
            )
    else:
        raise HTTPException(status_code=400, detail="Invalid session token")
    

#Admin routes...
@app.route("/admin", methods=['GET', 'POST'])
async def admin(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    scount=await get_data.getcount(ssdb.society_master)
    secount=await get_data.getcount(ssdb.security_agency_master)
    gcount=await get_data.getcount(ssdb.security_master)
    ccount=await get_data.getcount(ssdb.chairman_master)
    mcount=await get_data.getcount(ssdb.member_master)
    carcount=await get_data.getcount(ssdb.caretaker_master)
    guestcount=await get_data.getcount(ssdb.guest_master)
    return templates.TemplateResponse("AdminDashboard/index.html", {"request": request, "user": use, "scount": scount, "secount": secount,"gcount": gcount, "ccount": ccount, "mcount": mcount, "carcount": carcount, "guestcount": guestcount})
    
#admin user profile
@app.route("/admin/ausers-profile", methods=['GET', 'POST'])
async def auser(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("AdminDashboard/users-profile.html", {"request": request, "user": use})

#Admin user profile edit
@app.post("/editprofile/{user_id}")
async def pedit(request: Request, user_id: int, fName:str = Form(...), lName: Optional[str] = Form(), adress1: Optional[str] = Form(), adress2: Optional[str] = Form(), phone: Optional[str] = Form(), email: Optional[str] = Form()):
    current_user = auth.verify_session(request)
    query=ssdb.user_master.update().where(ssdb.user_master.c.user_id==user_id).values(
        f_name=fName,
        l_name=lName,
        address_line1=adress1,
        address_line2=adress2,
        mobile_no=phone,
        email=email
    )
    user=await ssdb.database.fetch_one(query)
    if user is None:
        return RedirectResponse("/admin")

#Admin Change pass
@app.route("/admin/chgpass", methods=['GET', 'POST'])
async def auser(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("AdminDashboard/chgpass.html", {"request": request, "user": use})

#Admin pass edit
@app.post("/chgpass/{user_id}")
async def pedit(request: Request, user_id: int, password:str = Form(...), newpswd: str = Form(...)):
    current_user = auth.verify_session(request)
    query=ssdb.user_master.select().where(ssdb.user_master.c.user_id==user_id)
    result=await ssdb.database.fetch_one(query)
    hashed_password = result["password"]
    if bcrypt_context.verify(password, hashed_password):
        passs=auth.encrypt_password(newpswd)
        query=ssdb.user_master.update().where(ssdb.user_master.c.user_id==user_id).values(
                password=passs
        )
        user=await ssdb.database.fetch_one(query)
        return RedirectResponse(f"/admin?message=Password+changed+successfully", status_code=303)
        if user is None:
            return RedirectResponse("/admin")
    return RedirectResponse(f"/admin/chgpass?message=Invalid+password", status_code=303)

#Admin Socity 
@app.route("/admin/asocieties", methods=['GET', 'POST'])
async def asocieties(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    society=await get_data.select_table('society_master')
    use=await get_data.select_tableuname(ssdb.user_master,email)

    return templates.TemplateResponse("AdminDashboard/societies.html", {"request": request,"society": society,"user": use})

#Admin Socity Insert
@app.route("/admin/asocieties_insert", methods=['GET', 'POST'])
async def asocieties_insert(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    queryy=ssdb.user_master.select()
    usern = await ssdb.database.fetch_all(queryy)
    quey=ssdb.city_master.select()
    city = await ssdb.database.fetch_all(quey)
    return templates.TemplateResponse("AdminDashboard/society_insert.html", {"request": request, "users": usern, "cityy": city})

@app.post("/admin/socinsert")
async def adminsocinsert(request: Request, Society_name : str = Form(...), builderName : str = Form(...), builderfirm_name: str = Form(...), regnumber: str = Form(...), regdate: str = Form(...), address_1: str = Form(...), address_2: Optional[str] = Form(), Road: str = Form(...), landmarks: Optional[str] = Form(), citys:str = Form(...)):
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
  
#Admin Socity Upload
@app.route("/admin/asocieties_upload", methods=['GET', 'POST'])
async def asocieties_upload(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("AdminDashboard/soc_upload.html", {"request": request,"user": use})
@app.post("/societiesupload")
async def asocieties_upload(request: Request, csvfile: UploadFile = File(...)):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    if not csvfile.filename.endswith('.csv'):
        return templates.TemplateResponse(
                "AdminDashboard/soc_upload.html",
                {"request": request, "pop_up_message": "Please upload .CSV file.","user": use}
            )
    # Read and parse the CSV file
    num=0
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
            num=num+1
            await ssdb.database.execute(society)
        except Exception as e:
        # Handle database-related errors
         return templates.TemplateResponse(
                "AdminDashboard/security_agency_upload.html",
                {"request": request, "pop_up_message": f"Error occurred on row no: {num}" })

    return RedirectResponse('/admin/asocieties')

#Admin Socity Edit 
@app.get("/admin/socedit/{soc_id}")
async def adminsocedit(request: Request, soc_id: int):
 
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
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
async def adminsocedit(request: Request, soc_id: int, Society_name : str = Form(...), builderName : str = Form(...), builderfirm_name: str = Form(...), regnumber: str = Form(...), regdate: str = Form(...), address_1: str = Form(...), address_2: Optional[str] = Form(), Road: str = Form(...), landmarks: Optional[str] = Form(), citys:str = Form(...)):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    
    user=await get_data.select_tablename(ssdb.user_master,builderName)
    updby=await get_data.select_tableemail(ssdb.user_master,email)

    
    date =datetime.strptime(regdate, '%Y-%m-%d')
    registration_years = date.strftime('%d-%m-%Y')
    registration_years = date.date()

    
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
        updated_date=todaydate()
    )
    dresult=await ssdb.database.fetch_one(query)
    if dresult is None:
        return RedirectResponse(url="/admin/asocieties")

#Admin Socity Delete
@app.get("/admin/socdel/{soc_id}")
async def adminsocdel(request: Request, soc_id: int):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    query=ssdb.society_master.delete().where(ssdb.society_master.c.society_id == soc_id)
    result = await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Society/Appartment_Master')
    if result is None:
        return RedirectResponse(url="/admin/asocieties")


#Admin Security Agency 
@app.route("/admin/asecurityagency", methods=['GET', 'POST'])
async def asecurityagency(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    secagency=await get_data.select_table('security_agency_master')

    return templates.TemplateResponse("AdminDashboard/security_agency.html", {"request": request, "user": use, "agency": secagency})


#Admin Security Agency Insert
@app.route("/admin/asecurityagencyinsert", methods=['GET', 'POST'])
async def asecurityagency(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
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
  

#Admin Security Agency Edit
@app.get("/admin/agencyedit/{agen_id}")
async def adminsocedit(request: Request, agen_id: int):
 
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
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
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    updby=await get_data.select_tableemail(ssdb.user_master,email)
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
    )
    dresult=await ssdb.database.fetch_one(query)
    if dresult is None:
        return RedirectResponse(url="/admin/asecurityagency")


#Admin Security Agency Delete 
@app.get("/agencydel/{agen_id}")
async def adminsocdel(request: Request, agen_id: int):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    query=ssdb.security_agency_master.delete().where(ssdb.security_agency_master.c.security_agency_id == agen_id)
    result = await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Security_Agency_Master')
    if result is None:
        return RedirectResponse(url="/admin/asecurityagency")    

#Admin Security Agency Upload 
@app.route("/admin/agency_upload", methods=['GET', 'POST'])
async def asocieties_upload(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("AdminDashboard/security_agency_upload.html", {"request": request,"user": use})

@app.post("/agencyupload")
async def asocieties_upload(request: Request, csvfile: UploadFile = File(...)):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    if not csvfile.filename.endswith('.csv'):
        return templates.TemplateResponse(
                "AdminDashboard/security_agency_upload.html",
                {"request": request, "pop_up_message": "Please upload .CSV file.","user": use}
            )
    # Read and parse the CSV file
    contents = await csvfile.read()
    csv_data = io.StringIO(contents.decode('utf-8'))
    csv_reader = csv.reader(csv_data)
    current_user = auth.verify_session(request)
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    next(csv_reader, None) #removing header
    num=1
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
            
        # Track successfully processed rows
        except Exception as e:
        # Handle database-related errors
         return templates.TemplateResponse(
                "AdminDashboard/security_agency_upload.html",
                {"request": request, "pop_up_message": f"Error occurred on row no: {num}" })
    return RedirectResponse('/admin/asecurityagency')


#Admin Security Gurd
@app.route("/admin/asecurityguard", methods=['GET', 'POST'])
async def asecurityguard(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    query = select(ssdb.security_master,
                   ssdb.security_agency_master,
                   ssdb.user_master
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


#Admin Security Gurd Insert
@app.route("/admin/guardinsert", methods=['GET', 'POST'])
async def asecurityguard(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
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
    sit=ssdb.security_agency_master.select().where(ssdb.security_agency_master.c.security_agency_name==secagencys)
    agid=await ssdb.database.fetch_one(sit)
    hashed_pass=auth.encrypt_password(pswd)
    
    user = ssdb.user_master.insert().values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
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

#Admin Security Gurd Edit
@app.get("/admin/guardedit/{gurd_id}")
async def adminsocedit(request: Request, gurd_id: int):
 
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
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
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    cit=ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    cityid=await ssdb.database.fetch_one(cit)
    sit=ssdb.security_agency_master.select().where(ssdb.security_agency_master.c.security_agency_name==secagencys)
    agid=await ssdb.database.fetch_one(sit)
    userid=await get_data.select_tableemail(ssdb.user_master,emaill)
    
    user = ssdb.user_master.update().where(ssdb.user_master.c.user_id==userid).values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
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
        updated_date=todaydate()
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

#Admin Security Gurd Delte
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

#Admin Security Gurd Upload
@app.route("/admin/gurd_upload", methods=['GET', 'POST'])
async def gurd_upload(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("AdminDashboard/security_guard_upload.html", {"request": request,"user": use})

@app.post("/gurdupload")
async def gurdupload(request: Request, csvfile: UploadFile = File(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    if not csvfile.filename.endswith('.csv'):
        return templates.TemplateResponse(
                "AdminDashboard/security_guard_upload.html",
                {"request": request, "pop_up_message": "Please upload .CSV file.", "user" : use}
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
        gender=row[5],
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
        updated_date=todaydate()
        )
        result =await ssdb.database.fetch_one(user)
        userid=await get_data.select_tableemail(ssdb.user_master,row[6])
        seecu = ssdb.security_master.insert().values(
        user_id=userid,
        security_agency_id=agid[0],
        join_date=jdate,
        created_by=createdby,
        updated_by=createdby,
        updated_date=todaydate()
        )
        sresult =await ssdb.database.fetch_one(seecu)
    
        return RedirectResponse('/admin/asecurityguard')

    
      except ValueError as e:
            print(f"Error converting date for row {row}: {e}")


#Admin Chairman  
@app.route("/admin/achairmanbuilder", methods=['GET', 'POST'])
async def achairmanbuilder(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email=email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)

    query = select(ssdb.chairman_master,
                   ssdb.society_master,
                   ssdb.user_master
                   ).select_from(
        ssdb.chairman_master.join(
        ssdb.user_master,
        ssdb.chairman_master.c.chairman_userid == ssdb.user_master.c.user_id
    ).join(
        ssdb.society_master,
        ssdb.chairman_master.c.society_id == ssdb.society_master.c.society_id
    )
                   )
    chairmen= await ssdb.database.fetch_all(query)
    return templates.TemplateResponse("AdminDashboard/chairman_builder.html", {"request": request, "user": use, "chairmen": chairmen})

#Admin Chairman Insert
@app.route("/admin/achairmaninsert", methods=['GET', 'POST'])
async def achairmanbuilder(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    quey = ssdb.society_master.select()
    soc= await ssdb.database.fetch_all(quey)
    quer = ssdb.city_master.select()
    cit= await ssdb.database.fetch_all(quer)
    return templates.TemplateResponse("AdminDashboard/chairman_builder_insert.html", {"request": request, "society": soc, "city": cit})

@app.post("/chairmaninsert")
async def adminsocinsert(request: Request, firstname : str = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: str = Form(...), altemail: Optional[str] = Form(None), pswd: str = Form(...), address1: str = Form(...), address2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), altmobile: Optional[str] = Form(None), societys:str = Form(...), assigndt:date =Form(...), assigntilldt:date =Form(...), ischairmans:bool =Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    quey = ssdb.society_master.select().where(ssdb.society_master.c.society_name==societys)
    socid= await ssdb.database.fetch_one(quey)
    quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    citid= await ssdb.database.fetch_one(quer)
    hashed_pass=auth.encrypt_password(pswd)
    
    user = ssdb.user_master.insert().values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
        address_line1=address1,
        address_line2=address2,
        landmark=landmarks,
        road=Road,
        city_id=citid[0],
        email=emaill,
        alternate_email=altemail,
        password=hashed_pass,
        mobile_no=mobile,
        alternate_mobile_no=altmobile,
        user_type='chairman',
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(user)
    userid=await get_data.select_tableemail(ssdb.user_master,emaill)
    chair=ssdb.chairman_master.insert().values(
        chairman_userid=userid,
        society_id=socid[0],
        assign_date=assigndt,
        assign_till=assigntilldt,
        is_chairman=ischairmans,
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(chair)
    return RedirectResponse('/admin/achairmanbuilder')

#Admin Chairman Edit
@app.get("/admin/chairmanedit/{chairman_id}")
async def chairmanedit(request: Request, chairman_id: int):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    query = select(ssdb.chairman_master,
                   ssdb.society_master,
                   ssdb.user_master,
                   ssdb.city_master,
                   ).where(ssdb.chairman_master.c.chairman_id==chairman_id).select_from(
        ssdb.chairman_master.join(
        ssdb.user_master,
        ssdb.chairman_master.c.chairman_userid == ssdb.user_master.c.user_id
    ).join(
        ssdb.society_master,
        ssdb.chairman_master.c.society_id == ssdb.society_master.c.society_id
    ).join(
       ssdb.city_master,
       ssdb.user_master.c.city_id == ssdb.city_master.c.city_id
    )
                   )
    chairmen= await ssdb.database.fetch_one(query)
    quey = ssdb.society_master.select()
    soc= await ssdb.database.fetch_all(quey)
    quer = ssdb.city_master.select()
    cit= await ssdb.database.fetch_all(quer)
   
    return templates.TemplateResponse("AdminDashboard/chairman_builder_edit.html", {"request": request, "society": soc, "city": cit, "c": chairmen})

@app.post("/chairmanedit/{chairman_id}")
async def adminsocinsert(request: Request, chairman_id: int, firstname : str = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: str = Form(...), altemail: Optional[str] = Form(None), address1: str = Form(...), address2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), altmobile: Optional[str] = Form(None), societys:str = Form(...), assigndt:date =Form(...), assigntilldt:date =Form(...), ischairmans:bool =Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    updtby=await get_data.select_tableemail(ssdb.user_master,email)
    quey = ssdb.society_master.select().where(ssdb.society_master.c.society_name==societys)
    socid= await ssdb.database.fetch_one(quey)
    quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    citid= await ssdb.database.fetch_one(quer)
    uid=await get_data.select_tableemail(ssdb.user_master,emaill)
    user = ssdb.user_master.update().values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
        address_line1=address1,
        address_line2=address2,
        landmark=landmarks,
        road=Road,
        city_id=citid[0],
        email=emaill,
        alternate_email=altemail,
        mobile_no=mobile,
        alternate_mobile_no=altmobile,
        updated_by=updtby,
        updated_date=todaydate()
    ).where(ssdb.user_master.c.user_id==uid)
    result =await ssdb.database.fetch_one(user)
    userid=await get_data.select_tableemail(ssdb.user_master,emaill)
    query=ssdb.chairman_master.select().where(ssdb.chairman_master.c.chairman_id==chairman_id)
    cid=await ssdb.database.fetch_one(query)
    chair=ssdb.chairman_master.update().values(
        chairman_userid=userid,
        society_id=socid[0],
        assign_date=assigndt,
        assign_till=assigntilldt,
        is_chairman=ischairmans,
        updated_by=updtby,
        updated_date=todaydate()
    ).where(ssdb.chairman_master.c.chairman_id==cid[0])
    result =await ssdb.database.fetch_one(chair)
    return RedirectResponse('/admin/achairmanbuilder')

#Admin Chairman Delete
@app.get("/chairmandel/{chairman_id}")
async def charidel(request: Request, chairman_id: int):
    query=ssdb.chairman_master.select().where(ssdb.chairman_master.c.chairman_id==chairman_id)
    uid=await ssdb.database.fetch_one(query)
    query=ssdb.user_master.delete().where(ssdb.user_master.c.user_id==uid[1])
    udel=await ssdb.database.fetch_one(query)
    query=ssdb.chairman_master.delete().where(ssdb.chairman_master.c.chairman_id==chairman_id)
    cdel=await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Chairman_Master')
    get_data.delete_sequence_value('User_Master')
    if cdel is None:
        return RedirectResponse(url='/admin/achairmanbuilder')

#Admin Chairman Upload  
@app.route("/admin/charmanupload", methods=['GET', 'POST'])
async def amember(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("AdminDashboard/chairman_builder_upload.html", {"request": request, "user": use})

@app.post("/charmanupload")
async def csupload(request: Request, csvfile: UploadFile = File()):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    if csvfile is None or current_user["user_type"] != 'admin':
        return RedirectResponse('/admin/charmanupload')
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    if not csvfile.filename.endswith('.csv'):
        return templates.TemplateResponse(
                "AdminDashboard/chairman_builder_upload.html",
                {"request": request, "pop_up_message": "Please upload .CSV file.","user": use}
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
        date_str = row[17]
        date = datetime.strptime(date_str, '%d-%m-%Y').date()
        date=date.strftime('%Y-%m-%d')
        assgdate=datetime.strptime(date, "%Y-%m-%d").date()
        date_str = row[18]
        date = datetime.strptime(date_str, '%d-%m-%Y').date()
        date=date.strftime('%Y-%m-%d')
        assgtidate=datetime.strptime(date, "%Y-%m-%d").date()
        date_str = row[4]
        date = datetime.strptime(date_str, '%d-%m-%Y').date()
        date=date.strftime('%Y-%m-%d')
        dob=datetime.strptime(date, "%Y-%m-%d").date()
        quey = ssdb.society_master.select().where(ssdb.society_master.c.society_name==row[16])
        socid= await ssdb.database.fetch_one(quey)
        quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==row[15])
        citid= await ssdb.database.fetch_one(quer)
        hashed_pass=auth.encrypt_password(row[8])
    
        user = ssdb.user_master.insert().values(
        f_name=row[1],
        m_name=row[2],
        l_name=row[3],
        dob=dob,
        gender=row[5],
        address_line1=row[11],
        address_line2=row[12],
        landmark=row[13],
        road=row[14],
        city_id=citid[0],
        email=row[6],
        alternate_email=row[7],
        password=hashed_pass,
        mobile_no=row[9],
        alternate_mobile_no=row[10],
        user_type='chairman',
        created_by=createdby,
        updated_by=createdby,
        updated_date=todaydate()
        )
        result =await ssdb.database.fetch_one(user)
        
        value_str = row[19]
        value_bool = value_str.upper() == 'TRUE'
        userid=await get_data.select_tableemail(ssdb.user_master,row[6])
        chair=ssdb.chairman_master.insert().values(
        chairman_userid=userid,
        society_id=socid[0],
        assign_date=assgdate,
        assign_till=assgtidate,
        is_chairman=value_bool,
        created_by=createdby,
        updated_by=createdby,
        updated_date=todaydate()
        )
        result =await ssdb.database.fetch_one(chair)
      except ValueError as e:
            print(f"Error converting date for row {e}: {e}")
    return RedirectResponse('/admin/achairmanbuilder')


#Admin Member   
@app.route("/admin/amember", methods=['GET', 'POST'])
async def amember(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    query = select(ssdb.member_master,
                   ssdb.unit_master,
                   ssdb.society_master,
                   ssdb.user_master
                   ).select_from(
        ssdb.member_master.join(
        ssdb.unit_master,
        ssdb.unit_master.c.unit_id == ssdb.member_master.c.unit_id
    ).join(
        ssdb.society_master,
        ssdb.society_master.c.society_id == ssdb.unit_master.c.society_id
    ).join(
        ssdb.user_master,
        ssdb.user_master.c.user_id==ssdb.member_master.c.member_userid
    )
                   )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    member= await ssdb.database.fetch_all(query)
    return templates.TemplateResponse("AdminDashboard/member.html", {"request": request, "member": member,"user": use})

#Admin Member Insert
@app.route("/admin/amember_insert", methods=['GET', 'POST'])
async def amember(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    quey = ssdb.unit_master.select()
    un= await ssdb.database.fetch_all(quey)
    query= ssdb.city_master.select()
    cit= await ssdb.database.fetch_all(query)
    return templates.TemplateResponse("AdminDashboard/member_insert.html", {"request": request, "unit": un, "cityy": cit})

@app.post("/amemberinsert")
async def adminmebinsert(request: Request, firstname : str = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: str = Form(...), altemail: Optional[str] = Form(None), pswd: str = Form(...), address1: str = Form(...), address2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), altmobile: Optional[str] = Form(None), unitname: str = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    citid= await ssdb.database.fetch_one(quer)
    hashed_pass=auth.encrypt_password(pswd)
    query=ssdb.unit_master.select().where(ssdb.unit_master.c.unit_name==unitname)
    unitn= await ssdb.database.fetch_one(query)
    user = ssdb.user_master.insert().values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
        address_line1=address1,
        address_line2=address2,
        landmark=landmarks,
        road=Road,
        city_id=citid[0],
        email=emaill,
        alternate_email=altemail,
        password=hashed_pass,
        mobile_no=mobile,
        alternate_mobile_no=altmobile,
        user_type='member',
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(user)
    userid=await get_data.select_tableemail(ssdb.user_master,emaill)
    mamber=ssdb.member_master.insert().values(
        member_userid=userid,
        unit_id=unitn[1],
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(mamber)
    return RedirectResponse('/admin/amember')

#Admin Member Edit
@app.get("/admin/amember_edit/{member_id}")
async def amember(request: Request, member_id : int):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    quey = ssdb.unit_master.select()
    un= await ssdb.database.fetch_all(quey)
    query= ssdb.city_master.select()
    cit= await ssdb.database.fetch_all(query)
    query=ssdb.member_master.select().where(ssdb.member_master.c.member_id==member_id)
    mem= await ssdb.database.fetch_one(query)
    query=ssdb.unit_master.select().where(ssdb.unit_master.c.unit_id==mem[4])
    uin=await ssdb.database.fetch_one(query)
    query=ssdb.user_master.select().where(ssdb.user_master.c.user_id==mem[1])
    use= await ssdb.database.fetch_one(query)
    return templates.TemplateResponse("AdminDashboard/member_edit.html", {"request": request, "unit": un,"m" : mem, "cityy": cit, "user": use, "unit": uin})

@app.post("/amemberedit/{meber_id}")
async def adminmembinsert(request: Request, meber_id : int, firstname : str = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: str = Form(...), altemail: Optional[str] = Form(None), address1: str = Form(...), address2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), altmobile: Optional[str] = Form(None), unitname: str = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    userid=await get_data.select_tableemail(ssdb.user_master,emaill)
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    citid= await ssdb.database.fetch_one(quer)
    query=ssdb.unit_master.select().where(ssdb.unit_master.c.unit_name==unitname)
    unitn= await ssdb.database.fetch_one(query)
    user = ssdb.user_master.update().values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
        address_line1=address1,
        address_line2=address2,
        landmark=landmarks,
        road=Road,
        city_id=citid[0],
        email=emaill,
        alternate_email=altemail,
        mobile_no=mobile,
        alternate_mobile_no=altmobile,
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.user_master.c.user_id==userid)
    result =await ssdb.database.fetch_one(user)
    userid=await get_data.select_tableemail(ssdb.user_master,emaill)
    mamber=ssdb.member_master.update().values(
        member_userid=userid,
        unit_id=unitn[1],
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.member_master.c.member_id==meber_id)
    result =await ssdb.database.fetch_one(mamber)
    return RedirectResponse('/admin/amember')

#Admin Member Delete
@app.get("/amemberdel/{member_id}")
async def charidel(request: Request, member_id: int):
    query=ssdb.member_master.select().where(ssdb.member_master.c.member_id==member_id)
    uid=await ssdb.database.fetch_one(query)
    query=ssdb.user_master.delete().where(ssdb.user_master.c.user_id==uid[1])
    udel=await ssdb.database.fetch_one(query)
    query=ssdb.member_master.delete().where(ssdb.member_master.c.member_id==member_id)
    cdel=await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Member/Owner_Master')
    get_data.delete_sequence_value('User_Master')
    if cdel is None:
        return RedirectResponse(url='/admin/amember')

#Admin Member Upload  
@app.route("/admin/memberupload", methods=['GET', 'POST'])
async def amember(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("AdminDashboard/member_upload.html", {"request": request, "user": use})

@app.post("/memberupload")
async def csupload(request: Request, csvfile: UploadFile = File()):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    if csvfile is None or current_user["user_type"] != 'admin':
        return RedirectResponse('/admin/charmanupload')
    if not csvfile.filename.endswith('.csv'):
        return templates.TemplateResponse(
                "AdminDashboard/member_upload.html",
                {"request": request, "pop_up_message": "Please upload .CSV file.","user": use}
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
        date_str = row[4]
        date = datetime.strptime(date_str, '%d-%m-%Y').date()
        date=date.strftime('%Y-%m-%d')
        dob=datetime.strptime(date, "%Y-%m-%d").date()
        quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==row[16])
        citid= await ssdb.database.fetch_one(quer)
        hashed_pass=auth.encrypt_password(row[8])
        query=ssdb.unit_master.select().where(ssdb.unit_master.c.unit_name==row[11])
        unitn= await ssdb.database.fetch_one(query)
    
        user = ssdb.user_master.insert().values(
        f_name=row[1],
        m_name=row[2],
        l_name=row[3],
        dob=dob,
        gender=row[5],
        address_line1=row[12],
        address_line2=row[13],
        landmark=row[14],
        road=row[15],
        city_id=citid[0],
        email=row[6],
        alternate_email=row[7],
        password=hashed_pass,
        mobile_no=row[9],
        alternate_mobile_no=row[10],
        user_type='member',
        created_by=createdby,
        updated_by=createdby
        )
        result =await ssdb.database.fetch_one(user)
        userid=await get_data.select_tableemail(ssdb.user_master,row[6])
        mamber=ssdb.member_master.insert().values(
        member_userid=userid,
        unit_id=unitn[1],
        created_by=createdby,
        updated_by=createdby
        )
        result =await ssdb.database.fetch_one(mamber)
      except ValueError as e:
            print(f"Error converting date for row {e}: {e}")
    return RedirectResponse('/admin/achairmanbuilder')

#Admin Caretaker   
@app.route("/admin/acaretaker", methods=['GET', 'POST'])
async def acaretaker(request: Request):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   email = current_user["email"]
   use=await get_data.select_tableuname(ssdb.user_master,email)
   query=select(ssdb.caretaker_master,ssdb.user_master).select_from(
       ssdb.caretaker_master.join(
           ssdb.user_master,
           ssdb.user_master.c.user_id==ssdb.caretaker_master.c.user_id
       )
   )
   care=await ssdb.database.fetch_all(query)
   return templates.TemplateResponse("AdminDashboard/caretaker.html", {"request": request, "user": use, "caretaker": care})

 #Admin Caretaker Insert  
@app.route("/admin/acaretakerinsert", methods=['GET', 'POST'])
async def acaretaker(request: Request):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   email = current_user["email"]
   query=ssdb.city_master.select()
   cit=await ssdb.database.fetch_all(query)
   return templates.TemplateResponse("AdminDashboard/caretaker_insert.html", {"request": request, "cit": cit}) 

@app.post("/acaretakeredit")
async def adminmebinsert(request: Request, firstname : str = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: Optional[str] = Form(None), altemail: Optional[str] = Form(None), servicetyp: str = Form(...), address1: str = Form(...), address2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), altmobile: Optional[str] = Form(None)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    citid= await ssdb.database.fetch_one(quer)
    user = ssdb.user_master.insert().values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
        address_line1=address1,
        address_line2=address2,
        landmark=landmarks,
        road=Road,
        city_id=citid[0],
        email=emaill,
        alternate_email=altemail,
        mobile_no=mobile,
        alternate_mobile_no=altmobile,
        user_type='caretaker',
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(user)
    query=ssdb.user_master.select().where(ssdb.user_master.c.mobile_no==mobile)
    userid=await ssdb.database.fetch_one(query)
    caretkae=ssdb.caretaker_master.insert().values(
        user_id=userid[0],
        service_type=servicetyp,
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(caretkae)
    return RedirectResponse('/admin/acaretaker')

#Admin Caretaker edit  
@app.get("/admin/acaretakeredit/{c_id}")
async def acaretaker(request: Request, c_id: int):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   email = current_user["email"]
   query=ssdb.city_master.select()
   cit=await ssdb.database.fetch_all(query)
   query=select(ssdb.caretaker_master,ssdb.user_master,ssdb.city_master).select_from(
       ssdb.caretaker_master.join(
           ssdb.user_master,
           ssdb.user_master.c.user_id==ssdb.caretaker_master.c.user_id
       ).join(
           ssdb.city_master,
           ssdb.city_master.c.city_id==ssdb.user_master.c.city_id
       )
   ).where(ssdb.caretaker_master.c.c_id==c_id)
   care=await ssdb.database.fetch_one(query)
   return templates.TemplateResponse("AdminDashboard/caretaker_edit.html", {"request": request, "cit": cit, "car": care}) 

@app.post("/acaretakeredit/{c_id}")
async def admincaredit(request: Request, response: Response, c_id: int, firstname : str = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: Optional[str] = Form(None), altemail: Optional[str] = Form(None), servicetyp: str = Form(...), address1: str = Form(...), address2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), altmobile: Optional[str] = Form(None)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    citid= await ssdb.database.fetch_one(quer)
    query=ssdb.caretaker_master.select().where(ssdb.caretaker_master.c.c_id==c_id)
    uid=await ssdb.database.fetch_one(query)
    user = ssdb.user_master.update().values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
        address_line1=address1,
        address_line2=address2,
        landmark=landmarks,
        road=Road,
        city_id=citid[0],
        email=emaill,
        alternate_email=altemail,
        mobile_no=mobile,
        alternate_mobile_no=altmobile,
        user_type='caretaker',
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.user_master.c.user_id==uid[1])
    result =await ssdb.database.fetch_one(user)
    caretkae=ssdb.caretaker_master.update().values(
        user_id=uid[1],
        service_type=servicetyp,
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.caretaker_master.c.c_id==c_id)
    result =await ssdb.database.fetch_one(caretkae)
    return RedirectResponse('/admin/acaretaker')

#Admin Caretaker Delete
@app.get("/acaretakerdel/{c_id}")
async def charidel(request: Request, c_id: int):
    query=ssdb.caretaker_master.select().where(ssdb.caretaker_master.c.c_id==c_id)
    uid=await ssdb.database.fetch_one(query)
    query=ssdb.user_master.delete().where(ssdb.user_master.c.user_id==uid[1])
    udel=await ssdb.database.fetch_one(query)
    query=ssdb.caretaker_master.delete().where(ssdb.caretaker_master.c.c_id==c_id)
    cdel=await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Caretaker_Master')
    get_data.delete_sequence_value('User_Master')
    if cdel is None:
        return RedirectResponse(url='/admin/acaretaker')
    
#Admin Caretaker Upload
@app.route("/admin/car_upload", methods=['GET', 'POST'])
async def gurd_upload(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("AdminDashboard/care_upload.html", {"request": request,"user": use})

@app.post("/careupload")
async def csupload(request: Request, csvfile: UploadFile = File()):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    if csvfile is None or current_user["user_type"] != 'admin':
        return RedirectResponse('/admin/charmanupload')
    if not csvfile.filename.endswith('.csv'):
        return templates.TemplateResponse(
                "AdminDashboard/member_upload.html",
                {"request": request, "pop_up_message": "Please upload .CSV file.","user": use}
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
        date_str = row[4]
        date = datetime.strptime(date_str, '%d-%m-%Y').date()
        date=date.strftime('%Y-%m-%d')
        dob=datetime.strptime(date, "%Y-%m-%d").date()
        quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==row[15])
        citid= await ssdb.database.fetch_one(quer)
    
        user = ssdb.user_master.insert().values(
        f_name=row[1],
        m_name=row[2],
        l_name=row[3],
        dob=dob,
        gender=row[5],
        address_line1=row[11],
        address_line2=row[12],
        landmark=row[13],
        road=row[14],
        city_id=citid[0],
        email=row[6],
        alternate_email=row[7],
        mobile_no=row[9],
        alternate_mobile_no=row[10],
        user_type='caretaker',
        created_by=createdby,
        updated_by=createdby
        )
        result =await ssdb.database.fetch_one(user)
        query=ssdb.user_master.select().where(ssdb.user_master.c.mobile_no==row[9])
        userid=await ssdb.database.fetch_one(query)
        caretkae=ssdb.caretaker_master.insert().values(
        user_id=userid[0],
        service_type=row[8],
        created_by=createdby,
        updated_by=createdby
        )
        result =await ssdb.database.fetch_one(caretkae)
      except ValueError as e:
            print(f"Error converting date for row {e}: {e}")
    return RedirectResponse('/admin/acaretaker')


#Admin Guest
@app.route("/admin/aguest", methods=['GET', 'POST'])
async def aguest(request: Request):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   email = current_user["email"]
   use=await get_data.select_tableuname(ssdb.user_master,email)
   query=select(
       ssdb.guest_master,
       ssdb.unit_master
   ).select_from(ssdb.guest_master).join(
       ssdb.unit_master,
       ssdb.guest_master.c.unit_id==ssdb.unit_master.c.unit_id
   )
   guest=await ssdb.database.fetch_all(query)
   return templates.TemplateResponse("AdminDashboard/guest.html", {"request": request, "user": use, "guest": guest})

#Admin Guest insert
@app.route("/admin/aguestinsert", methods=['GET', 'POST'])
async def aguest_insert(request: Request):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   query=ssdb.unit_master.select()
   unit= await ssdb.database.fetch_all(query)
   return templates.TemplateResponse("AdminDashboard/guest_entry.html", {"request": request, "unit": unit})

@app.post("/aguestinsert")
async def aguest_insert(request: Request, gname: str = Form(...), unitname: str = Form(...), age: str = Form(...), genders: str = Form(...), emaill: Optional[str] = Form(None), mobile: str = Form(...), guestnum: str = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    que=ssdb.unit_master.select().where(ssdb.unit_master.c.unit_name==unitname)
    unitid=await ssdb.database.fetch_one(que)
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    query=ssdb.guest_master.insert().values(
        guest_name=gname,
        unit_id=unitid[0],
        guest_age=age,
        guest_gender=genders,
        guest_number=mobile,
        guest_email=emaill,
        number_of_guest=guestnum,
        created_by=createdby,
        updated_by=createdby
    )
    guest=await ssdb.database.fetch_one(query)
    return RedirectResponse("/admin/aguest")

#Admin Guest edit
@app.get("/admin/aguestedit/{guestid}")
async def aguest_insert(request: Request, guestid : int):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'admin':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   query=ssdb.unit_master.select()
   unit= await ssdb.database.fetch_all(query)
   query=select(
       ssdb.guest_master,
       ssdb.unit_master
   ).where(ssdb.guest_master.c.guest_id==guestid).select_from(ssdb.guest_master).join(
       ssdb.unit_master,
       ssdb.guest_master.c.unit_id==ssdb.unit_master.c.unit_id
   )
   guest=await ssdb.database.fetch_one(query)
   return templates.TemplateResponse("AdminDashboard/guest_edit.html", {"request": request, "unit": unit, "g": guest})

@app.post("/aguestedit/{guestid}")
async def aguest_insert(request: Request, guestid : int, gname: str = Form(...), unitname: str = Form(...), age: str = Form(...), genders: str = Form(...), emaill: Optional[str] = Form(None), mobile: str = Form(...), guestnum: str = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    que=ssdb.unit_master.select().where(ssdb.unit_master.c.unit_name==unitname)
    unitid=await ssdb.database.fetch_one(que)
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    query=ssdb.guest_master.update().values(
        guest_name=gname,
        unit_id=unitid[0],
        guest_age=age,
        guest_gender=genders,
        guest_number=mobile,
        guest_email=emaill,
        number_of_guest=guestnum,
        created_by=createdby,
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.guest_master.c.guest_id==guestid)
    guest=await ssdb.database.fetch_one(query)
    return RedirectResponse("/admin/aguest")

#Admin Guest Delete
@app.get("/aguestdel/{guestid}")
async def gurddel(request: Request, guestid : int):
    query=ssdb.guest_master.delete().where(ssdb.guest_master.c.guest_id==guestid)
    gdel=await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Guest_Master')
    if gdel is None:
        return RedirectResponse(url='/admin/aguest')
    

#AGENCY
@app.route("/agency", methods=['GET', 'POST'])
async def admin(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user.get("user_type") != "agency":
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    query=ssdb.security_agency_master.select().where(ssdb.security_agency_master.c.email==email)
    use= await ssdb.database.fetch_one(query)
    gcount=await get_data.getcount(ssdb.security_master)
    acount=await get_data.getcount(ssdb.security_shift_master)
    return templates.TemplateResponse("AgencyDashboard/index.html", {"request": request, "user": use, "gcount": gcount, "acount": acount})   

#Agency Security Gurd
@app.route("/agency/asecurityguard", methods=['GET', 'POST'])
async def asecurityguard(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user.get("user_type") != "agency":
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email=email = current_user["email"]
    query=ssdb.security_agency_master.select().where(ssdb.security_agency_master.c.email==email)
    use= await ssdb.database.fetch_one(query)
    query = select(ssdb.security_master,
                   ssdb.security_agency_master,
                   ssdb.user_master
                   ).select_from(
        ssdb.security_master.join(
        ssdb.user_master,
        ssdb.security_master.c.user_id == ssdb.user_master.c.user_id
    ).join(
        ssdb.security_agency_master,
        ssdb.security_master.c.security_agency_id == ssdb.security_agency_master.c.security_agency_id
    )
    ).where(ssdb.security_agency_master.c.security_agency_name==use[1])
    gurds=await ssdb.database.fetch_all(query)

    return templates.TemplateResponse("AgencyDashboard/security_guard.html", {"request": request, "user": use, "gurd": gurds})


#Agency Security Gurd Insert
@app.route("/agency/guardinsert", methods=['GET', 'POST'])
async def asecurityguard(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    query=ssdb.security_agency_master.select()
    agency_name= await ssdb.database.fetch_all(query)
    query=ssdb.city_master.select()
    city=await ssdb.database.fetch_all(query)

    return templates.TemplateResponse("AgencyDashboard/security_guard_insert.html", {"request": request, "agency": agency_name, "city": city})
altmobile: Optional[str] = Form(None)

@app.post("/agencyguardsinsert")
async def aagencygurdinsert(request: Request, firstname : str = Form(...), joindt: date = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: str = Form(...), altemail: Optional[str] = Form(None), pswd: str = Form(...), address_1: str = Form(...), address_2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), altmobile: Optional[str] = Form(None)):

    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableuname(ssdb.security_agency_master,email)
    cit=ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    cityid=await ssdb.database.fetch_one(cit)
    hashed_pass=auth.encrypt_password(pswd)
    use=await get_data.select_tableuname(ssdb.security_agency_master,email)

    user = ssdb.user_master.insert().values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
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
        created_by=createdby[0][0],
        updated_by=createdby[0][0]
    )
    result =await ssdb.database.fetch_one(user)
    userid=await get_data.select_tableemail(ssdb.user_master,emaill)
    seecu = ssdb.security_master.insert().values(
        user_id=userid,
        security_agency_id=use[0][0],
        join_date=joindt,
        created_by=createdby[0][0],
        updated_by=createdby[0][0]
    )
    sresult =await ssdb.database.fetch_one(seecu)
    
    return RedirectResponse('/agency/asecurityguard')

#Agency Security Gurd Edit
@app.get("/agency/guardedit/{gurd_id}")
async def adminsocedit(request: Request, gurd_id: int):
 
    current_user = auth.verify_session(request)
    if current_user is None or current_user.get("user_type") != "agency":
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    query=ssdb.security_agency_master.select()
    agency= await ssdb.database.fetch_all(query)
    query=ssdb.city_master.select()
    city=await ssdb.database.fetch_all(query)
    query=ssdb.security_master.select().where(ssdb.security_master.c.security_id==gurd_id)
    gurd=await ssdb.database.fetch_one(query)
    query=ssdb.user_master.select().where(ssdb.user_master.c.user_id==gurd[1])
    user=await ssdb.database.fetch_one(query)
    query=ssdb.city_master.select().where(ssdb.city_master.c.city_id==user[14])
    cityy=await ssdb.database.fetch_one(query)

    return templates.TemplateResponse("AgencyDashboard/security_guard_edit.html", {"request": request, "city": city, "cityy": cityy, "user": user, "agency": agency, "gurd": gurd})

@app.post("/agencyguardsedit/{gurd_id}")
async def admingurdedit(request: Request, gurd_id: int, firstname : str = Form(...), joindt: date = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: str = Form(...), altemail: Optional[str] = Form(None), address_1: str = Form(...), address_2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), altmobile: Optional[str] = Form(None)):
    current_user = auth.verify_session(request)
    if current_user is None or current_user.get("user_type") != "agency":
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    createdby=await get_data.select_tableuname(ssdb.security_agency_master,email)
    cit=ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    cityid=await ssdb.database.fetch_one(cit)
    use=await get_data.select_tableuname(ssdb.security_agency_master,email)
    userid=await get_data.select_tableemail(ssdb.user_master,emaill)
    
    user = ssdb.user_master.update().where(ssdb.user_master.c.user_id==userid).values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
        address_line1=address_1,
        address_line2=address_2,
        landmark=landmarks,
        road=Road,
        city_id=cityid[0],
        email=emaill,
        alternate_email=altemail,
        mobile_no=mobile,
        alternate_mobile_no=altmobile,
        updated_by=createdby[0][0],
        updated_date=todaydate()
    )
    result =await ssdb.database.fetch_one(user)
    seecu = ssdb.security_master.update().where(ssdb.security_master.c.security_id==gurd_id).values(
        user_id=userid,
        security_agency_id=use[0][0],
        join_date=joindt,
        updated_by=createdby[0][0],
        updated_date=todaydate()
    )
    sresult =await ssdb.database.fetch_one(seecu)
    
    return RedirectResponse('/agency/asecurityguard')

#Agency Security Gurd Delte
@app.get("/agenguardsdelte/{gurd_id}")
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
        return RedirectResponse(url='/agency/asecurityguard')

#Agency Security Gurd Upload
@app.route("/agency/gurd_upload", methods=['GET', 'POST'])
async def gurd_upload(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user.get("user_type") != "agency":
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.security_agency_master,email)
    return templates.TemplateResponse("AgencyDashboard/security_guard_upload.html", {"request": request,"user": use})

@app.post("/agngurdupload")
async def gurdupload(request: Request, csvfile: UploadFile = File(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.security_agency_master,email)
    if current_user is None or current_user.get("user_type") != "agency":
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    if not csvfile.filename.endswith('.csv'):
        return templates.TemplateResponse(
                "AgencyDashboard/security_guard_upload.html",
                {"request": request, "pop_up_message": "Please upload .CSV file.", "user" : use}
            )
    # Read and parse the CSV file
    contents = await csvfile.read()
    csv_data = io.StringIO(contents.decode('utf-8'))
    csv_reader = csv.reader(csv_data)
    current_user = auth.verify_session(request)
    createdby=await get_data.select_tableuname(ssdb.security_agency_master,email)
    next(csv_reader, None) #removing header
    
    for row in csv_reader:
      try:
        date_str = row[4]
        date = datetime.strptime(date_str, '%d-%m-%Y').date()
        date=date.strftime('%Y-%m-%d')
        ddob=datetime.strptime(date, "%Y-%m-%d").date()
        date_str = row[16]
        date = datetime.strptime(date_str, '%d-%m-%Y').date()
        date=date.strftime('%Y-%m-%d')
        jdate=datetime.strptime(date, "%Y-%m-%d").date()
        hashed_pass=auth.encrypt_password(row[8])
        cit=ssdb.city_master.select().where(ssdb.city_master.c.city_name==row[15])
        cityid=await ssdb.database.fetch_one(cit)
        user = ssdb.user_master.insert().values(
        f_name=row[1],
        m_name=row[2],
        l_name=row[3],
        dob=ddob,
        gender=row[5],
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
        created_by=createdby[0][0],
        updated_by=createdby[0][0]
        )
        result =await ssdb.database.fetch_one(user)
        userid=await get_data.select_tableemail(ssdb.user_master,row[6])
        seecu = ssdb.security_master.insert().values(
        user_id=userid,
        security_agency_id=createdby[0][0],
        join_date=jdate,
        created_by=createdby[0][0],
        updated_by=createdby[0][0]
        )
        sresult =await ssdb.database.fetch_one(seecu)
    
        return RedirectResponse('/agency/asecurityguard')

    
      except ValueError as e:
            print(f"Error converting date for row {row}: {e}")

#Agency Security Allotment
@app.route("/agency/guardallotment", methods=['GET', 'POST'])
async def asecurityguard(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user.get("user_type") != "agency":
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email=email = current_user["email"]
    query=ssdb.security_agency_master.select().where(ssdb.security_agency_master.c.email==email)
    use= await ssdb.database.fetch_one(query)
    query = select(ssdb.security_master,
                   ssdb.security_shift_master,
                   ssdb.society_master,
                   ssdb.security_agency_master,
                   ssdb.user_master
                   ).select_from(
        ssdb.security_master.join(
        ssdb.user_master,
        ssdb.security_master.c.user_id == ssdb.user_master.c.user_id
    ).join(
        ssdb.security_agency_master,
        ssdb.security_master.c.security_agency_id == ssdb.security_agency_master.c.security_agency_id
    ).join(
        ssdb.security_shift_master,
        ssdb.security_master.c.security_id == ssdb.security_shift_master.c.security_id
    ).join(
        ssdb.society_master,
        ssdb.security_shift_master.c.society_id == ssdb.society_master.c.society_id
    )
    ).where(ssdb.security_agency_master.c.security_agency_name==use[1])
    gurds=await ssdb.database.fetch_all(query)

    return templates.TemplateResponse("AgencyDashboard/securityallotment.html", {"request": request, "user": use, "gurd": gurds})


#Agency Security Allot Insert
@app.route("/agency/allotminsert", methods=['GET', 'POST'])
async def asecurityguard(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    query=ssdb.user_master.select().where(ssdb.user_master.c.user_type=='security')
    security_name= await ssdb.database.fetch_all(query)
    query=ssdb.society_master.select()
    soci=await ssdb.database.fetch_all(query)

    return templates.TemplateResponse("AgencyDashboard/securityallotment_insert.html", {"request": request, "security": security_name, "soci": soci})
altmobile: Optional[str] = Form(None)

@app.post("/agencyallotinsert")
async def aagencygurdinsert(request: Request, secname : str = Form(...), shifttime: str = Form(...), shiftstrt: date = Form(...), shiftsend: date = Form(...), sociname : str = Form(...)):

    current_user = auth.verify_session(request)
    email = current_user["email"]
    query=ssdb.security_master.select().where(ssdb.security_master.c.user_id==secname)
    secid= await ssdb.database.fetch_one(query)
    createdby=await get_data.select_tableuname(ssdb.security_agency_master,email)

    user = ssdb.security_shift_master.insert().values(
        security_id=secid[0],
        society_id=sociname,
        shift_start_date=shiftstrt,
        shift_end_date=shiftsend,
        shift_time=shifttime,
        created_by=createdby[0][0],
        updated_by=createdby[0][0]
    )
    result =await ssdb.database.fetch_one(user)
    
    return RedirectResponse('/agency/guardallotment')

#Agency Security Gurd Edit
@app.get("/agency/allotedit/{gurd_id}")
async def adminsocedit(request: Request, gurd_id: int):
    current_user = auth.verify_session(request)
    if current_user is None or current_user.get("user_type") != "agency":
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email=email = current_user["email"]
    query=ssdb.security_agency_master.select().where(ssdb.security_agency_master.c.email==email)
    use= await ssdb.database.fetch_one(query)
    query = select(ssdb.security_master,
                   ssdb.security_shift_master,
                   ssdb.society_master,
                   ssdb.security_agency_master,
                   ssdb.user_master
                   ).select_from(
        ssdb.security_master.join(
        ssdb.user_master,
        ssdb.security_master.c.user_id == ssdb.user_master.c.user_id
    ).join(
        ssdb.security_agency_master,
        ssdb.security_master.c.security_agency_id == ssdb.security_agency_master.c.security_agency_id
    ).join(
        ssdb.security_shift_master,
        ssdb.security_master.c.security_id == ssdb.security_shift_master.c.security_id
    ).join(
        ssdb.society_master,
        ssdb.security_shift_master.c.society_id == ssdb.society_master.c.society_id
    )
    ).where(ssdb.security_shift_master.c.security_shift_id==gurd_id)
    gurds=await ssdb.database.fetch_one(query)
    query=ssdb.user_master.select().where(ssdb.user_master.c.user_type=='security')
    security_name= await ssdb.database.fetch_all(query)
    query=ssdb.society_master.select()
    soci=await ssdb.database.fetch_all(query)
    return templates.TemplateResponse("AgencyDashboard/securityallotment_edit.html", {"request": request, "user": use, "gurd": gurds, "security": security_name, "soci": soci})

@app.post("/agencyallotins/{gurd_id}")
async def aagencygurdinsert(request: Request, gurd_id: int, secname : str = Form(...), shifttime: str = Form(...), shiftstrt: date = Form(...), shiftsend: date = Form(...), sociname : str = Form(...)):

    current_user = auth.verify_session(request)
    email = current_user["email"]
    query=ssdb.security_master.select().where(ssdb.security_master.c.user_id==secname)
    secid= await ssdb.database.fetch_one(query)
    createdby=await get_data.select_tableuname(ssdb.security_agency_master,email)

    user = ssdb.security_shift_master.update().where(ssdb.security_shift_master.c.security_shift_id==gurd_id).values(
        security_id=secid[0],
        society_id=sociname,
        shift_start_date=shiftstrt,
        shift_end_date=shiftsend,
        shift_time=shifttime,
        created_by=createdby[0][0],
        updated_by=createdby[0][0]
    )
    result =await ssdb.database.fetch_one(user)
    
    return RedirectResponse('/agency/guardallotment')

#Agency Security Gurd Delte
@app.get("/agecyallotdel/{gurd_id}")
async def gurddel(request: Request, gurd_id: int):
    query=ssdb.security_shift_master.delete().where(ssdb.security_shift_master.c.security_shift_id==gurd_id)
    udel=await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Security_Shift_Master')
    if udel is None:
        return RedirectResponse(url='/agency/guardallotment')

#Agency user-profile
@app.route("/agency/users-profile", methods=['GET', 'POST'])
async def auser(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    query=ssdb.security_agency_master.select().where(ssdb.security_agency_master.c.email==email)
    use= await ssdb.database.fetch_one(query)
    return templates.TemplateResponse("AgencyDashboard/users-profile.html", {"request": request, "user": use})

#Agency profile edit
@app.post("/agenprofile/{user_id}")
async def pedit(request: Request, user_id: int, fName:str = Form(...), adress1: Optional[str] = Form(), adress2: Optional[str] = Form(), phone: Optional[str] = Form(), email: Optional[str] = Form()):
    current_user = auth.verify_session(request)
    query=ssdb.security_agency_master.update().where(ssdb.security_agency_master.c.security_agency_id==user_id).values(
        security_agency_name=fName,
        agency_address_line1=adress1,
        agency_address_line2=adress2,
        contact_no=phone,
        email=email
    )
    user=await ssdb.database.fetch_one(query)
    if user is None:
        return RedirectResponse("/agency")
    
#Agency Change pass
@app.route("/agency/chgpass", methods=['GET', 'POST'])
async def auser(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'agency':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.security_agency_master,email)
    return templates.TemplateResponse("AgencyDashboard/chgpass.html", {"request": request, "user": use})

#Security pass edit
@app.post("/agechgpass/{user_id}")
async def pedit(request: Request, user_id: int, password:str = Form(...), newpswd: str = Form(...)):
    current_user = auth.verify_session(request)
    query=ssdb.security_agency_master.select().where(ssdb.security_agency_master.c.security_agency_id==user_id)
    result=await ssdb.database.fetch_one(query)
    hashed_password = result["password"]
    if bcrypt_context.verify(password, hashed_password):
        passs=auth.encrypt_password(newpswd)
        query=ssdb.security_agency_master.update().where(ssdb.security_agency_master.c.security_agency_id==user_id).values(
                password=passs
        )
        user=await ssdb.database.fetch_one(query)
        return RedirectResponse(f"/agency?message=Password+changed+successfully", status_code=303)
    return RedirectResponse(f"/agency/chgpass?message=Invalid+password", status_code=303)


#Chairman
@app.route("/chairman", methods=["GET", "POST"])
async def chairman(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'chairman':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    mcount=await get_data.getcount(ssdb.member_master)
    carcount=await get_data.getcount(ssdb.caretaker_master)
    ucount=await get_data.getcount(ssdb.unit_master)
    return templates.TemplateResponse("ChairamnDashboard/index.html", {"request": request, "user": use, "mcount": mcount, "ucount": ucount, "carcount": carcount})

#Chairman Owner
@app.route("/chairman/owner", methods=["GET", "POST"])
async def cmemberowner(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'chairman':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    query = select(ssdb.member_master,
                   ssdb.unit_master,
                   ssdb.society_master,
                   ssdb.user_master
                   ).select_from(
        ssdb.member_master.join(
        ssdb.unit_master,
        ssdb.unit_master.c.unit_id == ssdb.member_master.c.unit_id
    ).join(
        ssdb.society_master,
        ssdb.society_master.c.society_id == ssdb.unit_master.c.society_id
    ).join(
        ssdb.user_master,
        ssdb.user_master.c.user_id==ssdb.member_master.c.member_userid
    )
                   )
    member= await ssdb.database.fetch_all(query)
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("ChairamnDashboard/owner.html", {"request": request, "member": member, "user": use})

#Chairman Member Insert
@app.route("/chairman/member_insert", methods=['GET', 'POST'])
async def cmember(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'chairman':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    quey = ssdb.unit_master.select()
    un= await ssdb.database.fetch_all(quey)
    query= ssdb.city_master.select()
    cit= await ssdb.database.fetch_all(query)
    return templates.TemplateResponse("ChairamnDashboard/owner_insert.html", {"request": request, "unit": un, "city": cit})

@app.post("/chmemberinsert")
async def chairmanmebinsert(request: Request, firstname : str = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: str = Form(...), altemail: Optional[str] = Form(None), pswd: str = Form(...), address1: str = Form(...), address2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), altmobile: Optional[str] = Form(None), unitname: str = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    citid= await ssdb.database.fetch_one(quer)
    hashed_pass=auth.encrypt_password(pswd)
    query=ssdb.unit_master.select().where(ssdb.unit_master.c.unit_name==unitname)
    unitn= await ssdb.database.fetch_one(query)
    user = ssdb.user_master.insert().values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
        address_line1=address1,
        address_line2=address2,
        landmark=landmarks,
        road=Road,
        city_id=citid[0],
        email=emaill,
        alternate_email=altemail,
        password=hashed_pass,
        mobile_no=mobile,
        alternate_mobile_no=altmobile,
        user_type='member',
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(user)
    userid=await get_data.select_tableemail(ssdb.user_master,emaill)
    mamber=ssdb.member_master.insert().values(
        member_userid=userid,
        unit_id=unitn[1],
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(mamber)
    return RedirectResponse('/chairman/owner')

#Chairman Member Edit
@app.get("/chairman/chmember_edit/{member_id}")
async def amember(request: Request, member_id : int):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'chairman':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    quey = ssdb.unit_master.select()
    un= await ssdb.database.fetch_all(quey)
    query= ssdb.city_master.select()
    cit= await ssdb.database.fetch_all(query)
    query=ssdb.member_master.select().where(ssdb.member_master.c.member_id==member_id)
    mem= await ssdb.database.fetch_one(query)
    query=ssdb.unit_master.select().where(ssdb.unit_master.c.unit_id==mem[4])
    uin=await ssdb.database.fetch_one(query)
    query=ssdb.user_master.select().where(ssdb.user_master.c.user_id==mem[1])
    use= await ssdb.database.fetch_one(query)
    return templates.TemplateResponse("ChairamnDashboard/owner_edit.html", {"request": request, "unit": un,"m" : mem, "cityy": cit, "user": use})

@app.post("/chmemberedit/{meber_id}")
async def chairmanmembinsert(request: Request, meber_id : int, firstname : str = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: str = Form(...), altemail: Optional[str] = Form(None), address1: str = Form(...), address2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), altmobile: Optional[str] = Form(None), unitname: str = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    userid=await get_data.select_tableemail(ssdb.user_master,emaill)
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    citid= await ssdb.database.fetch_one(quer)
    query=ssdb.unit_master.select().where(ssdb.unit_master.c.unit_name==unitname)
    unitn= await ssdb.database.fetch_one(query)
    user = ssdb.user_master.update().values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
        address_line1=address1,
        address_line2=address2,
        landmark=landmarks,
        road=Road,
        city_id=citid[0],
        email=emaill,
        alternate_email=altemail,
        mobile_no=mobile,
        alternate_mobile_no=altmobile,
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.user_master.c.user_id==userid)
    result =await ssdb.database.fetch_one(user)
    userid=await get_data.select_tableemail(ssdb.user_master,emaill)
    mamber=ssdb.member_master.update().values(
        member_userid=userid,
        unit_id=unitn[1],
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.member_master.c.member_id==meber_id)
    result =await ssdb.database.fetch_one(mamber)
    return RedirectResponse('/chairman/owner')

#Chairman Member Delete
@app.get("/chmemberdel/{member_id}")
async def charidel(request: Request, member_id: int):
    query=ssdb.member_master.select().where(ssdb.member_master.c.member_id==member_id)
    uid=await ssdb.database.fetch_one(query)
    query=ssdb.user_master.delete().where(ssdb.user_master.c.user_id==uid[1])
    udel=await ssdb.database.fetch_one(query)
    query=ssdb.member_master.delete().where(ssdb.member_master.c.member_id==member_id)
    cdel=await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Member/Owner_Master')
    get_data.delete_sequence_value('User_Master')
    if cdel is None:
        return RedirectResponse(url='/chairman/owner')

#Chairman Member Upload  
@app.route("/chairman/memberupload", methods=['GET', 'POST'])
async def amember(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'chairman':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("ChairamnDashboard/owner_upload.html", {"request": request, "user": use})

@app.post("/chmemberupload")
async def csupload(request: Request, csvfile: UploadFile = File()):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    if csvfile is None or current_user["user_type"] != 'chairman':
        return RedirectResponse('/chairman/charmanupload')
    if not csvfile.filename.endswith('.csv'):
        return templates.TemplateResponse(
                "ChairamnDashboard/owner_upload.html",
                {"request": request, "pop_up_message": "Please upload .CSV file.","user": use}
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
        date_str = row[4]
        date = datetime.strptime(date_str, '%d-%m-%Y').date()
        date=date.strftime('%Y-%m-%d')
        dob=datetime.strptime(date, "%Y-%m-%d").date()
        quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==row[16])
        citid= await ssdb.database.fetch_one(quer)
        hashed_pass=auth.encrypt_password(row[8])
        query=ssdb.unit_master.select().where(ssdb.unit_master.c.unit_name==row[11])
        unitn= await ssdb.database.fetch_one(query)
    
        user = ssdb.user_master.insert().values(
        f_name=row[1],
        m_name=row[2],
        l_name=row[3],
        dob=dob,
        gender=row[5],
        address_line1=row[12],
        address_line2=row[13],
        landmark=row[14],
        road=row[15],
        city_id=citid[0],
        email=row[6],
        alternate_email=row[7],
        password=hashed_pass,
        mobile_no=row[9],
        alternate_mobile_no=row[10],
        user_type='member',
        created_by=createdby,
        updated_by=createdby
        )
        result =await ssdb.database.fetch_one(user)
        userid=await get_data.select_tableemail(ssdb.user_master,row[6])
        mamber=ssdb.member_master.insert().values(
        member_userid=userid,
        unit_id=unitn[1],
        created_by=createdby,
        updated_by=createdby
        )
        result =await ssdb.database.fetch_one(mamber)
      except ValueError as e:
            print(f"Error converting date for row {e}: {e}")
    return RedirectResponse('/chairman/owner')

#Chairman Caretaker   
@app.route("/chairman/acaretaker", methods=['GET', 'POST'])
async def acaretaker(request: Request):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'chairman':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   email = current_user["email"]
   use=await get_data.select_tableuname(ssdb.user_master,email)
   query=select(ssdb.caretaker_master,ssdb.user_master).select_from(
       ssdb.caretaker_master.join(
           ssdb.user_master,
           ssdb.user_master.c.user_id==ssdb.caretaker_master.c.user_id
       )
   )
   care=await ssdb.database.fetch_all(query)
   return templates.TemplateResponse("ChairamnDashboard/caretaker.html", {"request": request, "user": use, "caretaker": care})

 #chairman Caretaker Insert  
@app.route("/chairman/acaretakerinsert", methods=['GET', 'POST'])
async def acaretaker(request: Request):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'chairman':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   email = current_user["email"]
   query=ssdb.city_master.select()
   cit=await ssdb.database.fetch_all(query)
   return templates.TemplateResponse("ChairamnDashboard/caretaker_insert.html", {"request": request, "cit": cit}) 

@app.post("/chcaretakeredit")
async def chairmanmebinsert(request: Request, firstname : str = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: Optional[str] = Form(None), altemail: Optional[str] = Form(None), servicetyp: str = Form(...), address1: str = Form(...), address2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), altmobile: Optional[str] = Form(None)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    citid= await ssdb.database.fetch_one(quer)
    user = ssdb.user_master.insert().values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
        address_line1=address1,
        address_line2=address2,
        landmark=landmarks,
        road=Road,
        city_id=citid[0],
        email=emaill,
        alternate_email=altemail,
        mobile_no=mobile,
        alternate_mobile_no=altmobile,
        user_type='caretaker',
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(user)
    query=ssdb.user_master.select().where(ssdb.user_master.c.mobile_no==mobile)
    userid=await ssdb.database.fetch_one(query)
    caretkae=ssdb.caretaker_master.insert().values(
        user_id=userid[0],
        service_type=servicetyp,
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(caretkae)
    return RedirectResponse('/chairman/acaretaker')

#Chairman Caretaker edit  
@app.get("/chairman/caretakeredit/{c_id}")
async def acaretaker(request: Request, c_id: int):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'chairman':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   email = current_user["email"]
   query=ssdb.city_master.select()
   cit=await ssdb.database.fetch_all(query)
   query=select(ssdb.caretaker_master,ssdb.user_master,ssdb.city_master).select_from(
       ssdb.caretaker_master.join(
           ssdb.user_master,
           ssdb.user_master.c.user_id==ssdb.caretaker_master.c.user_id
       ).join(
           ssdb.city_master,
           ssdb.city_master.c.city_id==ssdb.user_master.c.city_id
       )
   ).where(ssdb.caretaker_master.c.c_id==c_id)
   care=await ssdb.database.fetch_one(query)
   return templates.TemplateResponse("ChairamnDashboard/caretaker_edit.html", {"request": request, "cit": cit, "car": care}) 

@app.post("/caretakeredit/{c_id}")
async def chairmancaredit(request: Request, c_id: int, firstname : str = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: Optional[str] = Form(None), altemail: Optional[str] = Form(None), servicetyp: str = Form(...), address1: str = Form(...), address2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), altmobile: Optional[str] = Form(None)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    citid= await ssdb.database.fetch_one(quer)
    query=ssdb.caretaker_master.select().where(ssdb.caretaker_master.c.c_id==c_id)
    uid=await ssdb.database.fetch_one(query)
    user = ssdb.user_master.update().values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
        address_line1=address1,
        address_line2=address2,
        landmark=landmarks,
        road=Road,
        city_id=citid[0],
        email=emaill,
        alternate_email=altemail,
        mobile_no=mobile,
        alternate_mobile_no=altmobile,
        user_type='caretaker',
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.user_master.c.user_id==uid[1])
    result =await ssdb.database.fetch_one(user)
    caretkae=ssdb.caretaker_master.update().values(
        user_id=uid[1],
        service_type=servicetyp,
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.caretaker_master.c.c_id==c_id)
    result =await ssdb.database.fetch_one(caretkae)
    return RedirectResponse('/chairman/acaretaker')

#Chairman Caretaker Delete
@app.get("/caretakerdel/{c_id}")
async def charidel(request: Request, c_id: int):
    query=ssdb.caretaker_master.select().where(ssdb.caretaker_master.c.c_id==c_id)
    uid=await ssdb.database.fetch_one(query)
    query=ssdb.user_master.delete().where(ssdb.user_master.c.user_id==uid[1])
    udel=await ssdb.database.fetch_one(query)
    query=ssdb.caretaker_master.delete().where(ssdb.caretaker_master.c.c_id==c_id)
    cdel=await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Caretaker_Master')
    get_data.delete_sequence_value('User_Master')
    if cdel is None:
        return RedirectResponse(url='/chairman/acaretaker')
    
#Chairman Caretaker Upload
@app.route("/chairman/car_upload", methods=['GET', 'POST'])
async def gurd_upload(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'chairman':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("ChairamnDashboard/care_upload.html", {"request": request,"user": use})

@app.post("/chcareupload")
async def csupload(request: Request, csvfile: UploadFile = File()):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    if csvfile is None or current_user["user_type"] != 'chairman':
        return RedirectResponse('/chairman/charmanupload')
    if not csvfile.filename.endswith('.csv'):
        return templates.TemplateResponse(
                "ChairamnDashboard/care_upload.html",
                {"request": request, "pop_up_message": "Please upload .CSV file.","user": use}
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
        date_str = row[4]
        date = datetime.strptime(date_str, '%d-%m-%Y').date()
        date=date.strftime('%Y-%m-%d')
        dob=datetime.strptime(date, "%Y-%m-%d").date()
        quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==row[15])
        citid= await ssdb.database.fetch_one(quer)
    
        user = ssdb.user_master.insert().values(
        f_name=row[1],
        m_name=row[2],
        l_name=row[3],
        dob=dob,
        gender=row[5],
        address_line1=row[11],
        address_line2=row[12],
        landmark=row[13],
        road=row[14],
        city_id=citid[0],
        email=row[6],
        alternate_email=row[7],
        mobile_no=row[9],
        alternate_mobile_no=row[10],
        user_type='caretaker',
        created_by=createdby,
        updated_by=createdby
        )
        result =await ssdb.database.fetch_one(user)
        query=ssdb.user_master.select().where(ssdb.user_master.c.mobile_no==row[9])
        userid=await ssdb.database.fetch_one(query)
        caretkae=ssdb.caretaker_master.insert().values(
        user_id=userid[0],
        service_type=row[8],
        created_by=createdby,
        updated_by=createdby
        )
        result =await ssdb.database.fetch_one(caretkae)
      except ValueError as e:
            print(f"Error converting date for row {e}: {e}")
    return RedirectResponse('/chairman/acaretaker')

#Chairman Member Insert
@app.route("/chairman/member_insert", methods=['GET', 'POST'])
async def cmember(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'chairman':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    quey = ssdb.unit_master.select()
    un= await ssdb.database.fetch_all(quey)
    query= ssdb.city_master.select()
    cit= await ssdb.database.fetch_all(query)
    return templates.TemplateResponse("ChairamnDashboard/owner_insert.html", {"request": request, "unit": un, "city": cit})

@app.post("/chmemberinsert")
async def chairmanmebinsert(request: Request, firstname : str = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: str = Form(...), altemail: Optional[str] = Form(None), pswd: str = Form(...), address1: str = Form(...), address2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), altmobile: Optional[str] = Form(None), unitname: str = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    citid= await ssdb.database.fetch_one(quer)
    hashed_pass=auth.encrypt_password(pswd)
    query=ssdb.unit_master.select().where(ssdb.unit_master.c.unit_name==unitname)
    unitn= await ssdb.database.fetch_one(query)
    user = ssdb.user_master.insert().values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
        address_line1=address1,
        address_line2=address2,
        landmark=landmarks,
        road=Road,
        city_id=citid[0],
        email=emaill,
        alternate_email=altemail,
        password=hashed_pass,
        mobile_no=mobile,
        alternate_mobile_no=altmobile,
        user_type='member',
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(user)
    userid=await get_data.select_tableemail(ssdb.user_master,emaill)
    mamber=ssdb.member_master.insert().values(
        member_userid=userid,
        unit_id=unitn[1],
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(mamber)
    return RedirectResponse('/chairman/owner')

#Chairman Member Edit
@app.get("/chairman/chmember_edit/{member_id}")
async def amember(request: Request, member_id : int):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'chairman':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    quey = ssdb.unit_master.select()
    un= await ssdb.database.fetch_all(quey)
    query= ssdb.city_master.select()
    cit= await ssdb.database.fetch_all(query)
    query=ssdb.member_master.select().where(ssdb.member_master.c.member_id==member_id)
    mem= await ssdb.database.fetch_one(query)
    query=ssdb.unit_master.select().where(ssdb.unit_master.c.unit_id==mem[4])
    uin=await ssdb.database.fetch_one(query)
    query=ssdb.user_master.select().where(ssdb.user_master.c.user_id==mem[1])
    use= await ssdb.database.fetch_one(query)
    return templates.TemplateResponse("ChairamnDashboard/owner_edit.html", {"request": request, "unit": un,"m" : mem, "cityy": cit, "user": use})

@app.post("/chmemberedit/{meber_id}")
async def chairmanmembinsert(request: Request, meber_id : int, firstname : str = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: str = Form(...), altemail: Optional[str] = Form(None), address1: str = Form(...), address2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), altmobile: Optional[str] = Form(None), unitname: str = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    userid=await get_data.select_tableemail(ssdb.user_master,emaill)
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    citid= await ssdb.database.fetch_one(quer)
    query=ssdb.unit_master.select().where(ssdb.unit_master.c.unit_name==unitname)
    unitn= await ssdb.database.fetch_one(query)
    user = ssdb.user_master.update().values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
        address_line1=address1,
        address_line2=address2,
        landmark=landmarks,
        road=Road,
        city_id=citid[0],
        email=emaill,
        alternate_email=altemail,
        mobile_no=mobile,
        alternate_mobile_no=altmobile,
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.user_master.c.user_id==userid)
    result =await ssdb.database.fetch_one(user)
    userid=await get_data.select_tableemail(ssdb.user_master,emaill)
    mamber=ssdb.member_master.update().values(
        member_userid=userid,
        unit_id=unitn[1],
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.member_master.c.member_id==meber_id)
    result =await ssdb.database.fetch_one(mamber)
    return RedirectResponse('/chairman/owner')

#Chairman Member Delete
@app.get("/chmemberdel/{member_id}")
async def charidel(request: Request, member_id: int):
    query=ssdb.member_master.select().where(ssdb.member_master.c.member_id==member_id)
    uid=await ssdb.database.fetch_one(query)
    query=ssdb.user_master.delete().where(ssdb.user_master.c.user_id==uid[1])
    udel=await ssdb.database.fetch_one(query)
    query=ssdb.member_master.delete().where(ssdb.member_master.c.member_id==member_id)
    cdel=await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Member/Owner_Master')
    get_data.delete_sequence_value('User_Master')
    if cdel is None:
        return RedirectResponse(url='/chairman/owner')

#Chairman Member Upload  
@app.route("/chairman/memberupload", methods=['GET', 'POST'])
async def amember(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'chairman':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("ChairamnDashboard/owner_upload.html", {"request": request, "user": use})

@app.post("/chmemberupload")
async def csupload(request: Request, csvfile: UploadFile = File()):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    if csvfile is None or current_user["user_type"] != 'chairman':
        return RedirectResponse('/chairman/charmanupload')
    if not csvfile.filename.endswith('.csv'):
        return templates.TemplateResponse(
                "chairmanDashboard/member_upload.html",
                {"request": request, "pop_up_message": "Please upload .CSV file.","user": use}
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
        date_str = row[4]
        date = datetime.strptime(date_str, '%d-%m-%Y').date()
        date=date.strftime('%Y-%m-%d')
        dob=datetime.strptime(date, "%Y-%m-%d").date()
        quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==row[16])
        citid= await ssdb.database.fetch_one(quer)
        hashed_pass=auth.encrypt_password(row[8])
        query=ssdb.unit_master.select().where(ssdb.unit_master.c.unit_name==row[11])
        unitn= await ssdb.database.fetch_one(query)
    
        user = ssdb.user_master.insert().values(
        f_name=row[1],
        m_name=row[2],
        l_name=row[3],
        dob=dob,
        gender=row[5],
        address_line1=row[12],
        address_line2=row[13],
        landmark=row[14],
        road=row[15],
        city_id=citid[0],
        email=row[6],
        alternate_email=row[7],
        password=hashed_pass,
        mobile_no=row[9],
        alternate_mobile_no=row[10],
        user_type='member',
        created_by=createdby,
        updated_by=createdby
        )
        result =await ssdb.database.fetch_one(user)
        userid=await get_data.select_tableemail(ssdb.user_master,row[6])
        mamber=ssdb.member_master.insert().values(
        member_userid=userid,
        unit_id=unitn[1],
        created_by=createdby,
        updated_by=createdby
        )
        result =await ssdb.database.fetch_one(mamber)
      except ValueError as e:
            print(f"Error converting date for row {e}: {e}")
    return RedirectResponse('/chairman/owner')

#Chairman Units
@app.route("/chairman/units", methods=["GET", "POST"])
async def cmemberunits(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'chairman':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    query = select(ssdb.unit_master,
                   ssdb.society_master,
                   ).select_from(
        ssdb.unit_master.join(
        ssdb.society_master,
        ssdb.society_master.c.society_id == ssdb.unit_master.c.society_id
    )
      )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    unit= await ssdb.database.fetch_all(query)
    return templates.TemplateResponse("ChairamnDashboard/units.html", {"request": request, "unit": unit, "user": use})

#Chairman Units Insert
@app.route("/chairman/unit_insert", methods=['GET', 'POST'])
async def cmember(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'chairman':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    query= ssdb.society_master.select()
    soc= await ssdb.database.fetch_all(query)
    return templates.TemplateResponse("ChairamnDashboard/units_insert.html", {"request": request, "soci": soc})

@app.post("/chunitinsert")
async def chairmanmebinsert(request: Request, unitname: str = Form(...), unitype: str = Form(...), block: str = Form(...), floor: str = Form(...), soci: str = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    query=ssdb.society_master.select().where(ssdb.society_master.c.society_name==soci)
    socid= await ssdb.database.fetch_one(query)
    unit = ssdb.unit_master.insert().values(
        society_id=socid[0],
        unit_name=unitname,
        unit_type=unitype,
        unit_block=block,
        unit_floor=floor,
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(unit)
    return RedirectResponse('/chairman/units')

#Chairman Unit Delete
@app.get("/chunitdel/{unit_id}")
async def charidel(request: Request, unit_id: int):
    query=ssdb.unit_master.delete().where(ssdb.unit_master.c.unit_id==unit_id)
    udel=await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Unit_Master')
    if udel is None:
        return RedirectResponse(url='/chairman/units')
    
#Chairman Unit Upload  
@app.route("/chairman/unitupload", methods=['GET', 'POST'])
async def unitupload(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'chairman':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("ChairamnDashboard/unit_upload.html", {"request": request, "user": use})

@app.post("/chunitupload")
async def csupload(request: Request, csvfile: UploadFile = File()):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    if csvfile is None or current_user["user_type"] != 'chairman':
        return RedirectResponse('/chairman/unitupload')
    if not csvfile.filename.endswith('.csv'):
        return templates.TemplateResponse(
                "ChairamnDashboard/unit_upload.html",
                {"request": request, "pop_up_message": "Please upload .CSV file.","user": use}
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
        query=ssdb.society_master.select().where(ssdb.society_master.c.society_name==row[5])
        socid= await ssdb.database.fetch_one(query)
        unit = ssdb.unit_master.insert().values(
        society_id='1',
        unit_name=row[1],
        unit_type=row[2],
        unit_block=row[3],
        unit_floor=row[4],
        created_by=createdby,
        updated_by=createdby
        )
        result =await ssdb.database.fetch_one(unit)
        return RedirectResponse('/chairman/units')
      except ValueError as e:
            print(f"Error converting date for row {e}: {e}")
    return RedirectResponse('/chairman/units')

#chairman user-profile
@app.route("/chairman/users-profile", methods=['GET', 'POST'])
async def auser(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'chairman':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("ChairamnDashboard/users-profile.html", {"request": request, "user": use})

#chairman profile edit
@app.post("/charprofile/{user_id}")
async def pedit(request: Request, user_id: int, fName:str = Form(...), lName: Optional[str] = Form(), adress1: Optional[str] = Form(), adress2: Optional[str] = Form(), phone: Optional[str] = Form(), email: Optional[str] = Form()):
    current_user = auth.verify_session(request)
    query=ssdb.user_master.update().where(ssdb.user_master.c.user_id==user_id).values(
        f_name=fName,
        l_name=lName,
        address_line1=adress1,
        address_line2=adress2,
        mobile_no=phone,
        email=email
    )
    user=await ssdb.database.fetch_one(query)
    if user is None:
        return RedirectResponse("/chairman")

#Chairman Change pass
@app.route("/chairman/chgpass", methods=['GET', 'POST'])
async def auser(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'chairman':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("ChairamnDashboard/chgpass.html", {"request": request, "user": use})

#Chairman pass edit
@app.post("/chairchgpass/{user_id}")
async def pedit(request: Request, user_id: int, password:str = Form(...), newpswd: str = Form(...)):
    current_user = auth.verify_session(request)
    query=ssdb.user_master.select().where(ssdb.user_master.c.user_id==user_id)
    result=await ssdb.database.fetch_one(query)
    hashed_password = result["password"]
    if bcrypt_context.verify(password, hashed_password):
        passs=auth.encrypt_password(newpswd)
        query=ssdb.user_master.update().where(ssdb.user_master.c.user_id==user_id).values(
                password=passs
        )
        user=await ssdb.database.fetch_one(query)
        return RedirectResponse(f"/chairman?message=Password+changed+successfully", status_code=303)
    return RedirectResponse(f"/chairman/chgpass?message=Invalid+password", status_code=303)
  

#Member 
@app.route("/member", methods=["GET", "POST"])
async def member(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'member':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    notifications=await get_data.notyread(use[0][0])
    ncount=len(notifications)
    use=await get_data.select_tableuname(ssdb.user_master,email)
    carcount=await get_data.getcount(ssdb.caretaker_master)
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    query=ssdb.member_master.select().where(ssdb.member_master.c.member_userid==createdby)
    owner=await ssdb.database.fetch_one(query)
    query=ssdb.vehicle_master.select().where(ssdb.vehicle_master.c.unit_id==owner[3])
    vehi=await ssdb.database.fetch_all(query)
    vcount=len(vehi)
    query=ssdb.member_master.select().where(ssdb.member_master.c.member_userid==use[0][0])
    unitid=await ssdb.database.fetch_one(query)
    query=ssdb.frequently_visiting_master.select().where(ssdb.frequently_visiting_master.c.unit_id==unitid[3])
    freq=await ssdb.database.fetch_all(query)
    fcount=len(freq)
    query=ssdb.member_master.select().where(ssdb.member_master.c.member_userid==use[0][0])
    unitid=await ssdb.database.fetch_one(query)
    query=ssdb.guest_master.select().where(ssdb.guest_master.c.unit_id==unitid[3])
    guest=await ssdb.database.fetch_all(query)
    gcount=len(guest)
    return templates.TemplateResponse("MemberDashboard/index.html", {"request": request, "user": use, "notifications": notifications, "ncount": ncount, "vcount": vcount, "carcount": carcount, "fcount": fcount, "gcount": gcount})

#Member Allow Guest Entry
@app.route("/gallow", methods=['GET', 'POST'])
async def gallow(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'member':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    notifi=await get_data.nsid(use[0][0])
    query=ssdb.member_master.select().where(ssdb.member_master.c.member_userid==use[0][0])
    unitid=await ssdb.database.fetch_one(query)
    query=ssdb.notification_master.delete().where(ssdb.notification_master.c.reciver_id==use[0][0])
    noti=await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Notification_Master')
    query=ssdb.member_master.select().where(ssdb.member_master.c.member_userid==use[0][0])
    unitid=await ssdb.database.fetch_one(query)
    return RedirectResponse('/member')

#Member Allow Guest Entry
@app.get("/gdeny/{guest}")
async def gdeny(request: Request, guest: str):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'member':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    query=ssdb.notification_master.delete().where(ssdb.notification_master.c.reciver_id==use[0][0])
    noti=await ssdb.database.fetch_one(query)
    query=ssdb.member_master.select().where(ssdb.member_master.c.member_userid==use[0][0])
    unitid=await ssdb.database.fetch_one(query)
    query=ssdb.guest_master.delete().where((ssdb.guest_master.c.unit_id==unitid[3]) & (ssdb.guest_master.c.guest_name==guest))
    guest=await ssdb.database.execute(query)
    get_data.delete_sequence_value('Notification_Master')
    return RedirectResponse('/member')

#Member FamilyMembe
@app.route("/member/member", methods=['GET', 'POST'])
async def amember(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'member':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    query = select(ssdb.member_master,
                   ssdb.unit_master,
                   ssdb.society_master,
                   ssdb.user_master
                   ).where(ssdb.member_master.c.add_by==use[0][0]).select_from(
        ssdb.member_master.join(
        ssdb.unit_master,
        ssdb.unit_master.c.unit_id == ssdb.member_master.c.unit_id
    ).join(
        ssdb.society_master,
        ssdb.society_master.c.society_id == ssdb.unit_master.c.society_id
    ).join(
        ssdb.user_master,
        ssdb.user_master.c.user_id==ssdb.member_master.c.member_userid
    )
                   )
    member= await ssdb.database.fetch_all(query)
    notifications=await get_data.notyread(use[0][0])
    ncount=len(notifications)
    return templates.TemplateResponse("MemberDashboard/FamilyMember.html", {"request": request, "member": member, "user": use, "notifications": notifications, "ncount": ncount})

#Member FamilyMamber Insert
@app.route("/member/member_insert", methods=['GET', 'POST'])
async def cmember(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'member':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    quey = ssdb.unit_master.select()
    un= await ssdb.database.fetch_all(quey)
    query= ssdb.city_master.select()
    cit= await ssdb.database.fetch_all(query)
    return templates.TemplateResponse("MemberDashboard/family_insert.html", {"request": request, "unit": un, "city": cit})

@app.post("/mamemberinsert")
async def membermebinsert(request: Request, firstname : str = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: str = Form(...), altemail: Optional[str] = Form(None), mobile:str = Form(...), altmobile: Optional[str] = Form(None)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    use=await get_data.select_tableuname(ssdb.user_master,email)
    query=ssdb.member_master.select().where(ssdb.member_master.c.member_userid==createdby)
    owner=await ssdb.database.fetch_one(query)
    user = ssdb.user_master.insert().values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
        address_line1=use[0][10],
        address_line2=use[0][11],
        landmark=use[0][12],
        road=use[0][13],
        city_id=use[0][14],
        email=emaill,
        alternate_email=altemail,
        mobile_no=mobile,
        alternate_mobile_no=altmobile,
        user_type='familymember',
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(user)
    userid=await get_data.select_tableemail(ssdb.user_master,emaill)
    mamber=ssdb.member_master.insert().values(
        member_userid=userid,
        add_by=createdby,
        unit_id=owner[3],
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(mamber)
    return RedirectResponse('/member/member')

#member Member Edit
@app.get("/member/member_edit/{member_id}")
async def amember(request: Request, member_id : int):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'member':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    quey = ssdb.unit_master.select()
    un= await ssdb.database.fetch_all(quey)
    query= ssdb.city_master.select()
    cit= await ssdb.database.fetch_all(query)
    query=ssdb.member_master.select().where(ssdb.member_master.c.member_id==member_id)
    mem= await ssdb.database.fetch_one(query)
    query=ssdb.unit_master.select().where(ssdb.unit_master.c.unit_id==mem[4])
    uin=await ssdb.database.fetch_one(query)
    query=ssdb.user_master.select().where(ssdb.user_master.c.user_id==mem[1])
    use= await ssdb.database.fetch_one(query)
    return templates.TemplateResponse("MemberDashboard/family_edit.html", {"request": request, "unit": un,"m" : mem, "cityy": cit, "user": use})

@app.post("/fmemberedit/{meber_id}")
async def membermembinsert(request: Request, meber_id : int, firstname : str = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: str = Form(...), mobile:str = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    userid=await get_data.select_tableemail(ssdb.user_master,emaill)
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    user = ssdb.user_master.update().values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
        email=emaill,
        mobile_no=mobile,
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.user_master.c.user_id==userid)
    result =await ssdb.database.fetch_one(user)
    userid=await get_data.select_tableemail(ssdb.user_master,emaill)
    mamber=ssdb.member_master.update().values(
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.member_master.c.member_id==meber_id)
    result =await ssdb.database.fetch_one(mamber)
    return RedirectResponse('/member/member')

#member Member Delete
@app.get("/mmemberdel/{member_id}")
async def charidel(request: Request, member_id: int):
    query=ssdb.member_master.select().where(ssdb.member_master.c.member_id==member_id)
    uid=await ssdb.database.fetch_one(query)
    query=ssdb.user_master.delete().where(ssdb.user_master.c.user_id==uid[1])
    udel=await ssdb.database.fetch_one(query)
    query=ssdb.member_master.delete().where(ssdb.member_master.c.member_id==member_id)
    cdel=await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Member/Owner_Master')
    get_data.delete_sequence_value('User_Master')
    if cdel is None:
        return RedirectResponse(url='/member/member')

#member Member Upload  
@app.route("/member/memberupload", methods=['GET', 'POST'])
async def amember(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'member':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    notifications=await get_data.notyread(use[0][0])
    ncount=len(notifications)
    return templates.TemplateResponse("MemberDashboard/family_upload.html", {"request": request, "user": use, "notifications": notifications, "ncount": ncount})

@app.post("/mmemberupload")
async def csupload(request: Request, csvfile: UploadFile = File()):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    if csvfile is None or current_user["user_type"] != 'member':
        return RedirectResponse('/member/charmanupload')
    if not csvfile.filename.endswith('.csv'):
        return templates.TemplateResponse(
                "MemberDashboard/family_upload.html",
                {"request": request, "pop_up_message": "Please upload .CSV file.","user": use}
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
        date_str = row[4]
        date = datetime.strptime(date_str, '%d-%m-%Y').date()
        date=date.strftime('%Y-%m-%d')
        dob=datetime.strptime(date, "%Y-%m-%d").date()
        quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==row[16])
        citid= await ssdb.database.fetch_one(quer)
        hashed_pass=auth.encrypt_password(row[8])
        query=ssdb.unit_master.select().where(ssdb.unit_master.c.unit_name==row[11])
        unitn= await ssdb.database.fetch_one(query)
    
        user = ssdb.user_master.insert().values(
        f_name=row[1],
        m_name=row[2],
        l_name=row[3],
        dob=dob,
        gender=row[5],
        address_line1=row[12],
        address_line2=row[13],
        landmark=row[14],
        road=row[15],
        city_id=citid[0],
        email=row[6],
        alternate_email=row[7],
        password=hashed_pass,
        mobile_no=row[9],
        alternate_mobile_no=row[10],
        user_type='familymember',
        created_by=createdby,
        updated_by=createdby
        )
        result =await ssdb.database.fetch_one(user)
        userid=await get_data.select_tableemail(ssdb.user_master,row[6])
        mamber=ssdb.member_master.insert().values(
        member_userid=userid,
        unit_id=unitn[1],
        created_by=createdby,
        updated_by=createdby
        )
        result =await ssdb.database.fetch_one(mamber)
      except ValueError as e:
            print(f"Error converting date for row {e}: {e}")
    return RedirectResponse('/member/member')

#Member Vehicle
@app.route("/member/vehicle", methods=["GET", "POST"])
async def membervehic(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'member':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    query=ssdb.member_master.select().where(ssdb.member_master.c.member_userid==createdby)
    owner=await ssdb.database.fetch_one(query)
    query=ssdb.vehicle_master.select().where(ssdb.vehicle_master.c.unit_id==owner[3])
    vehi=await ssdb.database.fetch_all(query)
    notifications=await get_data.notyread(use[0][0])
    ncount=len(notifications)
    return templates.TemplateResponse("MemberDashboard/Vehicle.html", {"request": request, "user": use, "vehicle": vehi, "notifications": notifications, "ncount": ncount})

#Member Vehicle Insert
@app.route("/member/vehicleinsert", methods=["GET", "POST"])
async def membervehicins(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'member':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    return templates.TemplateResponse("MemberDashboard/vehicle_insert.html", {"request": request})

@app.post("/membervehicleinsertr")
async def membercare(request: Request, vtype : int = Form(...), vnumber : str = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    query=ssdb.member_master.select().where(ssdb.member_master.c.member_userid==createdby)
    owner=await ssdb.database.fetch_one(query)
    user = ssdb.vehicle_master.insert().values(
        vehicle_type=vtype,
        vehicle_number=vnumber,
        unit_id=owner[3],
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(user)
    return RedirectResponse("/member/vehicle")

#Member Vehicle Edit
@app.get("/member/vehicleedit/{v_id}")
async def membervehicedit(request: Request, v_id : int):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'member':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    query=ssdb.vehicle_master.select().where(ssdb.vehicle_master.c.vehicle_id==v_id)
    vehi=await ssdb.database.fetch_one(query)
    return templates.TemplateResponse("MemberDashboard/vehicle_edit.html", {"request": request, "v": vehi})

@app.post("/vehicleed/{v_id}")
async def membervehicedit(request: Request, v_id : int, vtype : int = Form(...), vnumber : str = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    user = ssdb.vehicle_master.update().values(
        vehicle_type=vtype,
        vehicle_number=vnumber,
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.vehicle_master.c.vehicle_id==v_id)
    result =await ssdb.database.fetch_one(user)
    return RedirectResponse("/member/vehicle")

#Member Vehicle Delete
@app.get("/vehicledel/{v_id}")
async def charidel(request: Request, v_id: int):
    query=ssdb.vehicle_master.delete().where(ssdb.vehicle_master.c.vehicle_id==v_id)
    cdel=await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Vehicle_Master')
    if cdel is None:
        return RedirectResponse(url='/member/vehicle')

#Member Caretaker
@app.route("/member/caretaker", methods=["GET", "POST"])
async def membercare(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'member':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    query=select(ssdb.caretaker_master,ssdb.user_master).select_from(
       ssdb.caretaker_master.join(
           ssdb.user_master,
           ssdb.user_master.c.user_id==ssdb.caretaker_master.c.user_id
       )
    )
    car=await ssdb.database.fetch_all(query)
    notifications=await get_data.notyread(use[0][0])
    ncount=len(notifications)
    return templates.TemplateResponse("MemberDashboard/Caretaker.html", {"request": request, "user": use, "care": car, "notifications": notifications, "ncount": ncount})

#Member Caretaker Insert  
@app.route("/member/acaretakerinsert", methods=['GET', 'POST'])
async def acaretaker(request: Request):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'member':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   email = current_user["email"]
   query=ssdb.city_master.select()
   cit=await ssdb.database.fetch_all(query)
   return templates.TemplateResponse("MemberDashboard/caretaker_insert.html", {"request": request, "cit": cit}) 

@app.post("/memcaretakerins")
async def adminmebinsert(request: Request, firstname : str = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: Optional[str] = Form(None), altemail: Optional[str] = Form(None), servicetyp: str = Form(...), address1: str = Form(...), address2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), altmobile: Optional[str] = Form(None)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    citid= await ssdb.database.fetch_one(quer)
    user = ssdb.user_master.insert().values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
        address_line1=address1,
        address_line2=address2,
        landmark=landmarks,
        road=Road,
        city_id=citid[0],
        email=emaill,
        alternate_email=altemail,
        mobile_no=mobile,
        alternate_mobile_no=altmobile,
        user_type='caretaker',
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(user)
    query=ssdb.user_master.select().where(ssdb.user_master.c.mobile_no==mobile)
    userid=await ssdb.database.fetch_one(query)
    caretkae=ssdb.caretaker_master.insert().values(
        user_id=userid[0],
        service_type=servicetyp,
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(caretkae)
    return RedirectResponse('/member/caretaker')

#Member Caretaker edit  
@app.get("/member/caretakeredit/{c_id}")
async def acaretaker(request: Request, c_id: int):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'member':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   email = current_user["email"]
   query=ssdb.city_master.select()
   cit=await ssdb.database.fetch_all(query)
   query=select(ssdb.caretaker_master,ssdb.user_master,ssdb.city_master).select_from(
       ssdb.caretaker_master.join(
           ssdb.user_master,
           ssdb.user_master.c.user_id==ssdb.caretaker_master.c.user_id
       ).join(
           ssdb.city_master,
           ssdb.city_master.c.city_id==ssdb.user_master.c.city_id
       )
   ).where(ssdb.caretaker_master.c.c_id==c_id)
   care=await ssdb.database.fetch_one(query)
   return templates.TemplateResponse("MemberDashboard/caretaker_edit.html", {"request": request, "cit": cit, "car": care}) 

@app.post("/memcaretakeredit/{c_id}")
async def admincaredit(request: Request, c_id: int, firstname : str = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: Optional[str] = Form(None), altemail: Optional[str] = Form(None), servicetyp: str = Form(...), address1: str = Form(...), address2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), altmobile: Optional[str] = Form(None)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    citid= await ssdb.database.fetch_one(quer)
    query=ssdb.caretaker_master.select().where(ssdb.caretaker_master.c.c_id==c_id)
    uid=await ssdb.database.fetch_one(query)
    user = ssdb.user_master.update().values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
        address_line1=address1,
        address_line2=address2,
        landmark=landmarks,
        road=Road,
        city_id=citid[0],
        email=emaill,
        alternate_email=altemail,
        mobile_no=mobile,
        alternate_mobile_no=altmobile,
        user_type='caretaker',
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.user_master.c.user_id==uid[1])
    result =await ssdb.database.fetch_one(user)
    caretkae=ssdb.caretaker_master.update().values(
        user_id=uid[1],
        service_type=servicetyp,
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.caretaker_master.c.c_id==c_id)
    result =await ssdb.database.fetch_one(caretkae)
    return RedirectResponse('/member/caretaker')

#Memebr Caretaker Delete
@app.get("/memcaretakerdel/{c_id}")
async def charidel(request: Request, c_id: int):
    query=ssdb.caretaker_master.select().where(ssdb.caretaker_master.c.c_id==c_id)
    uid=await ssdb.database.fetch_one(query)
    query=ssdb.user_master.delete().where(ssdb.user_master.c.user_id==uid[1])
    udel=await ssdb.database.fetch_one(query)
    query=ssdb.caretaker_master.delete().where(ssdb.caretaker_master.c.c_id==c_id)
    cdel=await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Caretaker_Master')
    get_data.delete_sequence_value('User_Master')
    if cdel is None:
        return RedirectResponse(url='/member/caretaker')

#Member Frequantly Visting
@app.route("/member/frequant", methods=["GET", "POST"])
async def memberfrequantly(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'member':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    query=ssdb.member_master.select().where(ssdb.member_master.c.member_userid==use[0][0])
    unitid=await ssdb.database.fetch_one(query)
    query=ssdb.frequently_visiting_master.select().where(ssdb.frequently_visiting_master.c.unit_id==unitid[3])
    freq=await ssdb.database.fetch_all(query)
    notifications=await get_data.notyread(use[0][0])
    ncount=len(notifications)
    return templates.TemplateResponse("MemberDashboard/Frequantly.html", {"request": request, "user": use, "freq": freq, "notifications": notifications, "ncount": ncount})

#Member Guest
@app.route("/member/guest", methods=["GET", "POST"])
async def memberguest(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'member':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    query=ssdb.member_master.select().where(ssdb.member_master.c.member_userid==use[0][0])
    unitid=await ssdb.database.fetch_one(query)
    query=ssdb.guest_master.select().where(ssdb.guest_master.c.unit_id==unitid[3])
    guest=await ssdb.database.fetch_all(query)
    notifications=await get_data.notyread(use[0][0])
    ncount=len(notifications)
    return templates.TemplateResponse("MemberDashboard/Guest.html", {"request": request, "user": use, "guest": guest, "notifications": notifications, "ncount": ncount})

#Member Guest insert
@app.route("/member/mguestinsert", methods=['GET', 'POST'])
async def aguest_insert(request: Request):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'member':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   query=ssdb.unit_master.select()
   unit= await ssdb.database.fetch_all(query)
   return templates.TemplateResponse("MemberDashboard/guest_entry.html", {"request": request, "unit": unit})

@app.post("/memguestinsert")
async def aguest_insert(request: Request, gname: str = Form(...), age: str = Form(...), genders: str = Form(...), emaill: Optional[str] = Form(None), mobile: str = Form(...), guestnum: str = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    query=ssdb.member_master.select().where(ssdb.member_master.c.member_userid==createdby)
    unitid=await ssdb.database.fetch_one(query)
    query=ssdb.guest_master.insert().values(
        guest_name=gname,
        unit_id=unitid[3],
        guest_age=age,
        guest_gender=genders,
        guest_number=mobile,
        guest_email=emaill,
        number_of_guest=guestnum,
        created_by=createdby,
        updated_by=createdby
    )
    guest=await ssdb.database.fetch_one(query)
    return RedirectResponse("/member/guest")

#Member Guest Edit
@app.get("/member/mguestedit/{guestid}")
async def aguest_insert(request: Request, guestid : int):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'member':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   query=ssdb.guest_master.select().where(ssdb.guest_master.c.guest_id==guestid)
   guest=await ssdb.database.fetch_one(query)
   return templates.TemplateResponse("MemberDashboard/guest_edit.html", {"request": request, "g": guest})

@app.post("/mguestedit/{guestid}")
async def aguest_insert(request: Request, guestid : int, gname: str = Form(...), age: str = Form(...), genders: str = Form(...), emaill: Optional[str] = Form(None), mobile: str = Form(...), guestnum: str = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    query=ssdb.guest_master.update().values(
        guest_name=gname,
        guest_age=age,
        guest_gender=genders,
        guest_number=mobile,
        guest_email=emaill,
        number_of_guest=guestnum,
        created_by=createdby,
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.guest_master.c.guest_id==guestid)
    guest=await ssdb.database.fetch_one(query)
    return RedirectResponse("/member/guest")

@app.get("/mguestdel/{guestid}")
async def gurddel(request: Request, guestid : int):
    query=ssdb.guest_master.delete().where(ssdb.guest_master.c.guest_id==guestid)
    gdel=await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Guest_Master')
    if gdel is None:
        return RedirectResponse(url='/member/guest')


#Member Profile
@app.route("/member/profile", methods=["GET", "POST"])
async def memberguest(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'member':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    notifications=await get_data.notyread(use[0][0])
    ncount=len(notifications)
    return templates.TemplateResponse("MemberDashboard/users-profile.html", {"request": request, "user": use, "notifications": notifications, "ncount": ncount})

#Member profile edit
@app.post("/memeditprofile/{user_id}")
async def pedit(request: Request, user_id: int, fName:str = Form(...), lName: Optional[str] = Form(), adress1: Optional[str] = Form(), adress2: Optional[str] = Form(), phone: Optional[str] = Form(), email: Optional[str] = Form()):
    current_user = auth.verify_session(request)
    query=ssdb.user_master.update().where(ssdb.user_master.c.user_id==user_id).values(
        f_name=fName,
        l_name=lName,
        address_line1=adress1,
        address_line2=adress2,
        mobile_no=phone,
        email=email
    )
    user=await ssdb.database.fetch_one(query)
    if user is None:
        return RedirectResponse("/member")

#Member Change pass
@app.route("/member/chgpass", methods=['GET', 'POST'])
async def auser(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'member':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    notifications=await get_data.notyread(use[0][0])
    ncount=len(notifications)
    return templates.TemplateResponse("MemberDashboard/chgpass.html", {"request": request, "user": use, "notifications": notifications, "ncount": ncount})

#Member pass edit
@app.post("/memchgpass/{user_id}")
async def pedit(request: Request, user_id: int, password:str = Form(...), newpswd: str = Form(...)):
    current_user = auth.verify_session(request)
    query=ssdb.user_master.select().where(ssdb.user_master.c.user_id==user_id)
    result=await ssdb.database.fetch_one(query)
    hashed_password = result["password"]
    if bcrypt_context.verify(password, hashed_password):
        passs=auth.encrypt_password(newpswd)
        query=ssdb.user_master.update().where(ssdb.user_master.c.user_id==user_id).values(
                password=passs
        )
        user=await ssdb.database.fetch_one(query)
        return RedirectResponse(f"/member?message=Password+changed+successfully", status_code=303)
    return RedirectResponse(f"/member/chgpass?message=Invalid+password", status_code=303)
    

#Security
@app.route("/security", methods=["GET", "POST"])
async def securiyt(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'security':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    ecount=await get_data.getcount(ssdb.entry_master)
    gcount=await get_data.getcount(ssdb.guest_master)
    fcount=await get_data.getcount(ssdb.frequently_visiting_master)
    carcount=await get_data.getcount(ssdb.caretaker_master)
    vcount=await get_data.getcount(ssdb.vehicle_master)
    return templates.TemplateResponse("SecurityDashboard/index.html", {"request": request, "user": use, "ecount": ecount, "gcount":gcount, "fcount":fcount, "carcount":carcount, "vcount":vcount})

#Security Member/Caretaker Entry
@app.route("/security/mcentry", methods=["GET", "POST"])
async def securiyt(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    socid=await get_data.securitysoc(use[0][0])
    query = select(ssdb.entry_master,
                   ssdb.user_master
                   ).select_from(
        ssdb.entry_master.join(
        ssdb.user_master,
        ssdb.entry_master.c.user_id == ssdb.user_master.c.user_id
    )
    ).where(ssdb.entry_master.c.society_id==socid)
    entry=await ssdb.database.fetch_all(query)
    return templates.TemplateResponse("SecurityDashboard/member_caretaker_entry.html", {"request": request, "user": use, "entry": entry})

#Security Member Entry
@app.route("/security/memetinsert", methods=['GET', 'POST'])
async def aguest_insert(request: Request):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'security':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   email = current_user["email"]
   use=await get_data.select_tableuname(ssdb.user_master,email)
   socid=await get_data.securitysoc(use[0][0])
   query=ssdb.unit_master.select().where(ssdb.unit_master.c.society_id==socid)
   unit= await ssdb.database.fetch_all(query)
   query = select(ssdb.member_master,
                   ssdb.unit_master,
                   ssdb.society_master,
                   ssdb.user_master
                   ).select_from(
        ssdb.member_master.join(
        ssdb.unit_master,
        ssdb.unit_master.c.unit_id == ssdb.member_master.c.unit_id
    ).join(
        ssdb.society_master,
        ssdb.society_master.c.society_id == ssdb.unit_master.c.society_id
    ).join(
        ssdb.user_master,
        ssdb.user_master.c.user_id==ssdb.member_master.c.member_userid
    )
                   ).where(ssdb.unit_master.c.society_id==socid)
   mem=await ssdb.database.fetch_all(query)
   return templates.TemplateResponse("SecurityDashboard/member_entry_insert.html", {"request": request, "unit": unit, "member": mem})

@app.post("/smemeninsert")
async def aguest_insert(request: Request, namemberme: int = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    socid=await get_data.securitysoc(use[0][0])
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    query=ssdb.entry_master.insert().values(
        user_id=namemberme,
        society_id=socid,
        created_by=createdby,
        updated_by=createdby
    )
    guest=await ssdb.database.fetch_one(query)
    return RedirectResponse("/security/mcentry")

#Security Entry Delete
@app.get("/seentrydel/{entryid}")
async def gurddel(request: Request, entryid : int):
    query=ssdb.entry_master.delete().where(ssdb.entry_master.c.entry_id==entryid)
    gdel=await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Caretaker/Member_entry')
    if gdel is None:
        return RedirectResponse(url='/security/mcentry')

#Security Caretaker Entry
@app.route("/security/careinsert", methods=['GET', 'POST'])
async def aguest_insert(request: Request):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'security':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   email = current_user["email"]
   use=await get_data.select_tableuname(ssdb.user_master,email)
   socid=await get_data.securitysoc(use[0][0])
   query=ssdb.unit_master.select().where(ssdb.unit_master.c.society_id==socid)
   unit= await ssdb.database.fetch_all(query)
   query = select(ssdb.caretaker_master,
                   ssdb.unit_master,
                   ssdb.society_master,
                   ssdb.user_master
                   ).select_from(
        ssdb.caretaker_master.join(
        ssdb.society_master,
        ssdb.society_master.c.society_id == ssdb.unit_master.c.society_id
    ).join(
        ssdb.user_master,
        ssdb.user_master.c.user_id==ssdb.caretaker_master.c.user_id
    )
                   ).where(ssdb.unit_master.c.society_id==socid)
   mem=await ssdb.database.fetch_all(query)
   return templates.TemplateResponse("SecurityDashboard/care_entry_insert.html", {"request": request, "unit": unit, "member": mem})

@app.post("/smemeninsert")
async def aguest_insert(request: Request, namemberme: int = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    socid=await get_data.securitysoc(use[0][0])
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    query=ssdb.entry_master.insert().values(
        user_id=namemberme,
        society_id=socid,
        created_by=createdby,
        updated_by=createdby
    )
    guest=await ssdb.database.fetch_one(query)
    return RedirectResponse("/security/mcentry")


#Security Guest
@app.route("/security/guest", methods=['GET', 'POST'])
async def aguest(request: Request):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'security':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   email = current_user["email"]
   use=await get_data.select_tableuname(ssdb.user_master,email)
   socid=await get_data.securitysoc(use[0][0])
   query=select(
       ssdb.guest_master,
       ssdb.unit_master
   ).select_from(ssdb.guest_master).join(
       ssdb.unit_master,
       ssdb.guest_master.c.unit_id==ssdb.unit_master.c.unit_id
   ).where(ssdb.unit_master.c.society_id==socid)
   guest=await ssdb.database.fetch_all(query)
   return templates.TemplateResponse("SecurityDashboard/Guest_entry.html", {"request": request, "user": use, "guest": guest})

#Security Guest insert
@app.route("/security/guestinsert", methods=['GET', 'POST'])
async def aguest_insert(request: Request):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'security':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   email = current_user["email"]
   use=await get_data.select_tableuname(ssdb.user_master,email)
   socid=await get_data.securitysoc(use[0][0])
   query=ssdb.unit_master.select().where(ssdb.unit_master.c.society_id==socid)
   unit= await ssdb.database.fetch_all(query)
   return templates.TemplateResponse("SecurityDashboard/guest_entry_insert.html", {"request": request, "unit": unit})

@app.post("/sguestinsert")
async def aguest_insert(request: Request, gname: str = Form(...), age: str = Form(...), genders: str = Form(...), emaill: Optional[str] = Form(None), mobile: str = Form(...), guestnum: str = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    query=ssdb.guest_master.insert().values(
        guest_name=gname,
        unit_id='1',
        guest_age=age,
        guest_gender=genders,
        guest_number=mobile,
        guest_email=emaill,
        number_of_guest=guestnum,
        created_by=createdby,
        updated_by=createdby
    )
    guest=await ssdb.database.fetch_one(query)
    query=ssdb.guest_master.select().where(ssdb.guest_master.c.guest_email==emaill)
    guest=await ssdb.database.fetch_one(query)
    ruid=await get_data.memuid(1)
    query=ssdb.notification_master.insert().values(
        sender_id=createdby,
        reciver_id=ruid,
        unit_id='1',
        massage=f"{gname} is requesting to enter the society.",
        g_name=gname
    )
    noty=await ssdb.database.fetch_one(query)
    return templates.TemplateResponse("SecurityDashboard/waiting.html", {"request": request, "user": use, "guest": guest})

#Security Guest waiting
@app.get("/waiting/{guestid}")
async def aguest_insert(request: Request, guestid : int):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'security':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   email = current_user["email"]
   use=await get_data.select_tableuname(ssdb.user_master,email)
   query=ssdb.guest_master.select().where(ssdb.guest_master.c.guest_id==guestid)
   guest=await ssdb.database.fetch_one(query)
   query=ssdb.notification_master.select().where(ssdb.notification_master.c.sender_id==use[0][0])
   send=await ssdb.database.fetch_one(query)
   if guest is not None:
       return RedirectResponse(f"/security/guest?message=Entry+Approved", status_code=303)
   elif send is None:
       return RedirectResponse(f"/security/guest?message=Entry+Desapproved", status_code=303)
   else:
       return templates.TemplateResponse("SecurityDashboard/waiting.html", {"request": request, "user": use, "guest": guest})

#Security Guest edit
@app.get("/security/guestedit/{guestid}")
async def aguest_insert(request: Request, guestid : int):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'security':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   email = current_user["email"]
   use=await get_data.select_tableuname(ssdb.user_master,email)
   socid=await get_data.securitysoc(use[0][0])
   query=ssdb.unit_master.select().where(ssdb.unit_master.c.society_id==socid)
   unit= await ssdb.database.fetch_all(query)
   query=select(
       ssdb.guest_master,
       ssdb.unit_master
   ).where(ssdb.guest_master.c.guest_id==guestid).select_from(ssdb.guest_master).join(
       ssdb.unit_master,
       ssdb.guest_master.c.unit_id==ssdb.unit_master.c.unit_id
   )
   guest=await ssdb.database.fetch_one(query)
   return templates.TemplateResponse("SecurityDashboard/guest_edit.html", {"request": request, "unit": unit, "g": guest})

@app.post("/seguestedit/{guestid}")
async def aguest_insert(request: Request, guestid : int, gname: str = Form(...), unitname: str = Form(...), age: str = Form(...), genders: str = Form(...), emaill: Optional[str] = Form(None), mobile: str = Form(...), guestnum: str = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    que=ssdb.unit_master.select().where(ssdb.unit_master.c.unit_name==unitname)
    unitid=await ssdb.database.fetch_one(que)
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    query=ssdb.guest_master.update().values(
        guest_name=gname,
        unit_id=unitid[0],
        guest_age=age,
        guest_gender=genders,
        guest_number=mobile,
        guest_email=emaill,
        number_of_guest=guestnum,
        created_by=createdby,
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.guest_master.c.guest_id==guestid)
    guest=await ssdb.database.fetch_one(query)
    return RedirectResponse("/security/guest")

#Security Guest Delete
@app.get("/seguestdel/{guestid}")
async def gurddel(request: Request, guestid : int):
    query=ssdb.guest_master.delete().where(ssdb.guest_master.c.guest_id==guestid)
    gdel=await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Guest_Master')
    if gdel is None:
        return RedirectResponse(url='/security/guest')


#Security Frequantly Visting
@app.route("/security/frequant", methods=["GET", "POST"])
async def memberfrequantly(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'security':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    socid=await get_data.securitysoc(use[0][0])
    query=select(
        ssdb.frequently_visiting_master,
        ssdb.unit_master
    ).where(ssdb.frequently_visiting_master.c.society_id==socid).select_from(ssdb.frequently_visiting_master).join(
       ssdb.unit_master,
       ssdb.frequently_visiting_master.c.unit_id==ssdb.unit_master.c.unit_id
   )
    freq=await ssdb.database.fetch_all(query)
    return templates.TemplateResponse("SecurityDashboard/Frequantly.html", {"request": request, "user": use, "freq": freq})

#Security Frequantly insert
@app.route("/security/freqinsert", methods=['GET', 'POST'])
async def aguest_insert(request: Request):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'security':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   email = current_user["email"]
   use=await get_data.select_tableuname(ssdb.user_master,email)
   socid=await get_data.securitysoc(use[0][0])
   query=ssdb.unit_master.select().where(ssdb.unit_master.c.society_id==socid)
   unit= await ssdb.database.fetch_all(query)
   return templates.TemplateResponse("SecurityDashboard/freq_entry_insert.html", {"request": request, "unit": unit})

@app.post("/sfreqtinsert")
async def aguest_insert(request: Request, fname: str = Form(...), stype: str = Form(...), unitname: str = Form(...), gender: str = Form(...), mobile: str = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    socid=await get_data.securitysoc(use[0][0])
    que=ssdb.unit_master.select().where(ssdb.unit_master.c.unit_name==unitname)
    unitid=await ssdb.database.fetch_one(que)
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    query=ssdb.frequently_visiting_master.insert().values(
        f_name=fname,
        f_number=mobile,
        f_gender=gender,
        unit_id=unitid[0],
        society_id=socid,
        f_service_type=stype,
        created_by=createdby,
        updated_by=createdby
    )
    freq=await ssdb.database.fetch_one(query)
    return RedirectResponse("/security/frequant")

#Security Frequantly edit
@app.get("/security/freedit/{freqid}")
async def aguest_insert(request: Request, freqid : int):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'security':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   email = current_user["email"]
   use=await get_data.select_tableuname(ssdb.user_master,email)
   socid=await get_data.securitysoc(use[0][0])
   query=ssdb.unit_master.select().where(ssdb.unit_master.c.society_id==socid)
   unit= await ssdb.database.fetch_all(query)
   query=ssdb.frequently_visiting_master.select().where(ssdb.frequently_visiting_master.c.f_id==freqid)
   freq=await ssdb.database.fetch_one(query)
   return templates.TemplateResponse("SecurityDashboard/freq_edit.html", {"request": request, "unit": unit, "freq": freq})

@app.post("/sefreqeidit/{freqid}")
async def aguest_insert(request: Request, freqid: int, fname: str = Form(...), stype: str = Form(...), unitname: str = Form(...), gender: str = Form(...), mobile: str = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    socid=await get_data.securitysoc(use[0][0])
    que=ssdb.unit_master.select().where(ssdb.unit_master.c.unit_name==unitname)
    unitid=await ssdb.database.fetch_one(que)
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    query=ssdb.frequently_visiting_master.update().values(
        f_name=fname,
        f_number=mobile,
        f_gender=gender,
        unit_id=unitid[0],
        society_id=socid,
        f_service_type=stype,
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.frequently_visiting_master.c.f_id==freqid)
    freq=await ssdb.database.fetch_one(query)
    return RedirectResponse("/security/frequant")

#Security Frequantly Delete
@app.get("/sefreq/{freqid}")
async def freqdel(request: Request, freqid : int):
    query=ssdb.frequently_visiting_master.delete().where(ssdb.frequently_visiting_master.c.f_id==freqid)
    gdel=await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Frequently_Visiting_Master')
    if gdel is None:
        return RedirectResponse(url='/security/frequant')
    
#Security Caretaker   
@app.route("/security/caretaker", methods=['GET', 'POST'])
async def caretaker(request: Request):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'security':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   email = current_user["email"]
   use=await get_data.select_tableuname(ssdb.user_master,email)
   socid=await get_data.securitysoc(use[0][0])
   query=ssdb.unit_master.select().where(ssdb.unit_master.c.society_id==socid)
   unit= await ssdb.database.fetch_one(query)
   query=select(ssdb.caretaker_master,ssdb.user_master,ssdb.caretaker_schedule_master).select_from(
       ssdb.caretaker_master.join(
           ssdb.user_master,
           ssdb.user_master.c.user_id==ssdb.caretaker_master.c.user_id
       ).join(
           ssdb.caretaker_schedule_master,
           ssdb.caretaker_schedule_master.c.ct_id==ssdb.caretaker_master.c.c_id
       )
   ).where(ssdb.caretaker_schedule_master.c.unit_id==unit[0])
   care=await ssdb.database.fetch_all(query)
   return templates.TemplateResponse("SecurityDashboard/caretaker.html", {"request": request, "user": use, "caretaker": care})

 #Security Caretaker Insert  
@app.route("/security/secaretakerinsert", methods=['GET', 'POST'])
async def acaretaker(request: Request):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'security':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   email = current_user["email"]
   query=ssdb.city_master.select()
   cit=await ssdb.database.fetch_all(query)
   return templates.TemplateResponse("SecurityDashboard/caretaker_insert.html", {"request": request, "cit": cit}) 

@app.post("/secaretakeredit")
async def adminmebinsert(request: Request, firstname : str = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: Optional[str] = Form(None), altemail: Optional[str] = Form(None), servicetyp: str = Form(...), address1: str = Form(...), address2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), altmobile: Optional[str] = Form(None)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    citid= await ssdb.database.fetch_one(quer)
    user = ssdb.user_master.insert().values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
        address_line1=address1,
        address_line2=address2,
        landmark=landmarks,
        road=Road,
        city_id=citid[0],
        email=emaill,
        alternate_email=altemail,
        mobile_no=mobile,
        alternate_mobile_no=altmobile,
        user_type='caretaker',
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(user)
    query=ssdb.user_master.select().where(ssdb.user_master.c.mobile_no==mobile)
    userid=await ssdb.database.fetch_one(query)
    caretkae=ssdb.caretaker_master.insert().values(
        user_id=userid[0],
        service_type=servicetyp,
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(caretkae)
    return RedirectResponse('/security/caretaker')

#Security Caretaker edit  
@app.get("/security/caretakeredit/{c_id}")
async def acaretaker(request: Request, c_id: int):
   current_user = auth.verify_session(request)
   if current_user is None or current_user["user_type"] != 'security':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
   email = current_user["email"]
   query=ssdb.city_master.select()
   cit=await ssdb.database.fetch_all(query)
   query=select(ssdb.caretaker_master,ssdb.user_master,ssdb.city_master).select_from(
       ssdb.caretaker_master.join(
           ssdb.user_master,
           ssdb.user_master.c.user_id==ssdb.caretaker_master.c.user_id
       ).join(
           ssdb.city_master,
           ssdb.city_master.c.city_id==ssdb.user_master.c.city_id
       )
   ).where(ssdb.caretaker_master.c.c_id==c_id)
   care=await ssdb.database.fetch_one(query)
   return templates.TemplateResponse("SecurityDashboard/caretaker_edit.html", {"request": request, "cit": cit, "car": care}) 

@app.post("/secaretakeredit/{c_id}")
async def admincaredit(request: Request, c_id: int, firstname : str = Form(...), middlename : str = Form(...), lastname: str = Form(...), gender: str= Form(...), dob: date = Form(),emaill: Optional[str] = Form(None), altemail: Optional[str] = Form(None), servicetyp: str = Form(...), address1: str = Form(...), address2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...), mobile:str = Form(...), altmobile: Optional[str] = Form(None)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==citys)
    citid= await ssdb.database.fetch_one(quer)
    query=ssdb.caretaker_master.select().where(ssdb.caretaker_master.c.c_id==c_id)
    uid=await ssdb.database.fetch_one(query)
    user = ssdb.user_master.update().values(
        f_name=firstname,
        m_name=middlename,
        l_name=lastname,
        dob=dob,
        gender=gender,
        address_line1=address1,
        address_line2=address2,
        landmark=landmarks,
        road=Road,
        city_id=citid[0],
        email=emaill,
        alternate_email=altemail,
        mobile_no=mobile,
        alternate_mobile_no=altmobile,
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.user_master.c.user_id==uid[1])
    result =await ssdb.database.fetch_one(user)
    caretkae=ssdb.caretaker_master.update().values(
        user_id=uid[1],
        service_type=servicetyp,
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.caretaker_master.c.c_id==c_id)
    result =await ssdb.database.fetch_one(caretkae)
    return RedirectResponse('/security/caretaker')

#Security Caretaker Delete
@app.get("/secaretakerdel/{c_id}")
async def charidel(request: Request, c_id: int):
    query=ssdb.caretaker_master.select().where(ssdb.caretaker_master.c.c_id==c_id)
    uid=await ssdb.database.fetch_one(query)
    query=ssdb.user_master.delete().where(ssdb.user_master.c.user_id==uid[1])
    udel=await ssdb.database.fetch_one(query)
    query=ssdb.caretaker_master.delete().where(ssdb.caretaker_master.c.c_id==c_id)
    cdel=await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Caretaker_Master')
    get_data.delete_sequence_value('User_Master')
    if cdel is None:
        return RedirectResponse(url='/security/caretaker')
    
#Security Caretaker Upload
@app.route("/security/car_upload", methods=['GET', 'POST'])
async def gurd_upload(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'security':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("SecurityDashboard/care_upload.html", {"request": request,"user": use})

@app.post("/secareupload")
async def csupload(request: Request, csvfile: UploadFile = File()):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    if current_user["user_type"] != 'security':
        return RedirectResponse('/security/car_upload')
    if csvfile is None or not csvfile.filename.endswith('.csv'):
        return templates.TemplateResponse(
                "SecurityDashboard/care_upload.html",
                {"request": request, "pop_up_message": "Please upload .CSV file.","user": use}
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
        date_str = row[4]
        date = datetime.strptime(date_str, '%d-%m-%Y').date()
        date=date.strftime('%Y-%m-%d')
        dob=datetime.strptime(date, "%Y-%m-%d").date()
        quer = ssdb.city_master.select().where(ssdb.city_master.c.city_name==row[15])
        citid= await ssdb.database.fetch_one(quer)
    
        user = ssdb.user_master.insert().values(
        f_name=row[1],
        m_name=row[2],
        l_name=row[3],
        dob=dob,
        gender=row[5],
        address_line1=row[11],
        address_line2=row[12],
        landmark=row[13],
        road=row[14],
        city_id=citid[0],
        email=row[6],
        alternate_email=row[7],
        mobile_no=row[9],
        alternate_mobile_no=row[10],
        user_type='caretaker',
        created_by=createdby,
        updated_by=createdby
        )
        result =await ssdb.database.fetch_one(user)
        query=ssdb.user_master.select().where(ssdb.user_master.c.mobile_no==row[9])
        userid=await ssdb.database.fetch_one(query)
        caretkae=ssdb.caretaker_master.insert().values(
        user_id=userid[0],
        service_type=row[8],
        created_by=createdby,
        updated_by=createdby
        )
        result =await ssdb.database.fetch_one(caretkae)
      except ValueError as e:
            print(f"Error converting date for row {e}: {e}")
    return RedirectResponse('/security/caretaker')

#Security Vehicle
@app.route("/security/vehicle", methods=["GET", "POST"])
async def membervehic(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'security':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    query=ssdb.member_master.select().where(ssdb.member_master.c.member_userid==createdby)
    owner=await ssdb.database.fetch_one(query)
    query=ssdb.vehicle_master.select()
    vehi=await ssdb.database.fetch_all(query)
    return templates.TemplateResponse("SecurityDashboard/vehicle.html", {"request": request, "user": use, "vehicle": vehi})

#Security Vehicle Insert
@app.route("/security/vehicleinsert", methods=["GET", "POST"])
async def membervehicins(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'security':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    query=ssdb.unit_master.select().where()
    unit= await ssdb.database.fetch_all(query)
    return templates.TemplateResponse("SecurityDashboard/vehicle_insert.html", {"request": request, "unit": unit})

@app.post("/securityvehicleinsertr")
async def membercare(request: Request, vtype : int = Form(...), vnumber : str = Form(...), unitname : str = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    que=ssdb.unit_master.select().where(ssdb.unit_master.c.unit_name==unitname)
    unitid=await ssdb.database.fetch_one(que)
    user = ssdb.vehicle_master.insert().values(
        vehicle_type=vtype,
        vehicle_number=vnumber,
        unit_id=unitid[0],
        created_by=createdby,
        updated_by=createdby
    )
    result =await ssdb.database.fetch_one(user)
    return RedirectResponse("/security/vehicle")

#Security Vehicle Edit
@app.get("/security/vehicleedit/{v_id}")
async def membervehicedit(request: Request, v_id : int):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'security':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    query=ssdb.vehicle_master.select().where(ssdb.vehicle_master.c.vehicle_id==v_id)
    vehi=await ssdb.database.fetch_one(query)
    return templates.TemplateResponse("SecurityDashboard/vehicle_edit.html", {"request": request, "v": vehi})

@app.post("/sevehicleed/{v_id}")
async def membervehicedit(request: Request, v_id : int, vtype : int = Form(...), vnumber : str = Form(...)):
    current_user = auth.verify_session(request)
    email = current_user["email"]
    createdby=await get_data.select_tableemail(ssdb.user_master,email)
    user = ssdb.vehicle_master.update().values(
        vehicle_type=vtype,
        vehicle_number=vnumber,
        updated_by=createdby,
        updated_date=todaydate()
    ).where(ssdb.vehicle_master.c.vehicle_id==v_id)
    result =await ssdb.database.fetch_one(user)
    return RedirectResponse("/security/vehicle")

#Security Vehicle Delete
@app.get("/sevehicledel/{v_id}")
async def charidel(request: Request, v_id: int):
    query=ssdb.vehicle_master.delete().where(ssdb.vehicle_master.c.vehicle_id==v_id)
    cdel=await ssdb.database.fetch_one(query)
    get_data.delete_sequence_value('Vehicle_Master')
    if cdel is None:
        return RedirectResponse(url='/security/vehicle')

#Security Profile
@app.route("/security/profile", methods=["GET", "POST"])
async def memberguest(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'security':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("SecurityDashboard/users-profile.html", {"request": request, "user": use})

#Security Profile edit
@app.post("/seeditprofile/{user_id}")
async def pedit(request: Request, user_id: int, fName:str = Form(...), lName: Optional[str] = Form(), adress1: Optional[str] = Form(), adress2: Optional[str] = Form(), phone: Optional[str] = Form(), email: Optional[str] = Form()):
    current_user = auth.verify_session(request)
    query=ssdb.user_master.update().where(ssdb.user_master.c.user_id==user_id).values(
        f_name=fName,
        l_name=lName,
        address_line1=adress1,
        address_line2=adress2,
        mobile_no=phone,
        email=email
    )
    user=await ssdb.database.fetch_one(query)
    if user is None:
        return RedirectResponse("/security")

#Security Change pass
@app.route("/security/chgpass", methods=['GET', 'POST'])
async def auser(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None or current_user["user_type"] != 'security':
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login Required"}
            )
    email = current_user["email"]
    use=await get_data.select_tableuname(ssdb.user_master,email)
    return templates.TemplateResponse("SecurityDashboard/chgpass.html", {"request": request, "user": use})

#Security pass edit
@app.post("/secchgpass/{user_id}")
async def pedit(request: Request, user_id: int, password:str = Form(...), newpswd: str = Form(...)):
    current_user = auth.verify_session(request)
    query=ssdb.user_master.select().where(ssdb.user_master.c.user_id==user_id)
    result=await ssdb.database.fetch_one(query)
    hashed_password = result["password"]
    if bcrypt_context.verify(password, hashed_password):
        passs=auth.encrypt_password(newpswd)
        query=ssdb.user_master.update().where(ssdb.user_master.c.user_id==user_id).values(
                password=passs
        )
        user=await ssdb.database.fetch_one(query)
        return RedirectResponse(f"/security?message=Password+changed+successfully", status_code=303)
    return RedirectResponse(f"/security/chgpass?message=Invalid+password", status_code=303)


#LOGIN
@app.route("/login", methods=["GET", "POST"])
async def login(request: Request, email: str = Form(...), password: str = Form(...), session_token: str = Cookie(...)):
    if request.method == "POST":
    
        # Retrieve form data
        form_data = await request.form()

        # Extract email and password from form data
        email = form_data.get("emaill", "")
        password = form_data.get("pasword", "")

        # Perform login verification logic here
        query = ssdb.user_master.select().where(ssdb.user_master.c.email == email)
        result = await ssdb.database.fetch_one(query)

        if result:
            hashed_password = result["password"]
            if bcrypt_context.verify(password, hashed_password):
                user_type = result["user_type"]

                if user_type == "admin":
                    session_token = secrets.token_urlsafe(32)
                    auth.session_storage[session_token] = {"username": email, "user_type": user_type}
                    # Set the session token as a cookie in the response
                    response = RedirectResponse('/admin')
                    response.set_cookie("session_token", session_token)
                    return response
            
                elif user_type == "chairman":
                    session_token = secrets.token_urlsafe(32)
                    auth.session_storage[session_token] = {"username": email, "user_type": user_type }
                    # Set the session token as a cookie in the response
                    response = RedirectResponse('/chairman')
                    response.set_cookie("session_token", session_token)
                    return response
                
                elif user_type == "member":
                    session_token = secrets.token_urlsafe(32)
                    auth.session_storage[session_token] = {"username": email, "user_type": user_type }
                    # Set the session token as a cookie in the response
                    response = RedirectResponse('/member')
                    response.set_cookie("session_token", session_token)
                    return response  

                elif user_type == "security":
                    session_token = secrets.token_urlsafe(32)
                    auth.session_storage[session_token] = {"username": email, "user_type": user_type }
                    # Set the session token as a cookie in the response
                    response = RedirectResponse('/security')
                    response.set_cookie("session_token", session_token)
                    return response     
                      
            else:
                 return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Login failed."}
            ) 

        else:
            query = ssdb.security_agency_master.select().where(ssdb.security_agency_master.c.email == email)
            result = await ssdb.database.fetch_one(query)
            if result:
                hashed_password = result["password"]
                if bcrypt_context.verify(password, hashed_password):
                    session_token = secrets.token_urlsafe(32)
                    auth.session_storage[session_token] = {"username": email, "user_type": 'agency'}
                    # Set the session token as a cookie in the response
                    response = RedirectResponse('/agency')
                    response.set_cookie("session_token", session_token)
                    return response
            else:
                # Failed login
                return templates.TemplateResponse(
                    "home/login.html",
                    {"request": request, "pop_up_message": "Login failed."}
                    )       
    # Handle GET request (render login form)

    return templates.TemplateResponse("home/login.html", {"request": request})

#Forgot pass
@app.route("/forgotpswd", methods=["GET", "POST"])
async def forgot(request: Request):
        return templates.TemplateResponse("home/forgotpswd.html", {"request": request})

@app.post("/otpsend")
async def forgot(request: Request, emaill: Optional[str] = Form(...)):
    query = ssdb.user_master.select().where(ssdb.user_master.c.email == emaill)
    result = await ssdb.database.fetch_one(query)
     
    if result:
        auth.OTP = otp.email(emaill)
        otp.reset_otp_after_5_minutes(auth.OTP)
        return templates.TemplateResponse("home/chengpswd.html", {"request": request, "OTP": otp, "email": emaill})
    
    else:
        return templates.TemplateResponse(
                    "home/forgotpswd.html",
                    {"request": request, "pop_up_message": "Invalid Email."}
                    ) 

@app.post("/changpass/{email}")
async def forgot(request: Request, email: str, otp: str = Form(...), pswd: str = Form(...)):
    expected_otp = str(auth.OTP).strip()
    if expected_otp == otp:
        passs=auth.encrypt_password(pswd)
        query=ssdb.user_master.update().where(ssdb.user_master.c.email==email).values(
                password=passs
        )
        user=await ssdb.database.fetch_one(query)
        return templates.TemplateResponse(
                    "home/login.html",
                    {"request": request, "pop_up_message": "Pssword Updated."}
                    )
    else:
        return templates.TemplateResponse(
                    "home/forgotpswd.html",
                    {"request": request, "pop_up_message": "Invalid OTP."}
                    )