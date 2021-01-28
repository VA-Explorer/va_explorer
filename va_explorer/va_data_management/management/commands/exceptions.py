"""
openva_pipeline.exceptions
--------------------------

This module contains the set of openva_pipeline's exceptions.
"""

class PipelineError(Exception):
    """Base class for exceptions in the openva_pipeline module."""

class DatabaseConnectionError(PipelineError):
    """An error occurred connecting to the Transfer database."""
   
class PipelineConfigurationError(PipelineError):
    """An error occurred accessing the Pipeline_Conf table in the DB."""

class ODKConfigurationError(PipelineError):
    """An error occurred accessing the ODK_Conf table in the DB."""

class OpenVAConfigurationError(PipelineError):
    """An error occurred accessing the OpenVA_Conf table in the DB."""

class DHISConfigurationError(PipelineError):
    """An error occurred accessing the DHIS_Conf table in the DB."""

class DHISError(PipelineError):
    """An error occurred with the dhis module."""

class ODKError(PipelineError):
    """An error occurred with the odk module."""

class OpenVAError(PipelineError):
    """An error occurred with the openVA module."""

class SmartVAError(PipelineError):
    """An error occurred with the openVA module."""
