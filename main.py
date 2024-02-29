from fastapi import FastAPI, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
import os
import uvicorn
from passlib.context import CryptContext
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import ssdb
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table, Boolean, Date, ForeignKey, ForeignKeyConstraint

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
    query = ssdb.user_master.select()
    result = await ssdb.database.fetch_all(query)
    return templates.TemplateResponse("home/index.html", {"request": request, "data": result})

@app.get("/hello")
def read_hm(request: Request):
    return templates.TemplateResponse("home/index.html", {"request": request})

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
                    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "user": result})
            
                elif user_type == "chairman":
                    return templates.TemplateResponse("chairman_dashboard.html", {"request": request, "user": result})
            
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