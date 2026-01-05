from datetime import datetime

from flask import jsonify, request
import threading

from api.services.hot_things_service import clearAllTablesService, deleteHotThingService, getHotThingsService, getLvByIdService, getEmotionsByIdService, \
    searchByKeywordService, getMapDataByIdService, getWordCloudByIdService, getPlatformMetricsByIdService, \
    getTrendDataByIdService, getTypicalPostsByIdService, getHeatDataByIdService, getTypicalRadarDataByIdService, \
    getPopulationCompositonByIdService, getPopulationDataByPopIdService, addHotThingService
from api.utils.obtain_external_services import callAlgorithm


def addHotThingByCrawler():
    """
    添加爬虫数据到数据库
    """
    data = request.get_json()
    if not data or 'title' not in data or 'data' not in data:
        return jsonify({"message": "参数不正确"}), 400
    # 在返回响应前启动后台线程处理外部API调用
    thread = threading.Thread(target=callAlgorithm, args=(data,))
    thread.daemon = True
    thread.start()
    # 立即返回成功响应到爬虫程序
    return jsonify({"message": "success"}), 200


def getHotThings():
    result = getHotThingsService()
    if not result:
        return jsonify({"message": "no data"})
    return jsonify({"data": result, "message": "success"})


def getLvById():
    result = getLvByIdService(request.get_json().get("id"))
    if not result:
        return jsonify({"message": "no data"})
    return jsonify({"data": result, "message": "success"})


def getEmotionsById():
    result = getEmotionsByIdService(request.get_json().get("id"))
    if not result:
        return jsonify({"message": "no data"})
    return jsonify({"data": result, "message": "success"})


def searchByKeyword():
    result = searchByKeywordService(request.get_json().get("keyword"))
    if not result:
        return jsonify({"message": "no data", "code": 0})
    return jsonify({"data": result, "message": "success"})


def getMapDataById():
    result = getMapDataByIdService(request.get_json().get("id"))
    if not result:
        return jsonify({"message": "no data"})
    return jsonify({"data": result, "message": "success"})


def getWordCloudById():
    result = getWordCloudByIdService(request.get_json().get("id"))
    if not result:
        return jsonify({"message": "no data"})
    return jsonify({"data": result, "message": "success"})


def getPlatformMetricsById():
    result = getPlatformMetricsByIdService(request.get_json().get("id"))
    if not result:
        return jsonify({"message": "no data"})
    return jsonify({"data": result, "message": "success"})


def getTrendDataById():
    result = getTrendDataByIdService(request.get_json().get("id"))
    if not result:
        return jsonify({"message": "no data"})
    return jsonify({"data": result, "message": "success"})


def getTypicalPostsById():
    result = getTypicalPostsByIdService(request.get_json().get("id"))
    if not result:
        return jsonify({"message": "no data"})
    return jsonify({"data": result, "message": "success"})


def getHeatDataById():
    result = getHeatDataByIdService(request.get_json().get("id"))
    if not result:
        return jsonify({"message": "no data"})
    return jsonify({"data": result, "message": "success"})


def getTypicalRadarDataById():
    result = getTypicalRadarDataByIdService(request.get_json().get("id"))
    if not result:
        return jsonify({"message": "no data"})
    return jsonify({"data": result, "message": "success"})


def getPopulationCompositonById():
    result = getPopulationCompositonByIdService(request.get_json().get("id"))
    if not result:
        return jsonify({"message": "no data"})
    return jsonify({"data": result, "message": "success"})


def getPopulationDataByPopId():
    result = getPopulationDataByPopIdService(request.get_json().get("id"))
    if not result:
        return jsonify({"message": "no data"})
    return jsonify({"data": result, "message": "success"})


def validate_hot_thing(data):
    if not isinstance(data, dict):
        return False, "hot_thing should be an object"

    # 定义字段及其期望类型
    field_validations = {
        'title': {'type': str, 'message': "title should be a string"},
        'url': {'type': str, 'message': "url should be a string"},
        'source': {'type': str, 'message': "source should be a string"},
        'date': {'type': 'datetime', 'message': "Invalid datetime format, should be YYYY-MM-DD HH:MM:SS"},
        'heat': {'type': (int, float), 'message': "heat should be a number"},
        'warning_lv': {'type': str, 'message': "warning_lv should be a string"},
        'total_posts': {'type': (int, float), 'message': "total_posts should be a number"},
        'total_users': {'type': (int, float), 'message': "total_users should be a number"},
        'total_interactions': {'type': (int, float), 'message': "total_interactions should be a number"},
        'posts_with_location': {'type': (int, float), 'message': "posts_with_location should be a number"}
    }

    # 检查所有必需字段是否存在
    for field in field_validations:
        if field not in data:
            return False, f"Missing required field: {field}"

    # 检查每个字段的类型
    for field, validation in field_validations.items():
        if validation['type'] == 'datetime':  # 修改为datetime类型检查
            try:
                datetime.strptime(data[field], "%Y-%m-%d %H:%M:%S")  # 修改为包含时间的格式
            except ValueError:
                return False, validation['message']
        elif not isinstance(data[field], validation['type']):
            return False, validation['message']

    return True, ""


