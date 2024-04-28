import os
from databases import Database
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table, Boolean, Date, ForeignKey, ForeignKeyConstraint

current_folder = os.path.dirname(os.path.abspath(__file__))
database_file = os.path.join(current_folder, "the_third_eye.sqlite")
DATABASE_URL = f"sqlite+aiosqlite:///{database_file}"
database = Database(DATABASE_URL)
metadata = MetaData()


country_master = Table(
    "Country_Master",
    metadata,
    Column( "country_id " , Integer , primary_key=True,autoincrement=True,index=True),
    Column( "country_name" ,String,index=True,nullable=False),
    Column( " created_by" ,Integer,index=True,nullable=False),
    Column( " updated_by" ,Integer,index=True,nullable=False),
    Column( " created_date" ,Date,index=True,nullable=False),
    Column( " updated_date" ,Date,index=True,nullable=False),
    Column( " is_active" ,Boolean,index=True,nullable=False),
)

state_master = Table(
    "State_Master",
    metadata,
    Column("state_id", Integer, primary_key=True, autoincrement=True, index=True),
    Column("state_name", String, index=True, nullable=False),
    Column("country_id", Integer, index=True, nullable=False),
    Column("created_by", Integer, index=True, nullable=False),
    Column("updated_by", Integer, index=True, nullable=False),
    Column("created_date", Date, index=True, nullable=False),
    Column("updated_date", Date, index=True, nullable=False),
    Column("is_active", Boolean, index=True, nullable=False),
    ForeignKeyConstraint(["state_id"], ["State_Master.state_id"], name="fk_state_city_state_id"),

)

city_master = Table(
    "City_Master",
    metadata,
    Column("city_id", Integer, primary_key=True, autoincrement=True, index=True),
    Column("city_name", String, index=True, nullable=False),
    Column("state_id", Integer, index=True, nullable=False),
    Column("created_by", Integer, index=True, nullable=False),
    Column("updated_by", Integer, index=True, nullable=False),
    Column("created_date", Date, index=True, nullable=False),
    Column("updated_date", Date, index=True, nullable=False),
    Column("is_active", Boolean, index=True, nullable=False),
    ForeignKeyConstraint(["state_id"], ["State_Master.state_id"], name="fk_city_state_state_id"),
)


user_master = Table(
    "User_Master",
    metadata,
    Column("user_id" , Integer , primary_key=True,autoincrement=True,index=True),
    Column( "f_name" ,String,index=True,nullable=False),
    Column( "m_name" ,String,index=True,nullable=False),
    Column( "l_name" ,String,index=True,nullable=False),
    Column("dob",Date,index=True,nullable=False),
    Column("gender",String(length=1),index=True,nullable=False),
    Column("email",String,index=True,nullable=False),
    Column("alternate_email",String,index=True,nullable=True),
    Column("mobile_no",Integer,index=True,nullable=False),
    Column("alternate_mobile_no",Integer,index=True,nullable=True),
    Column("address_line1",String,index=True,nullable=False),
    Column("address_line2",String,index=True,nullable=False),
    Column("landmark",String,index=True,nullable=False),
    Column("road",String,index=True,nullable=True),
    Column("city_id", Integer, index=True, nullable=False),
    Column("password",String,index=True,nullable=True),
    Column("user_type",String,index=True,nullable=False),
    Column( "created_by" ,Integer,index=True,nullable=False),
    Column( "updated_by" ,Integer,index=True,nullable=False),
    Column( "created_date" ,Date,index=True,nullable=False),
    Column( "updated_date" ,Date,index=True,nullable=False),
    Column( "is_active" ,Boolean,index=True,nullable=False),    
    ForeignKeyConstraint(["city_id"], ["City_Master.city_id"], name="fk_user_city_city_id"),  
)

