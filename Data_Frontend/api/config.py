import os

class Config:
    # 基础配置（所有环境共享）
    DEBUG = False

# 开发环境配置
class DevelopmentConfig(Config):
    DEBUG = True
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'root'
    MYSQL_DB = 'sentiment'

# 生产环境配置
class ProductionConfig(Config):
    DEBUG = False
    # 生产环境MySQL配置（必须从环境变量获取）
    MYSQL_HOST = os.getenv('MYSQL_HOST')
    MYSQL_USER = os.getenv('MYSQL_USER')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
    MYSQL_DB = os.getenv('MYSQL_DB')

    @classmethod
    def validate_config(cls):
        """验证生产环境配置是否完整"""
        required = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DB']
        missing = [var for var in required if not getattr(cls, var)]
        if missing:
            raise ValueError(f"生产环境缺少必要的MySQL配置: {', '.join(missing)}")


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}

# 如果是生产环境，验证配置
if os.getenv('FLASK_ENV') == 'production':
    ProductionConfig.validate_config()