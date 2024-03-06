from fastapi import FastAPI, Form, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn
from typing import Any
from datetime import datetime, date
from passlib.context import CryptContext
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import ssdb
import secrets
import get_data
import auth
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table, Boolean, Date, ForeignKey, ForeignKeyConstraint, update

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    db=get_data.session()
    try:
        yield db
    finally:
        db.close()

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
    query = ssdb.user_master.select()
    result = await ssdb.database.fetch_all(query)
    return templates.TemplateResponse("home/index.html", {"request": request, "data": result})

@app.get("/hello")
def read_hm(request: Request):
    return templates.TemplateResponse("home/index.html", {"request": request})

@app.get("/logout/")
async def logout(request: Request):
    auth.key='TheThirdEye'
    return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "You are logged out."}
            )


@app.route("/admin", methods=['GET', 'POST'])
def admin(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )

    return templates.TemplateResponse("AdminDashboard/index.html", {"request": request})
    

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
    society=await get_data.select_table('society_master')
    user=await get_data.select_table('user_master')
    return templates.TemplateResponse("AdminDashboard/societies.html", {"request": request,"society": society,"user": user})
@app.route("/admin/asocieties_insert", methods=['GET', 'POST'])
def asocieties_insert(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    return templates.TemplateResponse("AdminDashboard/society_insert.html", {"request": request})
@app.post("/adminsocinsert")
async def adminsocinsert(request: Request, Society_name : str = Form(...), builderName : str = Form(...), builderfirm_name: str = Form(...), regnumber: str = Form(...), regdate: str = Form(...), address_1: str = Form(...), address_2: str = Form(...), Road: str = Form(...), landmarks:str = Form(...), citys:str = Form(...)):
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
    
# Pass the string value to the fetch_all method
    result =await ssdb.database.fetch_one(society)
    
    return RedirectResponse('/admin/asocieties')

@app.route("/admin/asecurityagency", methods=['GET', 'POST'])
def asecurityagency(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    return templates.TemplateResponse("AdminDashboard/security_agency.html", {"request": request})
    
@app.route("/admin/asecurityguard", methods=['GET', 'POST'])
def asecurityguard(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    return templates.TemplateResponse("AdminDashboard/security_guard.html", {"request": request})
    
@app.route("/admin/achairmanbuilder", methods=['GET', 'POST'])
def achairmanbuilder(request: Request):
    current_user = auth.verify_session(request)
    if current_user is None:
        return templates.TemplateResponse(
                "home/login.html",
                {"request": request, "pop_up_message": "Invalid Attempt"}
            )
    return templates.TemplateResponse("AdminDashboard/chairman_builder.html", {"request": request})
    
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