import sqlite3
import time

import pandas as pd
from flask import *

app = Flask(__name__)


@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Methods'] = 'GET , POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With, Authorization, Accept'
    return response


def get_db():
    conn = sqlite3.connect('eduvis.sqlite')
    return conn


def calClusterMastery(id_list):
    result = {
        'mastery': [],
        'key_date': [],
        'key_detail': []
    }
    conn = get_db()
    cur = conn.cursor()
    sql = "SELECT ms.score, ms.time, ms.memory, ms.timeconsume,mt.knowledge FROM main.submitrecord as ms join main.titleinfo as mt WHERE student_ID in (" + ', '.join(
        [f"'{item}'" for item in id_list]) + ") and ms.title_ID=mt.title_ID order by ms.time"
    query_result = cur.execute(sql)
    data = [(int(value[0]), value[1], 1, value[4]) for value in query_result]
    df = pd.DataFrame(data, columns=['score', 'timestamp', 'count', 'knowledge'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='s')
    daily_cumulative_sum = df.groupby(df['date'].dt.date)[['score', 'count']].sum()
    daily_cumulative_sum['cumulative_score'] = daily_cumulative_sum['score'].cumsum()
    daily_cumulative_sum['cumulative_count'] = daily_cumulative_sum['count'].cumsum()
    daily_cumulative_sum['mastery'] = daily_cumulative_sum['cumulative_score'] / daily_cumulative_sum[
        'cumulative_count']
    result['mastery'] = [item for item in daily_cumulative_sum['mastery']]
    quantiles = [0, 1 / 3, 2 / 3, 1]
    knowledge = ["r8S3g", "t5V9e", "m3D1v", "s8Y2f", "k4W1c", "g7R2j", "b3C9s", "y9W5d"]
    quantile_dates = daily_cumulative_sum.index.to_series().quantile(quantiles)
    result['key_date'] = [str(item) for item in quantile_dates]
    key_stamps = [time.mktime(time.strptime(str(item), '%Y-%m-%d')) for item in quantile_dates]
    for i in range(len(quantiles) - 1):
        for j in knowledge:
            filtered_df = df[
                (df['timestamp'] > key_stamps[0]) & (df['timestamp'] < key_stamps[1]) & (df['knowledge'] == j)]
            correct_df = filtered_df[filtered_df['score'] != 0]
            result['key_detail'].append({
                'knowledge': j,
                'index': i,
                'count': filtered_df.shape[0],
                'correctness': 0 if correct_df.shape[0] == 0 else correct_df.shape[0] / filtered_df.shape[0]
            })
    return result


def insert_comma(position):
    parts = position.strip('[]').split()
    return [eval(parts[0]), eval(parts[1])]


def calKnoeledgeMastery(id):
    print(id)
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT ms.score, ms.memory, ms.timeconsume,mt.knowledge FROM main.submitrecord as ms join main.titleinfo as mt WHERE student_ID=? and ms.title_ID=mt.title_ID",
        (id,))
    rows = cur.fetchall()
    if not rows:
        return jsonify({
            "msg": "学号无效",
            "code": 0,
        })
    xAxis = {"r8S3g": 0, "t5V9e": 0, "m3D1v": 0, "s8Y2f": 0, "k4W1c": 0, "g7R2j": 0, "b3C9s": 0, "y9W5d": 0}
    datda = {"r8S3g": [], "t5V9e": [], "m3D1v": [], "s8Y2f": [], "k4W1c": [], "g7R2j": [], "b3C9s": [], "y9W5d": []}
    for row in rows:
        xAxis[row[3]] += 1
        if row[2] == '-' or row[2] == '--':
            datda[row[3]].append([int(row[0]), int(row[1]) + 0])
        else:
            datda[row[3]].append([int(row[0]), int(row[1]) + int(row[2])])
    for key in datda:
        accumulate_score = 0
        accumulate_index = 0
        data = []
        for value in datda[key]:
            accumulate_score += value[0]
            accumulate_index += value[1]
            if accumulate_score == 0:
                data.append(0)
            else:
                data.append(accumulate_index / accumulate_score)
        min_value = min(data)
        max_value = max(data)
        datda[key] = [(value - min_value) / (max_value - min_value) for value in data]
    return xAxis, datda


