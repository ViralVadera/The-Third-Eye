import asyncio
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
import uvicorn
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import ssdb

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

database=ssdb.database

@app.on_event("startup")
async def startup_db():
    await database.connect()

@app.on_event("shutdown")
async def shutdown_db():
    await database.disconnect()

@app.get("/")
async def read_root(request: Request):
    query = ssdb.user_master.select()
    result = await database.fetch_all(query)
    return templates.TemplateResponse("home.html", {"request": request, "data": result})

@app.get("/home")
def read_home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.route("/login", methods=["GET", "POST"])
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    if request.method == "POST":
        # Retrieve form data
        form_data = await request.form()

        # Extract email and password from form data
        email = form_data.get("email", "")
        password = form_data.get("password", "")

        # Perform login verification logic here
        query = ssdb.user_master.select().where(ssdb.user_master.c.email == email, ssdb.user_master.c.password == password)
        result = await database.fetch_one(query)

        if result:
            
            user_type = result["user_type"]
            
            if user_type == "admin":
                return templates.TemplateResponse("admin_dashboard.html", {"request": request, "user": result})
            
            elif user_type == "chairman":
                return templates.TemplateResponse("user_dashboard.html", {"request": request, "user": result})
            
            else:
                return templates.TemplateResponse("user_dashboard.html", {"request": request, "user": result})

        else:
            # Failed login
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "pop_up_message": "Login failed. Invalid login credentials."}
            )    
    # Handle GET request (render login form)
    return templates.TemplateResponse("login.html", {"request": request})