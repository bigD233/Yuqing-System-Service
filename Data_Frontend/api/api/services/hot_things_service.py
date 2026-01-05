from api.database import db_connection
import base64


# 获取热点事件
def getHotThingsService():
    with db_connection() as cursor:
        cursor.execute("SELECT id, title, url, source, date, heat from hot_things order by id desc limit 4 ")
        data = cursor.fetchall()
        result = []
        if data is None:
            return result
        for row in data:
            item = {
                "id": row[0],
                "title": row[1],
                "url": row[2],
                "source": row[3],
                "datatime": row[4].strftime("%Y-%m-%d %H:%M:%S"),
                "heat": float(row[5])  # 确保heat是浮点数
            }
            result.append(item)
    return result


def getLvByIdService(id):
    with db_connection() as cursor:
        cursor.execute("SELECT warning_lv from hot_things where id = %s", (id,))
        data = cursor.fetchone()
        result = None
        if not data[0]:
            return result
        result = {
            "warning_lv": data[0]
        }
    return result


def getEmotionsByIdService(id):
    with db_connection() as cursor:
        cursor.execute("SELECT * from users_emotion where things_id = %s", (id,))
        data = cursor.fetchone()
        result = None
        if not data[0]:
            return result
        result = {
            "emotionData":
                {
                    "positive": data[1],
                    "negative": data[2],
                }
            ,
            "multiEmotionData":
                {
                    "like": data[3],
                    "happiness": data[4],
                    "sadness": data[5],
                    "anger": data[6],
                    "disgust": data[7],
                    "fear": data[8],
                    "surprise": data[9]
                }

        }
    return result


def searchByKeywordService(keyword):
    with db_connection() as cursor:
        cursor.execute("SELECT id,title,source,date,heat FROM hot_things WHERE title LIKE %s order by id desc limit 5",
                       (f"%{keyword}%",))
        data = cursor.fetchall()
        result = []
        if not data:
            return result
        for row in data:
            item = {
                "id": row[0],
                "title": row[1],
                "source": row[2],
                "datatime": row[3].strftime("%Y-%m-%d %H:%M:%S"),
                "heat": float(row[4])  # 确保heat是浮点数
            }
            result.append(item)
    return result


def getMapDataByIdService(id):
    with db_connection() as cursor:
        cursor.execute(
            "SELECT p.name AS province_name, tp.color FROM provinces p JOIN thing_provinces tp ON p.pid = tp.province_pid WHERE tp.thing_id = %s",
            (id,))
        data = cursor.fetchall()
        result = []
        if not data:
            return result
        for row in data:
            item = {
                "name": row[0],
                "itemStyle": {"areaColor": row[1]}
            }
            result.append(item)
    return result


def getWordCloudByIdService(id):
    with db_connection() as cursor:
        cursor.execute("SELECT img from word_cloud where thing_id = %s", (id,))
        data = cursor.fetchone()

        if not data or not data[0]:
            return None
        # Encode the binary data as base64 string
        result = {
            "img": data[0].decode('utf-8')
        }
    return result


def getPlatformMetricsByIdService(id):
    with db_connection() as cursor:
        cursor.execute(
            "SELECT total_posts, ​​total_users, total_interactions,posts_with_location from hot_things where id = %s",
            (id,))
        data = cursor.fetchone()
        result = None
        if not data[0]:
            return result
        result = {
            "total_posts": data[0],
            "total_users": data[1],
            "total_interactions": data[2],
            "posts_with_location": data[3]
        }
    return result


def getTrendDataByIdService(id):
    with db_connection() as cursor:
        cursor.execute("SELECT sort,value from trend where thing_id = %s order by sort", (id,))
        data = cursor.fetchall()
        result = None
        if not data:
            return result
        data_dict = {sort: value for sort, value in data}
        result = []
        for i in range(7):
            result.append(data_dict.get(i, 0))
    return result


def getTypicalPostsByIdService(id):
    with db_connection() as cursor:
        cursor.execute(
            "SELECT id, title, url, source, datetime, heat from typical_posts where thing_id = %s order by id desc limit 10 ",
            (id,))
        data = cursor.fetchall()
        result = []
        if data is None:
            return result
        for row in data:
            item = {
                "id": row[0],
                "title": row[1],
                "url": row[2],
                "source": row[3],
                "datatime": row[4].strftime("%Y-%m-%d %H:%M:%S"),
                "heat": float(row[5])  # 确保heat是浮点数
            }
            result.append(item)
    return result


def getHeatDataByIdService(id):
    with db_connection() as cursor:
        cursor.execute(
            "SELECT forward_count,comment_count, like_count,composite_hot_score,base_hot_value, media_hot_value,interaction_hot_value  from heat where thing_id = %s",
            (id,))
        data = cursor.fetchone()
        result = None
        if not data:
            return result
        result = {
            "forward_count": data[0],
            "comment_count": data[1],
            "like_count": data[2],
            "composite_hot_score": data[3],
            "base_hot_value": data[4],
            "media_hot_value": data[5],
            "interaction_hot_value": data[6]
        }
    return result


