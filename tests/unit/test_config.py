import pytest
import os
from unittest.mock import patch

from src.config import (
    get_api_key, 
    get_database_url,
    get_redis_url,
    get_data_source_config,
    validate_config
)


def test_get_api_key_from_env() -> None:
    """Test API key retrieval from environment variables."""
    with patch.dict(os.environ, {'ALPHA_VANTAGE_API_KEY': 'test_key'}):
        key = get_api_key('alpha_vantage')
        assert key == 'test_key'


def test_get_api_key_missing() -> None:
    """Test API key retrieval when key is missing."""
    with patch.dict(os.environ, {}, clear=True):
        key = get_api_key('alpha_vantage')
        assert key is None


def test_get_database_url_default() -> None:
    """Test database URL with default value."""
    with patch.dict(os.environ, {}, clear=True):
        url = get_database_url()
        assert url == "sqlite:///portfolio_data.db"


def test_get_database_url_from_env() -> None:
    """Test database URL from environment."""
    test_url = "postgresql://user:pass@localhost/test"
    with patch.dict(os.environ, {'DATABASE_URL': test_url}):
        url = get_database_url()
        assert url == test_url


def test_get_redis_url_default() -> None:
    """Test Redis URL with default value."""
    with patch.dict(os.environ, {}, clear=True):
        url = get_redis_url()
        assert url == "redis://localhost:6379/0"


def test_get_redis_url_from_env() -> None:
    """Test Redis URL from environment."""
    test_url = "redis://user:pass@remote:6379/1"
    with patch.dict(os.environ, {'REDIS_URL': test_url}):
        url = get_redis_url()
        assert url == test_url


def test_get_data_source_config() -> None:
    """Test data source configuration retrieval."""
    config = get_data_source_config()
    
    assert isinstance(config, dict)
    assert 'yahoo_finance' in config
    assert 'alpha_vantage' in config
    
    # Test structure
    yf_config = config['yahoo_finance']
    assert 'enabled' in yf_config
    assert isinstance(yf_config['enabled'], bool)


def test_validate_config_success() -> None:
    """Test successful configuration validation."""
    valid_config = {
        'database_url': 'sqlite:///test.db',
        'redis_url': 'redis://localhost:6379/0',
        'data_sources': {
            'yahoo_finance': {'enabled': True},
            'alpha_vantage': {'enabled': False}
        }
    }
    
    # Should not raise any exceptions
    result = validate_config(valid_config)
    assert result is True


def test_validate_config_missing_required() -> None:
    """Test configuration validation with missing required fields."""
    invalid_config = {
        'database_url': 'sqlite:///test.db',
        # Missing redis_url and data_sources
    }
    
    with pytest.raises((KeyError, ValueError)):
        validate_config(invalid_config)


def test_validate_config_invalid_database_url() -> None:
    """Test configuration validation with invalid database URL."""
    invalid_config = {
        'database_url': 'invalid_url',
        'redis_url': 'redis://localhost:6379/0',
        'data_sources': {
            'yahoo_finance': {'enabled': True}
        }
    }
    
    with pytest.raises(ValueError):
        validate_config(invalid_config)


def test_validate_config_invalid_redis_url() -> None:
    """Test configuration validation with invalid Redis URL."""
    invalid_config = {
        'database_url': 'sqlite:///test.db',
        'redis_url': 'invalid_redis_url',
        'data_sources': {
            'yahoo_finance': {'enabled': True}
        }
    }
    
    with pytest.raises(ValueError):
        validate_config(invalid_config)


def test_config_edge_cases() -> None:
    """Test configuration edge cases."""
    # Test empty environment
    with patch.dict(os.environ, {}, clear=True):
        config = get_data_source_config()
        assert isinstance(config, dict)
    
    # Test with whitespace values
    with patch.dict(os.environ, {'ALPHA_VANTAGE_API_KEY': '  '}):
        key = get_api_key('alpha_vantage')
        # Should handle whitespace appropriately
        assert key is None or key.strip() == ''


def test_config_type_validation() -> None:
    """Test configuration type validation."""
    # Test boolean conversion
    config = get_data_source_config()
    for source_name, source_config in config.items():
        if 'enabled' in source_config:
            assert isinstance(source_config['enabled'], bool)


def test_api_key_validation() -> None:
    """Test API key validation."""
    # Test various data source names
    test_sources = ['alpha_vantage', 'yahoo_finance', 'invalid_source']
    
    for source in test_sources:
        key = get_api_key(source)
        assert key is None or isinstance(key, str)