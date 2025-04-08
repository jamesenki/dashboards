"""
Security module initialization.
Provides central access to security wrappers and validation tools.
"""
from .data_validation import ArrowDataValidator
from .data_validation import SecurityError as DataSecurityError
from .ml_security import MLSecurityWrapper
from .ml_security import SecurityError as MLSecurityError

# Create default instances for easy import
ml_security = MLSecurityWrapper(
    allow_file_writes=False, trusted_model_dirs=["/app/models", "/data/trusted_models"]
)

data_validator = ArrowDataValidator(
    trusted_sources=["s3://iotsphere-trusted-data", "/data/trusted"]
)

# Function aliases for easier usage
validate_model_security = ml_security.validate_model_security
validate_arrow_data = data_validator.validate_arrow_data
safe_read_parquet = data_validator.safe_read_parquet
safe_read_arrow = data_validator.safe_read_arrow

__all__ = [
    "MLSecurityWrapper",
    "ArrowDataValidator",
    "MLSecurityError",
    "DataSecurityError",
    "ml_security",
    "data_validator",
    "validate_model_security",
    "validate_arrow_data",
    "safe_read_parquet",
    "safe_read_arrow",
]