def validate_user_emotion(data):
    required_fields = ['positive', 'negative', 'like', 'happiness', 'sadness',
                       'anger', 'disgust', 'fear', 'surprise']

    if not isinstance(data, dict):
        return False, "user_emotion should be an object"

    for field in required_fields:
        if field not in data:
            return False, f"Missing required field in user_emotion: {field}"
        if not isinstance(data[field], (int, float)):
            return False, f"{field} in user_emotion should be a number"

    return True, ""


def validate_heat(data):
    required_fields = ['forward_count', 'comment_count', 'like_count',
                       'composite_hot_score', 'base_hot_value',
                       'media_hot_value', 'interaction_hot_value']

    if not isinstance(data, dict):
        return False, "heat should be an object"

    for field in required_fields:
        if field not in data:
            return False, f"Missing required field in heat: {field}"
        if not isinstance(data[field], (int, float)):
            return False, f"{field} in heat should be a number"

    return True, ""


def validate_trend(data):
    if not isinstance(data, list):
        return False, "trend should be an array"
    if not all(isinstance(item, (int, float)) for item in data):
        return False, "All trend items should be numbers"
    return True, ""


def validate_typical_posts(data):
    if not isinstance(data, list):
        return False, "typical_posts should be an array"

    required_fields = {
        'title': str,
        'url': str,
        'source': str,
        'datetime': 'datetime',
        'heat': (int, float),
        'autonomy': (int, float),
        'stimulus': (int, float),
        'fraternity': (int, float),
        'friendliness': (int, float),
        'compliance': (int, float),
        'tradition': (int, float),
        'security': (int, float),
        'authority': (int, float),
        'achievement': (int, float),
        'hedonism': (int, float)
    }

    for post in data:
        if not isinstance(post, dict):
            return False, "Each post in typical_posts should be an object"

        for field, field_type in required_fields.items():
            if field not in post:
                return False, f"Missing required field in post: {field}"

            if field == 'datetime':
                try:
                    datetime.strptime(post['datetime'], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    return False, "Invalid datetime format in post, should be YYYY-MM-DD HH:MM:SS"
            elif field_type == str:
                if not isinstance(post[field], str):
                    return False, f"{field} in post should be a string"
            elif isinstance(field_type, tuple):  # For numeric fields
                if not isinstance(post[field], field_type):
                    return False, f"{field} in post should be a number"

    return True, ""


def validate_population_composition(data):
    if not isinstance(data, list):
        return False, "population_composition should be an array"

    for group in data:
        if not isinstance(group, dict):
            return False, "Each group in population_composition should be an object"

        if 'name' not in group or 'value' not in group or 'population_values' not in group:
            return False, "Missing required fields in population group"

        if not isinstance(group['value'], (int, float)):
            return False, "value in population group should be a number"

        if not isinstance(group['population_values'], list):
            return False, "population_values should be an array"

        for value in group['population_values']:
            if not isinstance(value, dict):
                return False, "Each population value should be an object"
            if 'label' not in value or 'value' not in value:
                return False, "Missing required fields in population value"
            if not isinstance(value['value'], (int, float)):
                return False, "value in population value should be a number"

    return True, ""


def validate_map(data):
    if not isinstance(data, list):
        return False, "map should be an array"

    required_fields = ['province_pid', 'province_name', 'color']

    for province in data:
        if not isinstance(province, dict):
            return False, "Each province in map should be an object"

        for field in required_fields:
            if field not in province:
                return False, f"Missing required field in province: {field}"

    return True, ""


def addHotThing():
    data = request.get_json()

    if not data:
        return jsonify({"message": "No data provided"}), 400

    # Validate each section
    validators = [
        ('hot_thing', validate_hot_thing),
        ('user_emotion', validate_user_emotion),
        ('heat', validate_heat),
        ('trend', validate_trend),
        ('typical_posts', validate_typical_posts),
        ('population_composition', validate_population_composition),
        ('map', validate_map)
    ]

    for field, validator in validators:
        if field not in data:
            return jsonify({"message": f"Missing required section: {field}"}), 400

        is_valid, error_msg = validator(data[field])
        if not is_valid:
            return jsonify({"message": error_msg}), 400

    if 'word_cloud' in data and not isinstance(data['word_cloud'], str):
        return jsonify({"message": "word_cloud should be a string"}), 400

    result = addHotThingService(data)
    if not result:
        return jsonify({"message": "insert fail"}), 400
    return jsonify({"message": "insert success"}), 201

def delHotThingById():
    result = deleteHotThingService(request.get_json().get("id"))
    if not result:
        return jsonify({"message": "delete fail"}), 400
    
    return jsonify({"message": "delete success"}), 200

def clearAllTables():
    result = clearAllTablesService()
    if not result:
        return jsonify({"message": "clear fail"}), 400
    
    return jsonify({"message": "clear success"}), 200