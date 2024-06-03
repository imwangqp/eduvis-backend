import sqlite3

from flask import *

# from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)


# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eduvis.sqlite'
# db = SQLAlchemy(app)

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


@app.route('/getAnswerLog', methods=['GET'])
def getAnswerLog():
    conn = get_db()
    stu_id = request.args.get('stu_id')
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM main.submitrecord WHERE student_ID=?", (stu_id,))
        rows = cur.fetchall()
        if not rows:
            return jsonify({
                "msg": "学号无效",
                "code": 0,
            })
        data = [{
            'index': row[0],
            'class': row[1],
            'time': row[2],
            'state': row[3],
            'title_ID': row[4],
            'method': row[5],
            'memory': row[6],
            'timeconsume': row[7],
        } for row in rows]
        return jsonify({
            "msg": "答题日志返回成功",
            "code": 1,
            "data": data
        })
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(debug=True)
