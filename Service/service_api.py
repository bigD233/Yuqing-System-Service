from flask import Flask, request, jsonify
import os
import requests
import json

app = Flask(__name__)

# 单一服务端地址（可用环境变量覆盖）
SERVICE_URL_EMOTION = os.getenv("SERVICE_URL_EMOTION", "http://localhost:8001/emotion")
SERVICE_URL_YUQING = os.getenv("SERVICE_URL_YUQING", "http://localhost:8001/yuqing")
SERVICE_URL_HOT = os.getenv("SERVICE_URL_HOT", "http://localhost:8002/hot")
SERVICE_URL_CLUSTER = os.getenv("SERVICE_URL_CLUSTER", "http://localhost:8002/cluster")
SERVICE_URL_VALUE = os.getenv("SERVICE_URL_VALUE", "http://localhost:8003/value")
SERVICE_URL_BASEINFO = os.getenv("SERVICE_URL_BASEINFO", "http://localhost:8003/baseinfo")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "600"))


def call_service(url, payload):
    try:
        resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        try:
            data = resp.json()
        except ValueError:
            data = {"raw": resp.text}
        return {
            "ok": resp.ok,
            "status_code": resp.status_code,
            "data": data,
        }
    except requests.Timeout:
        return {
            "ok": False,
            "status_code": 504,
            "error": f"timeout after {REQUEST_TIMEOUT_SECONDS}s",
        }
    except requests.RequestException as exc:
        return {
            "ok": False,
            "status_code": 502,
            "error": str(exc),
        }


def call_service_emotion(payload):
    return call_service(SERVICE_URL_EMOTION, payload)


def call_service_yuqing(payload):
    return call_service(SERVICE_URL_YUQING, payload)


def call_service_cluster(payload):
    return call_service(SERVICE_URL_CLUSTER, payload)


def call_service_hot(payload):
    return call_service(SERVICE_URL_HOT, payload)


def call_service_value(payload):
    return call_service(SERVICE_URL_VALUE, payload)


def call_service_baseinfo(payload):
    return call_service(SERVICE_URL_BASEINFO, payload)


def Results_Service_CLUSTER(data_source_path, use_saved=False, method="traditional", min_posts=1, source_site="新浪微博", use_prior=True, max_samples_per_event=1000, min_samples_per_event=1):
    payload = {
        "data_source_path": data_source_path,
        "use_saved": use_saved,
        "method": method,
        "min_posts": min_posts,
        "source_site": source_site,
        "use_prior": use_prior,
        "max_samples_per_event": max_samples_per_event,
        "min_samples_per_event": min_samples_per_event,
    }
    required_fields = ["data_source_path"]
    missing = [k for k in required_fields if not payload.get(k)]
    if missing:
        return {
            "ok": False,
            "error": f"CLUSTER missing required fields: {', '.join(missing)}",
            "required": required_fields,
        }
    return call_service_cluster(payload)

def Results_Service(service_key, event_name, csv_file_path, image_dir_path):
    payload = {
        "event_name": event_name,
        "csv_file_path": csv_file_path,
        "image_dir_path": image_dir_path,
    }
    required_fields = ["event_name", "csv_file_path", "image_dir_path"]
    missing = [k for k in required_fields if not payload.get(k)]

    service_map = {
        # 保持原本的报错文案（即使某些文案看起来不太一致）
        "emotion": {
            "caller": call_service_emotion,
            "error_prefix": "Emotion Service",
            "error_as_jsonify": True,
        },
        "yuqing": {
            "caller": call_service_yuqing,
            "error_prefix": "Yuqing Service",
            "error_as_jsonify": True,
        },
        "hot": {
            "caller": call_service_hot,
            "error_prefix": "Hot Service",
            "error_as_jsonify": True,
        },
        "value": {
            "caller": call_service_value,
            "error_prefix": "Value Service",
            "error_as_jsonify": False,
        },
        "baseinfo": {
            "caller": call_service_baseinfo,
            "error_prefix": "Baseinfo Service",
            "error_as_jsonify": True,
        },
    }

    if service_key not in service_map:
        raise ValueError(f"unknown service_key: {service_key}")

    cfg = service_map[service_key]
    if missing:
        if cfg["error_as_jsonify"]:
            return jsonify({
                "error": f"{cfg['error_prefix']} missing required fields: {', '.join(missing)}",
                "required": required_fields,
            }), 400
        return {
            "ok": False,
            "error": f"{cfg['error_prefix']} missing required fields: {', '.join(missing)}",
            "required": required_fields,
        }

    return cfg["caller"](payload)