society_master = Table(
    "Society/Appartment_Master",
    metadata,
    Column("society_id" , Integer , primary_key=True,autoincrement=True,index=True),
    Column("society_name" , String ,index=True,nullable=False),
    Column("address_line1" , String ,index=True,nullable=False),
    Column("address_line2",String,index=True,nullable=False),
    Column("landmark",String,index=True,nullable=True),
    Column("road",String,index=True,nullable=True),
    Column( "city" ,String,index=True,nullable=False),
    Column( "build_by" ,Integer,index=True,nullable=False),
    Column( "builder_firm" ,Integer,index=True,nullable=False),
    Column("registration_no",String,index=True,nullable=False),
    Column("registration_year",Date,index=True,nullable=False),
    Column( "created_by" ,Integer,index=True,nullable=False),
    Column( "updated_by" ,Integer,index=True,nullable=False),
    Column( "created_date" ,Date,index=True,nullable=False),
    Column( "updated_date" ,Date,index=True,nullable=False),
    Column( "is_active" ,Boolean,index=True,nullable=False), 
    ForeignKeyConstraint(["build_by"], ["User_Master.user_id"], name="fk_society_user_build_by"), 
)

chairman_master  = Table(
    "Chairman_Master",
    metadata,
    Column("chairman_id" , Integer , primary_key=True,autoincrement=True,index=True),
    Column( "chairman_userid" ,Integer,index=True,nullable=False),
    Column( "society_id" ,Integer,index=True,nullable=False),
    Column("assign_date",Date,index=True,nullable=True),
    Column("assign_till",Date,index=True,nullable=True),
    Column("is_chairman",Boolean,index=True,nullable=False),
    Column( "created_by" ,Integer,index=True,nullable=False),
    Column( "updated_by" ,Integer,index=True,nullable=False),
    Column( "created_date" ,Date,index=True,nullable=False),
    Column( "updated_date" ,Date,index=True,nullable=False),
    Column( "is_active" ,Boolean,index=True,nullable=False), 
    ForeignKeyConstraint(["chairman_userid"], ["User_Master.user_id"], name="fk_chairman_user_chairman_userid"),  
    ForeignKeyConstraint(["society_id"], ["Society/Appartment_Master.society_id"], name="fk_chairman_society_society_id"),
)

unit_master = Table(
    "Unit_Master",
    metadata,
    Column("unit_id" ,Integer , primary_key=True,autoincrement=True,index=True),
    Column( "society_id" ,Integer,index=True,nullable=False),
    Column("unit_name",String,index=True,nullable=True),
    Column("unit_type",String,index=True,nullable=False),
    Column("unit_block",Integer,index=True,nullable=True), 
    Column("unit_floor",Integer,index=True,nullable=False),
    Column( "created_by" ,Integer,index=True,nullable=False),
    Column( "updated_by" ,Integer,index=True,nullable=False),
    Column( "created_date" ,Date,index=True,nullable=False),
    Column( "updated_date" ,Date,index=True,nullable=False),
    Column( "is_active" ,Boolean,index=True,nullable=False), 
    ForeignKeyConstraint(["society_id"], ["Society/Appartment_Master.society_id"], name="fk_unit_society_society_id"),
)

member_master = Table(
    "Member/Owner_Master",
    metadata,
    Column("member_id" ,Integer , primary_key=True,autoincrement=True,index=True),
    Column( "member_userid" ,Integer,index=True,nullable=False),
    Column( "add_by" ,Integer,index=True,nullable=False),
    Column( "unit_id" ,Integer,index=True,nullable=False),
    Column( "created_by" ,Integer,index=True,nullable=False),
    Column( "updated_by" ,Integer,index=True,nullable=False),
    Column( "created_date" ,Date,index=True,nullable=False),
    Column( "updated_date" ,Date,index=True,nullable=False),
    Column( "is_active" ,Boolean,index=True,nullable=False),
    ForeignKeyConstraint(["member_userid"], ["User_Master.user_id"], name="fk_member_user_member_userid"), 
    ForeignKeyConstraint(["add_by"], ["User_Master.user_id"], name="fk_member_user_add_by"),  
    ForeignKeyConstraint(["unit_id"], ["Unit_Master.unit_id"], name="fk_member_unit_unit_id"),   
)

