from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase,relationship
from sqlalchemy import String,Integer,CHAR

class BaseModel(DeclarativeBase):
    pass


class User(BaseModel):
    __tablename__ = "user_info"
    
    id:Mapped[int] = mapped_column("id",Integer,nullable=False,primary_key=True,autoincrement=True)
    uid:Mapped[str] = mapped_column("uid",String,nullable=True)
    first_name:Mapped[str] = mapped_column("first_name",String,nullable=True)
    middle_name:Mapped[str] = mapped_column("middle_name",String,nullable=True)
    last_name:Mapped[str] = mapped_column("last_name",String,nullable=True)

    attendance:Mapped[list['Attendance']] = relationship(
        "Attendance",
        primaryjoin= "User.id == Attendance.user_id",
        foreign_keys= "[Attendance.user_id]",
        viewonly=True
    )

class Attendance(BaseModel):
    __tablename__ = "user_attendance"

    id:Mapped[int] = mapped_column("id",Integer,nullable=False,primary_key=True,autoincrement=True)
    user_id:Mapped[int] = mapped_column("user_id",Integer,nullable=True)
    type:Mapped[str] = mapped_column("type",CHAR,nullable=True)
    current_time:Mapped[str] = mapped_column("current_time",String,nullable=True)