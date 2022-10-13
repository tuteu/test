#Flaskとrender_template（HTMLを表示させるための関数）をインポート
import re
import sys
from flask import Flask, render_template, request,jsonify
from markupsafe import escape
import sqlite3
import json
import datetime
import pytz


#Flaskオブジェクトの生成
app = Flask(__name__)
dbname = r'C:\Users\tuteu\Desktop\RICO\new_teu\ForcedExcursionSystemV2-new_Runner-main\api\gateChecker.sqlite3'

app.config['JSON_AS_ASCII']=False
app.config['JSON_SORT_KEYS']=False


def get_event_department(event_id,department_id):
    
   
    conn = sqlite3.connect(dbname)
    cur = conn.cursor()
    cur.execute('SELECT Department.id,Department.name FROM \
     Department inner join  EventDepartment on Department.id=EventDepartment.id\
     where EventDepartment.event_id='+str(event_id)+' AND EventDepartment.department_id='+str(department_id))

    v_event_dep = cur.fetchall()
    result = None
    for event_dep in v_event_dep: # 1個しかないはず
        result = event_dep
    return result

#re=get_event_department(2,4)
#print(re)


def get_course_layout(department_id, gate_id=None):
    ''' 引数で指定された情報に対応する部門の関門情報（コースレイアウトを含む）を配列にして返す。
        gate_idをNoneにすると、その部門のコース全部を返す。指定すると指定された関門の情報だけ返す。
        空配列が返ったらID指定が間違っている。
    '''
    conn = sqlite3.connect(dbname)
    cur = conn.cursor()
    a='SELECT CourseLayout.gate_id,Gate.name,CourseLayout.gateOrder,CourseLayout.distance FROM \
     CourseLayout inner join  Gate on CourseLayout.gate_id=Gate.id'
    results = []
    if gate_id == None:
        courses = cur.execute(a+' where CourseLayout.department_id=' + str(department_id))
    else:
        courses = cur.execute(a+' where CourseLayout.department_id=' + str(department_id)
         +' and  CourseLayout.gate_id=' + str(gate_id))
    v_event_dep = cur.fetchall()


    for course in v_event_dep:
        results.append({"id":course[0], "gateOrder":course[2], "name":course[1], "distance":course[3]})
    return results

#re=get_course_layout(2)
#print(re)
def make_classno_string(grade, classNo, attendanceNo):
    '''何年何組、という文字列表現をintから作る'''
    if grade == 4:
        return u"甲府/定時"
    return str(grade) + u'年' + str(classNo) + u'組' + str(attendanceNo) + "番"
def convert_time(uctTime):
    ''''UTCのDateTimeを日本時間に戻し、かつ、23:59:59の場合表記を変更する'''
    # 日本時間に戻して時分秒の部分のみ取り出す
    tz_tokyo = pytz.timezone('Asia/Tokyo')
    jst_time = uctTime.astimezone(tz_tokyo).strftime('%H:%M:%S')

    #リタイアは23:59:59が設定されるので、表示上--:--:--にする
    if jst_time == "23:59:59":
        jst_time = "--:--:--"

    return jst_time

def convert_rank(rank):
    if rank == 0: # 順位に0がある場合、--に表記を変更する。スタート時や棄権、欠席時などが該当
        return "--"
    else:
        return str(rank)

@app.route("/gateChecker/api/events/<int:str_event_id>/departments/<int:str_dep_id>/gates/<int:str_gate_id>/ranking", methods=['GET'])
def Record( str_event_id, str_dep_id,str_gate_id):
    conn = sqlite3.connect(dbname)
    cur = conn.cursor()

    event_id = int(str_event_id)
    dep_id = int(str_dep_id)
    event_dep = get_event_department(event_id, dep_id)
    course_layout = get_course_layout(dep_id, int(str_gate_id))
    
    b= ' SELECT Runner.id, Person.name, Person.yomi, Runner.grade, Runner.classNo, Runner.attendanceNo\
	FROM Runner inner join Person on Runner.person_id = Person.pid\
	where Runner.event_id ='+ str(event_id) +' and Runner.department_id = '+ str(dep_id)

    a='SELECT r.id, r.time, r.rank, r.status, r.gate_id, r.runner_id,T.name, T.yomi, T.grade, T.classNo, T.attendanceNo \
    FROM Record as r inner join (' +b+')T on r.runner_id = T.id\
    where r.gate_id = 2 and (status = "走行" or status = "停止") order by rank'
    cur.execute(a)
    whole = cur.fetchall()
    #results = {"ranking":[]}
    results = {"department":  event_dep[1], "gate": course_layout[0]['name'], "ranking":[]}
    for record in whole:
        tmp = {}
        tmp['rank'] = convert_rank(record[2])
        tmp['class'] = make_classno_string(record[8], record[9], record[10])
        tmp['name'] = record[6]
        tmp['time'] = record[1]
        results['ranking'].append(tmp)

    cur.close()
    conn.close()
    return jsonify(results) 
#re=Record(1,2,1)
#print(re)
@app.route("/index/<string:name>")
def index(name):
    return render_template("index.html", name=escape(name))
#おまじない
if __name__ == "__main__":
    app.run(debug=True)


