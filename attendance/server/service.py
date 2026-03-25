from sqlalchemy import select,and_
from db import db
from model import User,Attendance
from datetime import datetime
from sqlalchemy.orm import contains_eager

def insert_user_info(user:dict):
    sysuser = User(
        uid = user["uid"],
        first_name = user["first_name"],
        middle_name = user.get("middle_name"),
        last_name = user["last_name"]
    )
    db.session.add(sysuser)
    db.session.commit()

def check_attendance(uid:str)->bool:
    now = datetime.now()
    today = now.strftime("%Y-%m-%d") + "%"
    sql = (select(Attendance).join(User,User.id == Attendance.user_id).where(and_(User.uid == uid,Attendance.current_time.like(today))))
    data =  db.session.scalars(sql).all()
    print(len(data))
    if len(data) == 0:
        return True
    else:
        return False

def user_exist(uid:str)->bool:
    user = db.session.scalar(select(User).where(User.uid == uid))
    flag = False
    if user:
        flag = True
    return flag    

def show_attendance()->list:
    time = datetime.now()
    today = time.strftime("%Y-%m-%d") + "%"
    sql = (select(User,Attendance).outerjoin(Attendance,and_(User.id == Attendance.user_id, Attendance.current_time.like(today)))
           .options(contains_eager(User.attendance)))
    data =  db.session.scalars(sql).unique().all()
    result = []
    for item in data:
        result.append({
            "first_name":item.first_name,
            "middle_name":item.middle_name,
            "last_name":item.last_name,
            "attendance":[
                {"type":a.type,
                 "time":a.current_time}
                 for a in item.attendance
            ]
        })
    return result

def insert_attendance(data:dict):
    user = db.session().scalar(select(User).where(User.uid == data["uid"]))
    attendance = db.session.scalar(select(Attendance).where(and_(Attendance.user_id == user.id,Attendance.type == data["type"])))
    if attendance is None:
        attendance = Attendance(
        user_id = user.id,
        type = data["type"],
        current_time = data["current_time"]
         )
        db.session.add(attendance)
    else:
        attendance.current_time = data["current_time"]  
    db.session.commit()

def get_user_info(uid:str)->dict:
    user = db.session().scalar(select(User).where(User.uid == uid))
    if user is not None:
        userResult = {
        "username":user.first_name
    }
    return userResult    