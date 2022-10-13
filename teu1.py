#Flaskとrender_template（HTMLを表示させるための関数）をインポート
import re
import sys
from flask import Flask, render_template, request,jsonify
from markupsafe import escape
import sqlite3
import json

#Flaskオブジェクトの生成
app = Flask(__name__)
dbname = r'C:\Users\tuteu\Desktop\RICO\new_teu\ForcedExcursionSystemV2-new_Runner-main\api\gateChecker.sqlite3'

app.config['JSON_AS_ASCII']=False
app.config['JSON_SORT_KEYS']=False


def get_event_department(event_id,department_id):
    
    '''
        event_idとdepartment_idからevent_departmentの情報を検索する
        {'id':1 , 'department__name': "全日男子"} のような辞書オブジェクトが返る
    '''
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


def get_course_layout(department_id, gate_id=None):
    ''' 引数で指定された情報に対応する部門の関門情報（コースレイアウトを含む）を配列にして返す。
        gate_idをNoneにすると、その部門のコース全部を返す。指定すると指定された関門の情報だけ返す。
        空配列が返ったらID指定が間違っている。
    '''
    results = []
    if gate_id == None:
        courses = CourseLayout.objects.select_related('gate').filter(department=department_id).order_by('gateOrder')
    else:
        courses = CourseLayout.objects.select_related('gate').filter(department=department_id, gate__id=gate_id).order_by('gateOrder')

    course_values = courses.values('gate__id', 'gate__name', 'gateOrder', 'distance')
    for course in course_values:
        results.append({"id":course["gate__id"], "gateOrder":course["gateOrder"], "name":course["gate__name"], "distance":course["distance"]})
    return results

@app.route('/gateChecker/api/events/<int:str_event_id>/departments/\
<int:str_dep_id>/gates/<int:str_gate_id>/ranking', methods=['GET'])

def get_gate_ranking( str_event_id, str_dep_id, str_gate_id):
    '''
        ある部門（全日/定時と男女）の、ある関門の通過順位を返す.
        以下のような形式のJSONになる。
        {"department": "全日男子", "gate": "北見北斗高校", "ranking": 
            [
                {"rank": 0, "class": "1年1組1番", "name": "全日A男", "time": "13:00:00"},
                {"rank": 0, "class": "1年1組2番", "name": "全日E平", "time": "13:00:00"}
            ]
        }
    '''
    # connect data
    conn = sqlite3.connect(dbname)
    cur = conn.cursor()

    cur.execute('SELECT Runner.code, person.name, person.yomi,Runner.grade,Runner.classNo,\
                Runner.attendanceNo,Department.gender,Department.tense\
                FROM Runner\
            inner join Person on Runner.person_id=person.pid\
            inner join Department on Runner.department_id=Department.id' + ' where event_id='+ str(str_event_id))


    event_id = int(str_event_id)
    dep_id = int(str_dep_id)
    event_dep = get_event_department(event_id, dep_id)

    course_layout = get_course_layout(dep_id, int(str_gate_id))

    records = Record.objects.select_related('runner', 'gate').filter(
        runner__event_id=event_id, gate__id=course_layout[0]['id'], runner__department__id=dep_id).filter(Q(status=Status.RUNNING.value) | Q(status=Status.STOP.value)
        ).order_by('rank')

    if limit != None:
        records = records[:limit]

    results = {"department": event_dep['department__name'], "gate": course_layout[0]['name'], "ranking":[]}
    for record in records:
        tmp = {}
        tmp['rank'] = convert_rank(record.rank)
        tmp['class'] = make_classno_string(record.runner.grade, record.runner.classNo, record.runner.attendanceNo)
        tmp['name'] = record.runner.person.name
        tmp['time'] = convert_time(record.time)
        results['ranking'].append(tmp)
    eventdeps_json = json.dumps(results, ensure_ascii=False, indent=2)
    return HttpResponse(eventdeps_json, content_type='application/json; charset=UTF-8', status=200)






