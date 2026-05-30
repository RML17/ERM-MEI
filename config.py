import os

class Config:
    """Base configuration class."""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get("SESSION_SECRET", "default-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///database.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Lista de alíquotas de impostos padrões
    DEFAULT_TAX_RATES = {
        'ICMS': 0.18,  # 18%
        'IPI': 0.10,   # 10%
        'PIS': 0.0165, # 1.65%
        'COFINS': 0.076, # 7.6%
        'ISS': 0.05,   # 5%
    }
    # Configurações para relatórios
    REPORT_FOLDER = 'reports'
    # Número máximo de itens por página nas listagens
    ITEMS_PER_PAGE = 20
    # Formato de data padrão
    DATE_FORMAT = "%d/%m/%Y"
    DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

class ProductionConfig(Config):
    """Production configuration."""
    # Configurações específicas de produção
    pass

# Configuração ativa com base no ambiente
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

active_config = config_by_name[os.environ.get('FLASK_ENV', 'development')]