security_agency_master = Table(
    "Security_Agency_Master",
    metadata,
    Column("security_agency_id" ,Integer , primary_key=True,autoincrement=True,index=True),
    Column("security_agency_name",String,index=True,nullable=False),
    Column("agency_license_no",String,index=True,nullable=False),
    Column("agency_address_line1",String,index=True,nullable=False),
    Column("agency_address_line2",String,index=True,nullable=False),
    Column("landmark",String,index=True,nullable=False),
    Column("road",String,index=True,nullable=True),
    Column( "city_id" ,Integer,index=True,nullable=False),
    Column( "state_id" ,Integer,index=True,nullable=False),
    Column("contact_no",Integer,index=True,nullable=False),
    Column("email",String,index=True,nullable=False),
    Column("password",String,index=True,nullable=False),
    Column("agency_type",String,index=True,nullable=True),
    Column( "created_by" ,Integer,index=True,nullable=False),
    Column( "updated_by" ,Integer,index=True,nullable=False),
    Column( "created_date" ,Date,index=True,nullable=False),
    Column( "updated_date" ,Date,index=True,nullable=False),
    Column( "is_active" ,Boolean,index=True,nullable=False),
    ForeignKeyConstraint(["city_id"], ["City_Master.city_id"], name="fk_security_agency_city_city_id"),
    ForeignKeyConstraint(["state_id"], ["State_Master.state_id"], name="fk_security_agency_state_state_id"),  
)

security_master = Table(
    "Security_Master",
    metadata,
    Column("security_id" ,Integer , primary_key=True,autoincrement=True,index=True),
    Column( "user_id" ,Integer,index=True,nullable=False),
    Column( "security_agency_id" ,Integer,index=True,nullable=False),
    Column( "join_date" ,Date,index=True,nullable=False),
    Column( "created_by" ,Integer,index=True,nullable=False),
    Column( "updated_by" ,Integer,index=True,nullable=False),
    Column( "created_date" ,Date,index=True,nullable=False),
    Column( "updated_date" ,Date,index=True,nullable=False),
    Column( "is_active" ,Boolean,index=True,nullable=False), 
    ForeignKeyConstraint(["user_id"], ["User_Master.user_id"], name="fk_security_user_user_id"), 
    ForeignKeyConstraint(["security_agency_id"], ["Security_Agency_Master.security_agency_id"], name="fk_security_security_agency_security_agency_id"),
)


shift_master = Table(
    "Shift_Master",
    metadata,
    Column("shift_id" ,Integer , primary_key=True,autoincrement=True,index=True),
    Column( "shift_time" ,String,index=True,nullable=False),
    Column( "created_by" ,Integer,index=True,nullable=False),
    Column( "updated_by" ,Integer,index=True,nullable=False),
    Column( "created_date" ,Date,index=True,nullable=False),
    Column( "updated_date" ,Date,index=True,nullable=False),
    Column( "is_active" ,Boolean,index=True,nullable=False), 
)

security_shift_master = Table(
    "Security_Shift_Master",
    metadata,
    Column("security_shift_id" ,Integer , primary_key=True,autoincrement=True,index=True),
    Column( "security_id" ,Integer,index=True,nullable=False),
    Column( "society_id" ,Integer,index=True,nullable=False),
    Column( "shift_start_date" ,Date,index=True,nullable=False),
    Column( "shift_end_date" ,Date,index=True,nullable=False),
    Column( "shift_time" ,String,index=True,nullable=False),
    Column( "created_by" ,Integer,index=True,nullable=False),
    Column( "updated_by" ,Integer,index=True,nullable=False),
    Column( "created_date" ,Date,index=True,nullable=False),
    Column( "updated_date" ,Date,index=True,nullable=False),
    Column( "is_active" ,Boolean,index=True,nullable=False),
    ForeignKeyConstraint(["security_id"], ["Security_Master.security_id"], name="fk_security_shift_security_security_id"),   
    ForeignKeyConstraint(["society_id"], ["Society_Master.society_id"], name="fk_security_shift_society_society_id"),  
)