# 省份ID映射表
PROVINCE_MAP = {
    "北京": "110000", "天津": "120000", "河北": "130000", "山西": "140000",
    "内蒙古": "150000", "辽宁": "210000", "吉林": "220000", "黑龙江": "230000",
    "上海": "310000", "江苏": "320000", "浙江": "330000", "安徽": "340000",
    "福建": "350000", "江西": "360000", "山东": "370000", "河南": "410000",
    "湖北": "420000", "湖南": "430000", "广东": "440000", "广西": "450000",
    "海南": "460000", "重庆": "500000", "四川": "510000", "贵州": "520000",
    "云南": "530000", "西藏": "540000", "陕西": "610000", "甘肃": "620000",
    "青海": "630000", "宁夏": "640000", "新疆": "650000", "台湾": "710000",
    "香港": "810000", "澳门": "820000"
}

# 根据比例生成颜色（比例越高颜色越深）
def get_color_by_ratio(ratio):
    if ratio <= 0:
        return "#E0E0E0"  # 无数据灰色
    elif ratio < 0.05:
        return "#BBDEFB"
    elif ratio < 0.1:
        return "#64B5F6"
    elif ratio < 0.15:
        return "#2196F3"
    elif ratio < 0.2:
        return "#1976D2"
    else:
        return "#0D47A1"

