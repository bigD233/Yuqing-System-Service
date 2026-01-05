# 数据库上下文管理器
import pymysql
from contextlib import contextmanager
from config import config
import logging

# 获取logger实例
logger = logging.getLogger(__name__)

@contextmanager
def db_connection():
    # 生产环境将如下参数由development改为production
    current_config = config['development']()
    """自动根据当前环境选择配置的上下文管理器"""
    conn = pymysql.connect(
        host=current_config.MYSQL_HOST,
        user=current_config.MYSQL_USER,
        password=current_config.MYSQL_PASSWORD,
        database=current_config.MYSQL_DB,
        autocommit=False
    )
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"数据库操作出错: {str(e)}")
        # 将错误信息写入日志
        logger.error(f"数据库操作出错: {str(e)}", exc_info=True)
        raise e
    finally:
        cursor.close()
        conn.close()