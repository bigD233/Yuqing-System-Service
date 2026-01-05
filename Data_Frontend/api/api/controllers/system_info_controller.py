from flask import jsonify

from api.services.system_info_service import getSysInfoService
def getSysInfo():
    result = getSysInfoService()
    if not result:
        return jsonify({"message": "no data"})
    return jsonify({"data": result,"message": "success"})