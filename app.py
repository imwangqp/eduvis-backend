import sqlite3

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
            "SELECT ms.state, ms.score, mt.knowledge FROM main.submitrecord2 as ms join main.titleinfo as mt WHERE student_ID=? and ms.title_ID=mt.title_ID",
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
            "SELECT ms.score, ms.memory, ms.timeconsume,mt.knowledge FROM main.submitrecord2 as ms join main.titleinfo as mt WHERE student_ID=? and ms.title_ID=mt.title_ID",
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
        max_num = sum(list(xAxis.values()))
        for key in xAxis:
            xAxis[key] = [0 for i in range(max_num)]
        i = 0
        for row in rows:
            sub_knowledge = row[3]
            xAxis[sub_knowledge][i] = 1
            i = i + 1
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


# 每个题目下获取学生信息接口
@app.route('/getTitleStudentInfo', methods=['GET'])
def getTitleStudentInfo():
    conn = get_db()
    title_ID = request.args.get('title_ID')
    try:
        cur = conn.cursor()
        cur.execute(
            "select sm.student_ID,sm.score,sm.s,ti.sub_knowledge from submitRecord4UpdateS as sm join titleinfo as ti WHERE sm.title_ID=? and sm.title_ID=ti.title_ID",
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


# 一次性API
# 学生信息接口
@app.route('/getStudentInfo', methods=['GET'])
def getStudentInfo():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "select sr3.class,si.student_ID,si.sex,si.age,si.major,sr3.time,sr3.state,sr3.method,ti.knowledge from submitrecord3 as sr3 join titleinfo as ti join studentinfo as si WHERE sr3.title_ID=ti.title_ID and sr3.student_ID=si.student_ID")
        rows = cur.fetchall()
        students_data = {}

        # 处理每一行数据
        for row in rows:
            student_class, student_ID, sex, age, major, time, state, method, knowledge = row
            hour = (int(time / 86400) % 24) + 1
            # 如果学生ID不在字典中，初始化学生数据
            if student_ID not in students_data:
                students_data[student_ID] = {
                    "class": student_class,
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


# 一次性API
# 每个题目下三类同学（error、partly correct、correct）的平均子知识点（该题目对应）掌握程度
@app.route('/getTitleKnowledgeInfo', methods=['GET'])
def getTitleKnowledgeInfo():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "select sr4s.state,sr4s.student_ID,sr4s.s ,ti.title_ID,ti.sub_knowledge from submitRecord4UpdateS sr4s join titleinfo as ti where ti.title_ID=sr4s.title_ID")
        rows = cur.fetchall()
        # knowledges = {}  # 学生对与每个知识点的最新知识掌握程度
        # sub_knowledges = {}  # 学生对与每个知识点的最新知识掌握程度
        # titles = []
        # for row in rows:
        #     state, student, s, title, sub_knowledge = row
        #     if title not in titles:
        #         titles.append(title)
        #     if sub_knowledge not in sub_knowledges:
        #         sub_knowledges[sub_knowledge] = [0, 0]
        #     if student not in knowledges:
        #         knowledges[student] = {}
        #     if sub_knowledge not in knowledges[student]:
        #         knowledges[student][sub_knowledge] = s
        #     else:
        #         knowledges[student][sub_knowledge] = (knowledges[student][sub_knowledge] + s) / 2
        #
        # for student in knowledges:
        #     for sub_knowledge in knowledges[student]:
        #         sub_knowledges[sub_knowledge][0] += 1
        #         sub_knowledges[sub_knowledge][1] += knowledges[student][sub_knowledge]
        titles_data = {}
        for row in rows:
            state, student_ID, s, title_ID, sub_knowledge = row
            if state == "Absolutely_Correct":
                st = "correct"
            # elif state == "Partly_Correct":
            elif state == "Partially_Correct":
                st = "partly_correct"
            else:
                st = "error"
            if title_ID not in titles_data:
                titles_data[title_ID] = {
                    "id": title_ID,
                    "value": [],
                    "knowledge": {},
                    "Knowledge": []
                }
            if sub_knowledge not in titles_data[title_ID]["knowledge"]:
                titles_data[title_ID]["knowledge"][sub_knowledge] = {
                    "error": [0, 0],
                    "partly_correct": [0, 0],
                    "correct": [0, 0],
                    "name": sub_knowledge,
                }
            titles_data[title_ID]["knowledge"][sub_knowledge][st][0] += 1
            titles_data[title_ID]["knowledge"][sub_knowledge][st][1] += s
        for title in titles_data.values():  # 遍历值
            for sub_knowledge in title["knowledge"]:
                title["Knowledge"].append(title["knowledge"][sub_knowledge]["name"])
                if title["knowledge"][sub_knowledge]["error"][0] == 0:
                    e = 0
                else:
                    e = title["knowledge"][sub_knowledge]["error"][1] / title["knowledge"][sub_knowledge]["error"][0]
                if title["knowledge"][sub_knowledge]["partly_correct"][0] == 0:
                    p = 0
                else:
                    p = title["knowledge"][sub_knowledge]["partly_correct"][1] / title["knowledge"][sub_knowledge][
                        "partly_correct"][0]
                if title["knowledge"][sub_knowledge]["correct"][0] == 0:
                    c = 0
                else:
                    c = title["knowledge"][sub_knowledge]["correct"][1] / title["knowledge"][sub_knowledge]["correct"][
                        0]
                # mmax = max(e, p, c)
                # mmin = min(e, p, c)
                # e = (e - mmin) / (mmax - mmin)
                # p = (p - mmin) / (mmax - mmin)
                # c = (c - mmin) / (mmax - mmin)
                title["value"].append([e, p, c])
        return jsonify(list(titles_data.values()))
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(debug=True)