def getTypicalRadarDataByIdService(id):
    with db_connection() as cursor:
        cursor.execute(
            "SELECT p.title , r.autonomy,r.stimulus,r.fraternity,r.friendliness,r.compliance,r.tradition,r.security,r.authority,r.achievement,r.hedonism,p.id FROM typical_posts p JOIN typical_radar r ON p.id = r.typical_id WHERE p.thing_id = %s order by p.id desc limit 3",
            (id,))
        data = cursor.fetchall()
        result = {
            "titles": [],
            "values": []
        }
        if not data:
            return result

        for row in data:
            result["titles"].append(row[0])
            result["values"].append([
                row[1],  # autonomy
                row[2],  # stimulus
                row[3],  # fraternity
                row[4],  # friendliness
                row[5],  # compliance
                row[6],  # tradition
                row[7],  # security
                row[8],  # authority
                row[9],  # achievement
                row[10]  # hedonism
            ])
    return result


def getPopulationCompositonByIdService(id):
    with db_connection() as cursor:
        cursor.execute(
            "SELECT id,name,value  from population_composition where thing_id = %s",
            (id,))
        data = cursor.fetchall()
        result = []
        if not data:
            return None
        for row in data:
            item = {
                "id": row[0],
                "name": row[1],
                "value": row[2]
            }
            result.append(item)
    return result


def getPopulationDataByPopIdService(id):
    with db_connection() as cursor:
        cursor.execute(
            "SELECT label,value  from population_values where population_id = %s",
            (id,))
        data = cursor.fetchall()
        result = []
        if not data:
            return None
        for row in data:
            item = {
                "name": row[0],
                "value": row[1]
            }
            result.append(item)
    return result


