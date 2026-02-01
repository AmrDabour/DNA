"""
SNP Analysis Tasks
===================
Background tasks for SNP file processing and VEP annotation.

These tasks can run synchronously (when Celery is disabled) or
asynchronously (when Celery is enabled with RabbitMQ).
"""
import os
import logging
from typing import Dict, Any, List, Optional

from celery_app import async_task, CELERY_ENABLED

logger = logging.getLogger(__name__)


@async_task(name='tasks.snp_analysis.analyze_snp_file')
def analyze_snp_file_task(
    file_path: str,
    patient_id: Optional[str] = None,
    include_vep: bool = True,
    vep_limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Analyze an SNP file with optional VEP annotation.
    
    This task:
    1. Reads and validates the SNP file
    2. Extracts patient metadata
    3. Runs VEP annotation (if enabled)
    4. Returns comprehensive analysis results
    
    Args:
        file_path: Path to the SNP CSV/PED file
        patient_id: Optional patient identifier override
        include_vep: Whether to include VEP functional annotation
        vep_limit: Limit number of SNPs for VEP (None = all)
    
    Returns:
        Dict with analysis results and statistics
    """
    logger.info(f"Starting SNP analysis for: {file_path}")
    
    try:
        import pandas as pd
        
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}
        
        # Read the file
        df = pd.read_csv(file_path)
        
        # Extract metadata
        result = {
            "success": True,
            "file_path": file_path,
            "total_snps": len(df),
            "columns": list(df.columns),
        }
        
        # Get patient info if available
        if 'Patient_ID' in df.columns:
            result["patient_id"] = df['Patient_ID'].iloc[0] if not df.empty else patient_id
        else:
            result["patient_id"] = patient_id or "Unknown"
        
        if 'Population' in df.columns:
            result["population"] = df['Population'].iloc[0] if not df.empty else "Unknown"
        
        # Get SNP column
        snp_column = None
        for col in df.columns:
            if col.upper() == 'SNP':
                snp_column = col
                break
        
        if snp_column:
            rs_ids = df[snp_column].dropna().tolist()
            valid_rs_ids = [str(rs).strip() for rs in rs_ids if str(rs).lower().startswith('rs')]
            result["valid_snps"] = len(valid_rs_ids)
            result["sample_snps"] = valid_rs_ids[:10]  # First 10 as sample
        
        # Run VEP annotation if requested
        if include_vep and snp_column:
            try:
                from services.vep_service import vep_service
                
                if vep_service.enabled:
                    vep_result = vep_service.analyze_patient_csv(file_path, limit=vep_limit)
                    result["vep_analysis"] = {
                        "success": vep_result.get("success", False),
                        "snps_annotated": vep_result.get("snps_annotated", 0),
                        "high_impact_count": vep_result.get("high_impact_count", 0),
                        "impact_distribution": vep_result.get("impact_distribution", {}),
                    }
                else:
                    result["vep_analysis"] = {"skipped": True, "reason": "VEP service disabled"}
            except Exception as vep_error:
                logger.error(f"VEP analysis failed: {vep_error}")
                result["vep_analysis"] = {"success": False, "error": str(vep_error)}
        
        logger.info(f"SNP analysis complete: {result['valid_snps']} valid SNPs")
        return result
        
    except Exception as e:
        logger.error(f"SNP analysis failed: {e}")
        return {"success": False, "error": str(e)}


@async_task(name='tasks.snp_analysis.batch_vep_annotation')
def batch_vep_annotation_task(
    rs_ids: List[str],
    batch_size: int = 200
) -> Dict[str, Any]:
    """
    Run VEP annotation on a batch of rsIDs.
    
    Args:
        rs_ids: List of SNP rsIDs to annotate
        batch_size: Number of SNPs per API request
    
    Returns:
        Dict with annotation results
    """
    logger.info(f"Starting batch VEP annotation for {len(rs_ids)} SNPs")
    
    try:
        from services.vep_service import vep_service
        
        if not vep_service.enabled:
            return {"success": False, "error": "VEP service is disabled"}
        
        result = vep_service.get_batch_variants(rs_ids)
        
        logger.info(f"VEP annotation complete: {result.get('total_annotated', 0)} annotated")
        return result
        
    except Exception as e:
        logger.error(f"Batch VEP annotation failed: {e}")
        return {"success": False, "error": str(e)}


# ============================================================
# Helper function for sync/async call pattern
# ============================================================

def analyze_snp_file(file_path: str, **kwargs) -> Dict[str, Any]:
    """
    Analyze SNP file - uses async if Celery enabled, sync otherwise.
    
    Usage:
        # This automatically handles sync/async based on config
        result = analyze_snp_file(file_path, include_vep=True)
        
        # For async (returns AsyncResult when Celery enabled):
        async_result = analyze_snp_file_task.delay(file_path)
        result = async_result.get()  # Wait for result
    """
    if CELERY_ENABLED:
        return analyze_snp_file_task.delay(file_path, **kwargs).get()
    else:
        return analyze_snp_file_task(file_path, **kwargs)



