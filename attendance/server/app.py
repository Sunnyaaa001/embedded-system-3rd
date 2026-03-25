from db import app
from service import insert_attendance,insert_user_info,check_attendance,show_attendance,user_exist,get_user_info
from flask import jsonify,request

@app.route('/insert/user',methods = ['POST'])
def record_user():
    data = request.get_json()
    insert_user_info(data)
    return jsonify({"code":200})

@app.route('/check/attendance',methods = ['GET'])
def attendance_check():
    uid = request.args.get("uid","")
    result = check_attendance(uid=uid)
    print(result)
    return jsonify({"code":200,"data":result})

@app.route('/insert/attendance',methods = ['POST'])
def attendance_record():
    data = request.get_json()
    insert_attendance(data=data)
    return jsonify({"code":200})

@app.route('/attendance/show',methods = ['GET'])
def attendance_list():
    data = show_attendance()
    return jsonify({"code":200,"data":data})

@app.route('/user/check',methods = ['GET'])
def check_user():
    uid = request.args.get("uid","")
    flag = user_exist(uid)
    return jsonify({"code":200,"data":flag})

@app.route('/user/info',methods=["GET"])
def user_info():
    uid = request.args.get("uid","")
    userInfo = get_user_info(uid=uid)
    return jsonify({"code":200,"data":userInfo})


if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8080,debug=True)