security_allotment_master = Table(
    "Security_Allotment_Master",
    metadata,
    Column("security_allot_id" ,Integer , primary_key=True,autoincrement=True,index=True),
    Column( "security_id" ,Integer,index=True,nullable=False),
    Column( "shift_id" ,Integer,index=True,nullable=False),
    Column( "society_id" ,Integer,index=True,nullable=False),
    Column( "created_by" ,Integer,index=True,nullable=False),
    Column( "updated_by" ,Integer,index=True,nullable=False),
    Column( "created_date" ,Date,index=True,nullable=False),
    Column( "updated_date" ,Date,index=True,nullable=False),
    Column( "is_active" ,Boolean,index=True,nullable=False), 
    ForeignKeyConstraint(["security_id"], ["Security_Master.security_id"], name="fk_security_allot_security_security_id"),  
    ForeignKeyConstraint(["shift_id"], ["Shift_Master.shift_id"], name="fk_security_allot_shift_shift_id"),  
    ForeignKeyConstraint(["society_id"], ["Society_Master.society_id"], name="fk_security_allot_society_society_id"),  
)

guest_master = Table(
    "Guest_Master",
    metadata,
    Column("guest_id" ,Integer , primary_key=True,autoincrement=True,index=True),
    Column( "unit_id" ,Integer,index=True,nullable=False),
    Column( "guest_name" ,String,index=True,nullable=False),
    Column( "guest_age" ,Integer,index=True,nullable=False),
    Column( "guest_gender" ,String(length=1),index=True,nullable=False),
    Column( "guest_number" ,Integer,index=True,nullable=False),
    Column( "guest_email" ,String,index=True,nullable=True),
    Column( "number_of_guest" ,Integer,index=True,nullable=False),
    Column( "entry_time" ,String,index=True,nullable=True),
    Column( "created_by" ,Integer,index=True,nullable=False),
    Column( "updated_by" ,Integer,index=True,nullable=False),
    Column( "created_date" ,Date,index=True,nullable=False),
    Column( "updated_date" ,Date,index=True,nullable=False),
    Column( "is_active" ,Boolean,index=True,nullable=False), 
    ForeignKeyConstraint(["unit_id"], ["Unit_Master.unit_id"], name="fk_guest_unit_unit_id")
)

frequently_visiting_master = Table(
    "Frequently_Visiting_Master",
    metadata,
    Column("f_id" ,Integer , primary_key=True,autoincrement=True,index=True),
    Column( "f_name" ,String,index=True,nullable=True),
    Column( "f_number" ,Integer,index=True,nullable=True),
    Column( "f_gender" ,String(length=1),index=True,nullable=True),
    Column( "unit_id" ,Integer,index=True,nullable=False),
    Column( "society_id" ,Integer,index=True,nullable=False),
    Column( "f_service_type" ,String,index=True,nullable=True),
    Column( "entry_time" ,String,index=True,nullable=False),
    Column( "created_by" ,Integer,index=True,nullable=False),
    Column( "updated_by" ,Integer,index=True,nullable=False),
    Column( "created_date" ,Date,index=True,nullable=False),
    Column( "updated_date" ,Date,index=True,nullable=False),
    Column( "is_active" ,Boolean,index=True,nullable=False), 
    ForeignKeyConstraint(["unit_id"], ["Unit_Master.unit_id"], name="fk_frequently_visiting_unit_unit_id"),
    ForeignKeyConstraint(["society_id"], ["Society_Master.society_id"], name="fk_frequently_visiting_society_society_id"),
)

caretaker_master = Table(
    "Caretaker_Master",
    metadata,
    Column("c_id" ,Integer , primary_key=True,autoincrement=True,index=True),
    Column( "user_id" ,Integer,index=True,nullable=False),
    Column( "service_type" ,String,index=True,nullable=True),
    Column( "created_by" ,Integer,index=True,nullable=False),
    Column( "updated_by" ,Integer,index=True,nullable=False),
    Column( "created_date" ,Date,index=True,nullable=False),
    Column( "updated_date" ,Date,index=True,nullable=False),
    Column( "is_active" ,Boolean,index=True,nullable=False), 
    ForeignKeyConstraint(["user_id"], ["User_Master.user_id"], name="fk_caretaker_user_user_id"),
)

