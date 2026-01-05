import requests
from dotenv import dotenv_values
import logging
import os

# 确保 logs 目录存在
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
# 配置日志记录器
logger = logging.getLogger('algorithm_service')
logger.setLevel(logging.INFO)
# 创建文件处理器，指定日志文件路径到 logs 文件夹
log_file_path = os.path.join(log_dir, 'algorithm_service.log')
file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
file_handler.setLevel(logging.INFO)

# 创建日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# 将处理器添加到记录器
logger.addHandler(file_handler)

def callAlgorithm(data):
    """
    调用算法服务
    """
    try:
        logger.info("开始调用算法服务")
        config = dotenv_values(os.path.join("api/.env"))
        algorithm_url = config["ALGORITHM_URL"]
        response = requests.post(algorithm_url, json=data, timeout=5)
        if response.status_code == 200:
            logger.info("算法服务调用成功，添加事件:" + data["title"])
            return {"message": "success"}
        else:
            error_msg = f"调用算法服务失败，状态码: {response.status_code}"
            logger.error(error_msg)
            return {"error": error_msg}
    except Exception as e:
        error_msg = f"调用算法服务发生异常: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}