def addHotThingService(data):
    try:
        with db_connection() as cursor:
            # 开始事务
            cursor.execute("START TRANSACTION")

            # 1. 插入hot_things表
            cursor.execute(
                """
                INSERT INTO hot_things (title, url, source, date, heat, warning_lv, total_posts, ​​total_users,
                                        total_interactions, posts_with_location)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    data["hot_thing"]["title"],
                    data["hot_thing"]["url"],
                    data["hot_thing"]["source"],
                    data["hot_thing"]["date"],
                    data["hot_thing"]["heat"],
                    data["hot_thing"]["warning_lv"],
                    data["hot_thing"]["total_posts"],
                    data["hot_thing"]["total_users"],
                    data["hot_thing"]["total_interactions"],
                    data["hot_thing"]["posts_with_location"]
                )
            )
            thing_id = cursor.lastrowid

            # 2. 插入users_emotion表
            cursor.execute(
                """
                INSERT INTO users_emotion (things_id, positive, negative, `like`, happiness, sadness, anger, disgust,
                                           fear, surprise)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    thing_id,
                    data["user_emotion"]["positive"],
                    data["user_emotion"]["negative"],
                    data["user_emotion"]["like"],
                    data["user_emotion"]["happiness"],
                    data["user_emotion"]["sadness"],
                    data["user_emotion"]["anger"],
                    data["user_emotion"]["disgust"],
                    data["user_emotion"]["fear"],
                    data["user_emotion"]["surprise"]
                )
            )

            # 3. 插入heat表
            cursor.execute(
                """
                INSERT INTO heat (thing_id, forward_count, comment_count, like_count, composite_hot_score,
                                  base_hot_value, media_hot_value, interaction_hot_value)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    thing_id,
                    data["heat"]["forward_count"],
                    data["heat"]["comment_count"],
                    data["heat"]["like_count"],
                    data["heat"]["composite_hot_score"],
                    data["heat"]["base_hot_value"],
                    data["heat"]["media_hot_value"],
                    data["heat"]["interaction_hot_value"]
                )
            )

            # 4. 插入trend表
            for sort, value in enumerate(data["trend"]):
                cursor.execute(
                    "INSERT INTO trend (thing_id, sort, value) VALUES (%s, %s, %s)",
                    (thing_id, sort + 1, value)
                )

            # 5. 插入typical_posts表
            for post in data["typical_posts"]:
                cursor.execute(
                    """
                    INSERT INTO typical_posts (thing_id, title, url, source, datetime, heat)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        thing_id,
                        post["title"],
                        post["url"],
                        post["source"],
                        post["datetime"],
                        post["heat"]
                    )
                )
                post_id = cursor.lastrowid

                # 插入typical_radar表
                cursor.execute(
                    """
                    INSERT INTO typical_radar (typical_id, autonomy, stimulus, fraternity, friendliness, compliance,
                                               tradition, security, authority, achievement, hedonism)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        post_id,
                        post["autonomy"],
                        post["stimulus"],
                        post["fraternity"],
                        post["friendliness"],
                        post["compliance"],
                        post["tradition"],
                        post["security"],
                        post["authority"],
                        post["achievement"],
                        post["hedonism"]
                    )
                )

            # 6. 插入population_composition表
            for comp in data["population_composition"]:
                cursor.execute(
                    "INSERT INTO population_composition (thing_id, name, value) VALUES (%s, %s, %s)",
                    (thing_id, comp["name"], comp["value"])
                )
                pop_id = cursor.lastrowid

                # 插入population_values表
                for value in comp["population_values"]:
                    cursor.execute(
                        "INSERT INTO population_values (population_id, label, value) VALUES (%s, %s, %s)",
                        (pop_id, value["label"], value["value"])
                    )

            # 7. 插入thing_provinces表
            for province in data["map"]:
                cursor.execute(
                    "INSERT INTO thing_provinces (thing_id, province_pid, color) VALUES (%s, %s, %s)",
                    (thing_id, province["province_pid"], province["color"])
                )

            # 8. 插入word_cloud表
            if "word_cloud" in data and data["word_cloud"]:
                cursor.execute(
                    "INSERT INTO word_cloud (thing_id, img) VALUES (%s, %s)",
                    (thing_id, data["word_cloud"])
                )

            # 提交事务
            cursor.execute("COMMIT")

            return {"success": True, "thing_id": thing_id}

    except Exception as e:
        # 发生错误时返回错误信息
        # 不需要显式回滚，因为with语句会在退出时自动处理
        return {"success": False, "error": str(e)}


def deleteHotThingService(id):
    try:
        with db_connection() as cursor:
            cursor.execute("START TRANSACTION")  # 开始事务
            
            # 按依赖顺序删除从表记录：从叶子表开始，避免外键冲突
            cursor.execute("DELETE FROM word_cloud WHERE thing_id = %s", (id,))
            cursor.execute("DELETE FROM thing_provinces WHERE thing_id = %s", (id,))
            # 使用子查询删除population_values，因为它依赖population_composition
            cursor.execute("DELETE FROM population_values WHERE population_id IN (SELECT id FROM population_composition WHERE thing_id = %s)", (id,))
            cursor.execute("DELETE FROM population_composition WHERE thing_id = %s", (id,))
            cursor.execute("DELETE FROM typical_radar WHERE typical_id IN (SELECT id FROM typical_posts WHERE thing_id = %s)", (id,))
            cursor.execute("DELETE FROM typical_posts WHERE thing_id = %s", (id,))
            cursor.execute("DELETE FROM trend WHERE thing_id = %s", (id,))
            cursor.execute("DELETE FROM heat WHERE thing_id = %s", (id,))
            cursor.execute("DELETE FROM users_emotion WHERE things_id = %s", (id,))
            # 最后删除主表记录
            cursor.execute("DELETE FROM hot_things WHERE id = %s", (id,))
            
            cursor.execute("COMMIT")  # 提交事务
            return {"success": True, "message": "热点事件删除成功"}
    except Exception as e:
        # 错误时回滚事务（db_connection上下文管理器可能自动处理，但显式回滚更安全）
        cursor.execute("ROLLBACK")
        return {"success": False, "error": str(e)}
    
def clearAllTablesService():
    """
    清空数据库中所有表的数据，但保留provinces和system_info表
    这是一个危险操作，务必谨慎使用！
    """
    try:
        with db_connection() as cursor:
            # 开始事务
            cursor.execute("START TRANSACTION")
            
            # 禁用外键检查，避免因外键约束导致清空失败
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            # 获取所有表名，但排除provinces和system_info表
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_TYPE = 'BASE TABLE'
                AND TABLE_NAME NOT IN ('provinces', 'system_info')
            """)
            tables = cursor.fetchall()
            
            # 清空每个表（除了排除的表）
            cleared_tables = []
            for table in tables:
                table_name = table[0]
                try:
                    # 使用TRUNCATE快速清空表数据
                    cursor.execute(f"TRUNCATE TABLE `{table_name}`")
                    cleared_tables.append(table_name)
                    print(f"已清空表: {table_name}")
                except Exception as e:
                    # 如果TRUNCATE失败，尝试使用DELETE
                    try:
                        cursor.execute(f"DELETE FROM `{table_name}`")
                        cleared_tables.append(table_name)
                        print(f"使用DELETE清空表: {table_name}")
                    except Exception as delete_error:
                        print(f"清空表 {table_name} 失败: {str(delete_error)}")
                        # 继续处理其他表
            
            # 重新启用外键检查
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            
            # 提交事务
            cursor.execute("COMMIT")
            
            return {
                "success": True, 
                "message": f"成功清空 {len(cleared_tables)} 个表的数据，保留了provinces和system_info表",
                "cleared_tables": cleared_tables,
                "preserved_tables": ["provinces", "system_info"],
                "tables_cleared_count": len(cleared_tables)
            }
            
    except Exception as e:
        # 发生错误时回滚事务
        try:
            cursor.execute("ROLLBACK")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")  # 确保重新启用外键检查
        except:
            pass
        
        return {
            "success": False, 
            "error": f"清空表数据时发生错误: {str(e)}"
        }