caretaker_schedule_master = Table(
    "Caretaker_Schedule_Master",
    metadata,
    Column("ct_schedule_id" ,Integer , primary_key=True,autoincrement=True,index=True),
    Column( "shift_id" ,Integer,index=True,nullable=False),
    Column( "ct_id" ,Integer,index=True,nullable=False),
    Column( "unit_id" ,Integer,index=True,nullable=False),
    Column( "created_by" ,Integer,index=True,nullable=False),
    Column( "updated_by" ,Integer,index=True,nullable=False),
    Column( "created_date" ,Date,index=True,nullable=False),
    Column( "updated_date" ,Date,index=True,nullable=False),
    Column( "is_active" ,Boolean,index=True,nullable=False),
    ForeignKeyConstraint(["shift_id"], ["Shift_Master.shift_id"], name="fk_caretaker_schedule_shift_shift_id"),
    ForeignKeyConstraint(["ct_id"], ["Caretaker_Master.c_id"], name="fk_caretaker_schedule_caretaker_c_id"),
    ForeignKeyConstraint(["unit_id"], ["Unit_Master.unit_id"], name="fk_caretaker_schedule_unit_unit_id"), 
)

vehicle_master = Table(
    "Vehicle_Master",
    metadata,
    Column("vehicle_id" ,Integer , primary_key=True,autoincrement=True,index=True),
    Column( "vehicle_type" ,Integer,index=True,nullable=False),
    Column( "vehicle_number" ,String,index=True,nullable=False),
    Column( "unit_id" ,Integer,index=True,nullable=False),
    Column( "created_by" ,Integer,index=True,nullable=False),
    Column( "updated_by" ,Integer,index=True,nullable=False),
    Column( "created_date" ,Date,index=True,nullable=False),
    Column( "updated_date" ,Date,index=True,nullable=False),
    Column( "is_active" ,Boolean,index=True,nullable=False), 
    ForeignKeyConstraint(["unit_id"], ["Unit_Master.unit_id"], name="fk_vehicle_unit_unit_id"),
)

entry_master = Table(
    "Caretaker/Member_entry",
    metadata,
    Column("entry_id" ,Integer , primary_key=True,autoincrement=True,index=True),
    Column( "user_id" ,Integer,index=True,nullable=False),
    Column( "society_id" ,Integer,index=True,nullable=False),
    Column( "entry_date" ,String,index=True,nullable=False),
    Column( "created_by" ,Integer,index=True,nullable=False),
    Column( "updated_by" ,Integer,index=True,nullable=False),
    Column( "created_date" ,Date,index=True,nullable=False),
    Column( "updated_date" ,Date,index=True,nullable=False),
    Column( "is_active" ,Boolean,index=True,nullable=False), 
    ForeignKeyConstraint(["user_id"], ["User_Master.user_id"], name="fk_entry_user_user_id"),
    ForeignKeyConstraint(["society_id"], ["Society_Master.society_id"], name="fk_entry_society_society_id"),
)

notification_master = Table(
    "Notification_Master",
    metadata,
    Column("n_id" ,Integer , primary_key=True,autoincrement=True,index=True),
    Column( "sender_id" ,Integer,index=True,nullable=False),
    Column( "reciver_id" ,Integer,index=True,nullable=False),
    Column( "unit_id" ,Integer,index=True,nullable=False),
    Column( "massage" ,String,index=True,nullable=False),
     Column( "g_name" ,String,index=True,nullable=False),
    ForeignKeyConstraint(["sender_id"], ["User_Master.user_id"], name="fk_notification_user_user_id"),
    ForeignKeyConstraint(["reciver_id"], ["User_Master.user_id"], name="fk_notification_user_user_id"),
    ForeignKeyConstraint(["unit_id"], ["Unit_Master.unit_id"], name="fk_notification_unit_unit_id"),
)