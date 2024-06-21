import os
import sqlite3
import time

import pandas as pd
from flask import jsonify


# 指定目录路径
# folder_path = r'D:\Code\Server\eduvis-backend\data\Data_SubmitRecord'
#
# # 获取目录下所有 CSV 文件
# files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
#
# # 读取每个文件并合并数据
# dfs = []
# for file in files:
#     df = pd.read_csv(os.path.join(folder_path, file))
#     dfs.append(df)
#
# # 合并所有数据
# combined_data = pd.concat(dfs, ignore_index=True)
#
# conn = sqlite3.connect('eduvis.sqlite')
# cur = conn.cursor()
#
# for index, row in combined_data[['index', 'class', 'title_ID', 'student_ID', 'score']].iterrows():
#     cur.execute(
#         "update submitrecord set score = ? where 'index' = ? and 'title_ID' = ? and 'student_ID' = ?",
#         (row['score'], row['index'], row['title_ID'], row['student_ID']))
#     print(cur.fetchone())
#
# cur.close()
# conn.close()

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

    # for index, item in enumerate(data):
    #     accumulate_index
    # print(cur.fetchall())


def calKnowledgeMastery(id_list):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT ms.score, ms.memory, ms.timeconsume,mt.knowledge FROM main.submitrecord as ms join main.titleinfo as mt WHERE student_ID=? and ms.title_ID=mt.title_ID",
        (id,))
    rows = cur.fetchall()
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


calClusterMastery(['8b6d1125760bd3939b6e', '5d89810b20079366fcc2', '47eeab842793b09300c3'])
