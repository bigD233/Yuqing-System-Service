from flask import Blueprint

from api.controllers.hot_things_controller import getHotThings, getLvById, getEmotionsById, searchByKeyword, \
    getMapDataById, getWordCloudById, getPlatformMetricsById, getTrendDataById, getTypicalPostsById, getHeatDataById, \
    getTypicalRadarDataById, getPopulationCompositonById, getPopulationDataByPopId, addHotThing, addHotThingByCrawler, delHotThingById, clearAllTables
from api.controllers.system_info_controller import getSysInfo

# 创建主API蓝图
api_bp = Blueprint('api', __name__)

api_bp.route('/getHotThings', methods=['POST'])(getHotThings)
api_bp.route('/getSysInfo', methods=['POST'])(getSysInfo)
api_bp.route('/getLvById', methods=['POST'])(getLvById)
api_bp.route('/getEmotionsById', methods=['POST'])(getEmotionsById)
api_bp.route('/searchByKeyword', methods=['POST'])(searchByKeyword)
api_bp.route('/getMapDataById', methods=['POST'])(getMapDataById)
api_bp.route('/getWordCloudById', methods=['POST'])(getWordCloudById)
api_bp.route('/getPlatformMetricsById', methods=['POST'])(getPlatformMetricsById)
api_bp.route('/getTrendDataById', methods=['POST'])(getTrendDataById)
api_bp.route('/getTypicalPostsById', methods=['POST'])(getTypicalPostsById)
api_bp.route('/getHeatDataById', methods=['POST'])(getHeatDataById)
api_bp.route('/getTypicalRadarDataById', methods=['POST'])(getTypicalRadarDataById)
api_bp.route('/getPopulationCompositonById', methods=['POST'])(getPopulationCompositonById)
api_bp.route('/getPopulationDataByPopId', methods=['POST'])(getPopulationDataByPopId)
api_bp.route('/addHotThing', methods=['POST'])(addHotThing)
api_bp.route('/addHotThingByCrawler', methods=['POST'])(addHotThingByCrawler)
api_bp.route('/delHotThingById', methods=['POST'])(delHotThingById)
api_bp.route('/clearAllTables', methods=['POST'])(clearAllTables)