@app.route('/')
def hello_world():  # put application's code here
    return jsonify({
        "msg": "Hello World!",
        "code": 200
    })


# 学习日志接口
@app.route('/getAnswerLog', methods=['GET'])
def getAnswerLog():
    conn = get_db()
    stu_id = request.args.get('stu_id')
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT ms.state, ms.score, mt.knowledge FROM main.submitrecord as ms join main.titleinfo as mt WHERE student_ID=? and ms.title_ID=mt.title_ID",
            (stu_id,))
        rows = cur.fetchall()
        if not rows:
            return jsonify({
                "msg": "学号无效",
                "code": 0,
            })
        data = [{
            'status': row[0],
            'score': row[1],
            'knowledge': row[2],
        } for row in rows]
        return jsonify({
            "msg": "数据返回成功",
            "code": 1,
            "data": data
        })
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        conn.close()


# 知识掌握程度折线图接口
@app.route('/getKnowledgeMastery', methods=['GET'])
def getKnowledgeMastery():
    conn = get_db()
    stu_id = request.args.get('stu_id')
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT ms.score, ms.memory, ms.timeconsume,mt.knowledge FROM main.submitrecord as ms join main.titleinfo as mt WHERE student_ID=? and ms.title_ID=mt.title_ID",
            (stu_id,))
        rows = cur.fetchall()
        if not rows:
            return jsonify({
                "msg": "学号无效",
                "code": 0,
            })
        xAxis = {"r8S3g": 0, "t5V9e": 0, "m3D1v": 0, "s8Y2f": 0, "k4W1c": 0, "g7R2j": 0, "b3C9s": 0, "y9W5d": 0}
        datda = {"r8S3g": [], "t5V9e": [], "m3D1v": [], "s8Y2f": [], "k4W1c": [], "g7R2j": [], "b3C9s": [], "y9W5d": []}
        for row in rows:
            xAxis[row[3]] += 1
            if row[2] == '-' or row[2] == '--':
                datda[row[3]].append([int(row[0]), int(row[1]) + 0])
            else:
                datda[row[3]].append([int(row[0]), int(row[1]) + int(row[2])])
        for key in datda:
            accumulate_score = 0
            accumulate_index = 0
            data = []
            for value in datda[key]:
                accumulate_score += value[0]
                accumulate_index += value[1]
                if accumulate_score == 0:
                    data.append(0)
                else:
                    data.append(accumulate_index / accumulate_score)
            min_value = min(data)
            max_value = max(data)
            datda[key] = [(value - min_value) / (max_value - min_value) for value in data]
        return jsonify({
            "msg": "数据返回成功",
            "code": 1,
            "data": {
                "xAxis": list(xAxis.values()),
                "datda": list(datda.values())
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        conn.close()


@app.route('/getStudyModeScatter', methods=['GET'])
def getStudyModeScatter():
    result = {
        'scatter': [],
        'detail':[]
    }
    data = pd.read_csv('result.csv')
    data['position'] = data['position'].apply(insert_comma)
    result['scatter'] = eval(data[['id', 'position', 'label']].to_json(orient='records', force_ascii=False))
    for cluster in range(2 + 1):
        # print(data[data['label'] == cluster]['id'].tolist())
        result['detail'].append({
            'detail': calClusterMastery(data[data['label'] == cluster]['id'].tolist()),
            'index': cluster
        })
    return result


# 学习模式接口
@app.route('/getStudyMode', methods=['GET'])
def getStudyMode():
    conn = get_db()
    stu_id = request.args.get('student_ID')
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT ms.state, ms.score, mt.knowledge FROM main.submitrecord as ms join main.titleinfo as mt WHERE student_ID=? and ms.title_ID=mt.title_ID",
            (stu_id,))
        rows = cur.fetchall()
        if not rows:
            return jsonify({
                "msg": "学号无效",
                "code": 0,
            })
        data = []
        return jsonify({
            "msg": "数据返回成功",
            "code": 1,
            "data": data
        })
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        conn.close()


# 每个题目下获取学生信息接口
@app.route('/getTitleStudentInfo', methods=['GET'])
def getTitleStudentInfo():
    conn = get_db()
    title_ID = request.args.get('title_ID')
    try:
        cur = conn.cursor()
        cur.execute(
            "select sm.student_ID,sm.score,sm.s,ti.sub_knowledge from submitrecord3 as sm join titleinfo as ti WHERE sm.title_ID=? and sm.title_ID=ti.title_ID",
            (title_ID,))
        rows = cur.fetchall()
        if not rows:
            return jsonify({
                "msg": "题目ID无效",
                "code": 0,
            })
        data = [{
            "ID": row[0],
            "score": row[1],
            "knowledge": [
                {
                    "name": row[3],
                    "value": row[2],
                }
            ],
        } for row in rows]
        return jsonify({
            "msg": "数据返回成功",
            "code": 1,
            "data": data
        })
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        conn.close()


# 学生信息接口
@app.route('/getStudentInfo', methods=['GET'])
def getStudentInfo():
    conn = get_db()
    stu_id = request.args.get('student_ID')
    try:
        cur = conn.cursor()
        cur.execute(
            "select si.student_ID,si.sex,si.age,si.major,sr3.time,sr3.state,sr3.method,ti.knowledge from submitrecord3 as sr3 join titleinfo as ti join studentinfo as si WHERE sr3.title_ID=ti.title_ID and sr3.student_ID=si.student_ID")
        rows = cur.fetchall()
        students_data = {}

        # 处理每一行数据
        for row in rows:
            student_ID, sex, age, major, time, state, method, knowledge = row
            hour = (int(time / 86400) % 24) + 1

            # 如果学生ID不在字典中，初始化学生数据
            if student_ID not in students_data:
                students_data[student_ID] = {
                    "ID": student_ID,
                    "sex": sex,
                    "age": age,
                    "major": major,
                    "HotTime": {i: 0 for i in range(1, 25)},  # 初始化24小时的记录数
                    "Knowledge": {},
                    "badknowledge": {},
                    "method": {},
                    "most_used_method": {"name": "", "value": 0}
                }

            # 统计每个小时的记录数
            students_data[student_ID]["HotTime"][hour] += 1
            if knowledge not in students_data[student_ID]["Knowledge"]:
                students_data[student_ID]["Knowledge"][knowledge] = 0
                students_data[student_ID]["badknowledge"][knowledge] = 0
            students_data[student_ID]["Knowledge"][knowledge] += 1
            if state == "Absolutely_Correct":
                students_data[student_ID]["badknowledge"][knowledge] += 1

            # 统计最常用的方法
            if method in students_data[student_ID]["method"]:
                students_data[student_ID]["method"][method] += 1
                # 更新最常用的方法
                if students_data[student_ID]["method"][method] > students_data[student_ID]["most_used_method"]["value"]:
                    students_data[student_ID]["most_used_method"]["name"] = method
                    students_data[student_ID]["most_used_method"]["value"] = students_data[student_ID]["method"][method]
            else:
                students_data[student_ID]["method"][method] = 1

        # 计算知识点正确率
        for student in students_data.values():
            for knowledge, times in student["Knowledge"].items():
                student["Knowledge"][knowledge] = student["badknowledge"][knowledge] / times
            sorted_knowledge = sorted(student["Knowledge"].items(), key=lambda x: x[1], reverse=True)
            student["Knowledge"] = [{"name": key, "value": val} for key, val in sorted_knowledge[:3]]
            student["badknowledge"] = [{"name": key, "value": val} for key, val in sorted_knowledge[-3:]]

        # 移除中间变量，准备最终JSON结构
        for student in students_data.values():
            student["method"] = student.pop("most_used_method")
            student["HotTime"] = [{"time": key, "value": value} for key, value in
                                  student["HotTime"].items()]

        return jsonify({
            "msg": "数据返回成功",
            "code": 1,
            "data": list(students_data.values())
        })
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(debug=True)
    # getStudyModeScatter()
