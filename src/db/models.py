# Re-export all models from core_models.py for backward compatibility
# This maintains compatibility with existing imports while avoiding circular imports

# Import from the consolidated core_models.py file
from src.db.core_models import Base, DeviceModel, DiagnosticCodeModel, ReadingModel

# For backward compatibility, keep this file
# Original class definitions are completely removed and replaced with imports
# from core_models.py. This ensures backward compatibility while resolving
# circular import issues.
#
# See core_models.py for the actual model implementations