def extract_and_format_results(result_emo, result_yuqing, result_hot, result_value, result_baseinfo):
    """
    将各服务返回的原始结果整理成统一格式
    """
    try:
        # 安全获取嵌套字典值的辅助函数
        def safe_get(d, *keys, default=None):
            for key in keys:
                if isinstance(d, dict):
                    d = d.get(key, default)
                elif isinstance(d, list) and isinstance(key, int) and len(d) > key:
                    d = d[key]
                else:
                    return default
            return d if d is not None else default

        # 提取各服务数据
        emo_data = safe_get(result_emo, "data", default={})
        emo_outputs = safe_get(emo_data, "outputs", default={})
        yuqing_outputs = safe_get(result_yuqing, "data", "outputs", default={})
        hot_data = safe_get(result_hot, "data", default={})
        hot_outputs = safe_get(hot_data, "outputs", default={})
        baseinfo_outputs = safe_get(result_baseinfo, "data", "outputs", default={})

        # 提取value数据 - 结构为 [file_path, {event_name: {...}}]
        value_outputs = safe_get(result_value, "data", "outputs", default=[])
        value_event_data = {}
        if len(value_outputs) >= 2 and isinstance(value_outputs[1], dict):
            # 获取第一个key对应的值
            for key in value_outputs[1]:
                value_event_data = value_outputs[1][key]
                break

        # 获取typical_posts列表（嵌套在列表中）
        typical_posts_raw = safe_get(value_event_data, "typical_posts", 0, default=[])
        if not isinstance(typical_posts_raw, list):
            typical_posts_raw = []

        # 找到最早的帖子
        earliest_post = None
        if typical_posts_raw:
            earliest_post = min(typical_posts_raw, key=lambda x: x.get("datetime", "9999-99-99"))

        # 预警等级映射
        warning_map = {"严重": "Ⅰ", "中等": "Ⅱ", "轻微": "Ⅲ"}
        predicted_label = safe_get(yuqing_outputs, "predicted_label", default="轻微")
        warning_lv = warning_map.get(predicted_label, "Ⅲ")

        # 热度分数 - 使用 raw_score
        hot_score = safe_get(hot_outputs, "hot_score", "raw_score", default=0)

        # 构建 hot_thing
        total_posts = safe_get(baseinfo_outputs, "总帖子数", default=0)
        location_ratio = safe_get(baseinfo_outputs, "有定位帖子占比", default=0)
        hot_thing = {
            "title": safe_get(emo_data, "event_name", default=""),
            "url": safe_get(earliest_post, "url", default="") if earliest_post else "",
            "source": safe_get(earliest_post, "source", default="") if earliest_post else "",
            "date": safe_get(earliest_post, "datetime", default="") if earliest_post else "",
            "heat": hot_score,
            "warning_lv": warning_lv,
            "total_posts": total_posts,
            "total_users": safe_get(baseinfo_outputs, "总用户数", default=0),
            "total_interactions": int(safe_get(baseinfo_outputs, "总互动数", default=0)),
            "posts_with_location": int(total_posts * location_ratio)
        }

        # 构建 user_emotion
        emotion_counts = safe_get(emo_outputs, "emotion_counts", default={})
        user_emotion = {
            "positive": safe_get(emo_outputs, "positive", "count", default=0),
            "negative": safe_get(emo_outputs, "negative", "count", default=0),
            "like": safe_get(emotion_counts, "like", default=0),
            "happiness": safe_get(emotion_counts, "happiness", default=0),
            "sadness": safe_get(emotion_counts, "sadness", default=0),
            "anger": safe_get(emotion_counts, "anger", default=0),
            "disgust": safe_get(emotion_counts, "disgust", default=0),
            "fear": safe_get(emotion_counts, "fear", default=0),
            "surprise": safe_get(emotion_counts, "surprise", default=0)
        }

        # 构建 heat
        event_stats = safe_get(hot_outputs, "event_statistics", default={})
        heat = {
            "forward_count": safe_get(event_stats, "total_posts", default=0),
            "comment_count": safe_get(event_stats, "total_comments", default=0),
            "like_count": safe_get(event_stats, "total_likes", default=0),
            "composite_hot_score": hot_score,
            "base_hot_value": hot_score,
            "media_hot_value": hot_score,
            "interaction_hot_value": hot_score
        }

        # 构建 trend - 近七天帖子数
        trend_data = safe_get(baseinfo_outputs, "近七天帖子数", default={})
        trend = [
            trend_data.get("第1天", 0),
            trend_data.get("第2天", 0),
            trend_data.get("第3天", 0),
            trend_data.get("第4天", 0),
            trend_data.get("第5天", 0),
            trend_data.get("第6天", 0),
            trend_data.get("第7天", 0)
        ]

        # 构建 typical_posts
        typical_posts = []
        for post in typical_posts_raw:
            typical_posts.append({
                "title": post.get("title", ""),
                "url": post.get("url", ""),
                "source": post.get("source", ""),
                "datetime": post.get("datetime", ""),
                "heat": post.get("heat", 0),
                "autonomy": post.get("autonomy", 0),
                "stimulus": post.get("stimulus", 0),
                "fraternity": post.get("fraternity", 0),
                "friendliness": post.get("friendliness", 0),
                "compliance": post.get("compliance", 0),
                "tradition": post.get("tradition", 0),
                "security": post.get("security", 0),
                "authority": post.get("authority", 0),
                "achievement": post.get("achievement", 0),
                "hedonism": post.get("hedonism", 0)
            })

        # 构建 population_composition
        population_raw = safe_get(value_event_data, "population_composition", default=[])
        population_composition = []
        for pop in population_raw:
            pop_values = []
            for pv in pop.get("population_values", []):
                pop_values.append({
                    "label": pv.get("name", ""),
                    "value": pv.get("value", 0)
                })
            population_composition.append({
                "name": pop.get("name", ""),
                "value": pop.get("value", 0),
                "population_values": pop_values
            })

        # 构建 map
        region_data = safe_get(baseinfo_outputs, "地域分布", default={})
        map_list = []
        for province_name, pid in PROVINCE_MAP.items():
            ratio = region_data.get(province_name, 0)
            map_list.append({
                "province_pid": pid,
                "province_name": province_name,
                "color": get_color_by_ratio(ratio)
            })

        # 获取词云
        word_cloud = safe_get(baseinfo_outputs, "词云编码", default="")

        # 组装最终结果
        formatted_result = {
            "hot_thing": hot_thing,
            "user_emotion": user_emotion,
            "heat": heat,
            "trend": trend,
            "typical_posts": typical_posts,
            "population_composition": population_composition,
            "map": map_list,
            "word_cloud": word_cloud
        }

        return formatted_result

    except Exception as e:
        print(f"Error extracting results: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}



def pre_service(payload):
    required_fields = ["data_source_path"]
    missing = [k for k in required_fields if not payload.get(k)]
    if missing:
        return jsonify({
            "error": f"missing required fields: {', '.join(missing)}",
            "required": required_fields,
        }), 400
    
    data_source_path = payload.get("data_source_path")
    use_saved = bool(payload.get("use_saved", False))
    method = payload.get("method", "traditional")
    min_posts = int(payload.get("min_posts", 1))
    source_site = payload.get("source_site")
    use_prior = bool(payload.get("use_prior", True))
    max_samples_per_event = int(payload.get("max_samples_per_event", 1000))
    min_samples_per_event = int(payload.get("min_samples_per_event", 1))

    print("------------调用聚类服务------------")
    result_cluster = Results_Service_CLUSTER(data_source_path, use_saved, method, min_posts, source_site, use_prior, max_samples_per_event, min_samples_per_event)
    print("------------聚类完成------------")
    # print(result_cluster)
    if result_cluster.get("data"):
        if result_cluster["data"]["outputs"].get("clusters"):
            return jsonify({"INFO": "聚类服务调用成功","Cluster_folder":data_source_path+"/cluster_events"}), 200
    return jsonify({"INFO": "聚类服务调用失败"}), 500

@app.route("/whole_service", methods=["POST"])  # 等价入口，方便语义清晰
def ALL_SERVICE():
    if not request.is_json:
        return jsonify({"error": "request body must be JSON"}), 400
    payload = request.get_json(silent=True) or {}

    # 先调用聚类算法
    cluster_result, state = pre_service(payload)

    # 如果聚类成功，开始获取事件级数据（剩余5个算法）
    if state == 200:
        print("---------开始获取事件级数据---------")
        
        folder = cluster_result.json["Cluster_folder"]
        dir_names = [name for name in os.listdir(folder) if os.path.isdir(os.path.join(folder, name))]
        
        for dir_name in dir_names:
            print(f"**********开始处理事件：{dir_name}*************")
            event_res,stat_code = aggregate(dir_name,folder)
            if stat_code != 200:
                print(f"**********事件：{dir_name} 处理失败*************")
                return jsonify({"INFO": "事件级数据处理失败"}), 500
            else:
                print(f"**********事件：{dir_name} 处理成功*************")
    
    return jsonify({"INFO": "所有事件及服务处理成功，数据已入库"}), 200
            



def aggregate(event_name,file_path):
    
    csv_file_path = file_path +"/"+ event_name + "/" + event_name + ".csv"
    image_dir_path = file_path + "/" +event_name + "/images"
    file_path = file_path + "/" + event_name

    all_right_flag = True

    # 调用服务
    


    print("***************************************")
    print("------------调用热度预测服务------------")
    result_hot = Results_Service("hot", event_name, csv_file_path, image_dir_path)
    print(result_hot)
    if result_hot["status_code"] != 200:
        print("--------------热度预测服务调用失败--------------")
        all_right_flag = False
    else:
        print("--------------热度预测服务调用成功--------------")


        
    print("------------调用情感预测服务------------")
    result_emo = Results_Service("emotion", event_name, csv_file_path, image_dir_path)
    if result_emo["status_code"] != 200:
        print("--------------情感预测服务调用失败--------------")
        all_right_flag = False
    else:
        print("--------------情感预测服务调用成功--------------")
    


    print("***************************************")
    print("------------调用舆情预测服务------------")
    result_yuqing = Results_Service("yuqing", event_name, csv_file_path, image_dir_path)
    if result_yuqing["status_code"] != 200:
        print("--------------舆情预测服务调用失败--------------")
        all_right_flag = False
    else:
        print("--------------舆情预测服务调用成功--------------")




    print("***************************************")
    print("------------调用价值观预测服务------------")
    result_value = Results_Service("value", event_name, file_path, image_dir_path)
    if result_value["status_code"] != 200:
        print("--------------价值观预测服务调用失败--------------")
        all_right_flag = False
    else:
        print("--------------价值观预测服务调用成功--------------")



    print("***************************************")
    print("------------调用基础信息服务------------")
    result_baseinfo = Results_Service("baseinfo", event_name, csv_file_path, image_dir_path)
    if result_baseinfo["status_code"] != 200:
        print("--------------基础信息服务调用失败--------------")
        all_right_flag = False
    else:
        print("--------------基础信息服务调用成功--------------")
    print("***************************************")

    if all_right_flag == False:
        print("-----------事件级数据处理失败-----------")
        return jsonify({"INFO": "事件级数据处理失败"}), 500
    else:
        print("-----------事件级数据处理成功-----------")
    # 保存结果到本地json文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    

    # 整理并提取结果
    formatted_result = extract_and_format_results(
        result_emo, result_yuqing, result_hot, result_value, result_baseinfo
    )

    # 保存整理后的结果
    try:
        formatted_save_path = os.path.join(current_dir, "formatted_results.json")
        with open(formatted_save_path, "w", encoding="utf-8") as f:
            json.dump(formatted_result, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving formatted results: {e}")

    # 自动POST结果到本地端口8000/addHotThing
    
    try:
        add_hot_thing_url = "http://localhost:5000/api/addHotThing"
        post_response = requests.post(
            add_hot_thing_url, 
            json=formatted_result, 
            timeout=30
        )
        print(f"POST to {add_hot_thing_url} - Status: {post_response.status_code}")
        if not post_response.ok:
            print(f"Warning: POST to addHotThing failed with status {post_response.status_code}")
            print(f"Response: {post_response.text}")
        else:
            print("-----------事件级数据加入数据库成功----------------")
    except requests.RequestException as e:
        print(f"Error posting to addHotThing: {e}")
        # 继续执行，不影响主流程

    return jsonify({"INFO": "事件级数据处理成功"}), 200


@app.route("/health", methods=["GET"]) 
def health():
    return jsonify({
        "status": "ok",
        "service_url_emotion": SERVICE_URL_EMOTION,
        "service_url_yuqing": SERVICE_URL_YUQING,
    })


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "8080"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host=host, port=port, debug=debug) 
