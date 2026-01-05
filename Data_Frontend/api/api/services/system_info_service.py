from api.database import db_connection

def getSysInfoService():
    with db_connection() as cursor:
        cursor.execute("SELECT * from system_info limit 1")
        data = cursor.fetchone()
        result = None
        if data is None:
            return result
        result = {
            "id": data[0],
            "start_time": data[1].strftime("%Y-%m-%d"),
            "monitored_total": data[2],
            "excluded_count": data[3]
        }
    return result