"""
VEP (Variant Effect Predictor) Service
Integrates with Ensembl REST API for SNP functional annotation
"""
import os
import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import requests
from threading import Lock

logger = logging.getLogger(__name__)


class RateLimiter:
    """Thread-safe rate limiter for API calls"""
    
    def __init__(self, requests_per_second: float = 15.0):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0
        self.lock = Lock()
    
    def wait(self):
        """Wait if necessary to respect rate limit"""
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()


class VEPService:
    """
    Ensembl VEP REST API Integration for GenovaAI
    
    Provides SNP functional annotation including:
    - Gene impact predictions
    - CADD pathogenicity scores  
    - Population allele frequencies
    - Clinical significance
    
    Docs: https://rest.ensembl.org/documentation/info/vep_id_post
    """
    
    BASE_URL = "https://rest.ensembl.org"
    BATCH_LIMIT = 200  # Ensembl limit per POST request
    DEFAULT_CACHE_TTL_DAYS = 7
    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 2  # Exponential backoff base
    
    def __init__(self):
        self.rate_limiter = RateLimiter(
            requests_per_second=float(os.environ.get('VEP_RATE_LIMIT', 15))
        )
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.enabled = os.environ.get('VEP_ENABLED', 'true').lower() == 'true'
        self.cache_ttl_days = int(os.environ.get('VEP_CACHE_TTL', self.DEFAULT_CACHE_TTL_DAYS))
        self.batch_size = int(os.environ.get('VEP_BATCH_SIZE', self.BATCH_LIMIT))
        
        # In-memory cache for session (DB cache handled separately)
        self._memory_cache: Dict[str, Dict] = {}
        self._cache_lock = Lock()
    
    def _make_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """Make HTTP request with rate limiting and retry logic"""
        if not self.enabled:
            return None
        
        self.rate_limiter.wait()
        
        for attempt in range(self.MAX_RETRIES):
            try:
                if method.upper() == 'GET':
                    response = requests.get(url, headers=self.headers, timeout=60, **kwargs)
                else:
                    response = requests.post(url, headers=self.headers, timeout=120, **kwargs)
                
                # Handle rate limiting response
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 5))
                    logger.warning(f"VEP rate limited. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                
                # Success or client error (don't retry client errors)
                if response.status_code < 500:
                    return response
                
                # Server error - retry with backoff
                logger.warning(f"VEP server error {response.status_code}. Attempt {attempt + 1}/{self.MAX_RETRIES}")
                
            except requests.exceptions.Timeout:
                logger.warning(f"VEP request timeout. Attempt {attempt + 1}/{self.MAX_RETRIES}")
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"VEP connection error: {e}. Attempt {attempt + 1}/{self.MAX_RETRIES}")
            except Exception as e:
                logger.error(f"VEP unexpected error: {e}")
                return None
            
            # Exponential backoff
            if attempt < self.MAX_RETRIES - 1:
                sleep_time = self.RETRY_BACKOFF_BASE ** attempt
                time.sleep(sleep_time)
        
        return None
    
    def _get_from_cache(self, rs_id: str) -> Optional[Dict]:
        """Get result from memory cache"""
        with self._cache_lock:
            cached = self._memory_cache.get(rs_id)
            if cached:
                expires_at = cached.get('_expires_at')
                if expires_at and datetime.fromisoformat(expires_at) > datetime.utcnow():
                    return cached.get('data')
                else:
                    # Expired, remove from cache
                    del self._memory_cache[rs_id]
        return None
    
    def _set_cache(self, rs_id: str, data: Dict):
        """Set result in memory cache"""
        with self._cache_lock:
            expires_at = datetime.utcnow() + timedelta(days=self.cache_ttl_days)
            self._memory_cache[rs_id] = {
                'data': data,
                '_expires_at': expires_at.isoformat()
            }
    
    def _get_from_db_cache(self, rs_id: str) -> Optional[Dict]:
        """Get result from database cache"""
        try:
            from database.models import VEPAnnotation
            from database import db
            
            cached = VEPAnnotation.query.filter_by(rs_id=rs_id).first()
            if cached and cached.expires_at and cached.expires_at > datetime.utcnow():
                return cached.to_dict()
        except Exception as e:
            logger.debug(f"DB cache lookup failed for {rs_id}: {e}")
        return None
    
    def _save_to_db_cache(self, rs_id: str, parsed_result: Dict, full_response: Dict):
        """Save result to database cache"""
        try:
            from database.models import VEPAnnotation
            from database import db
            
            expires_at = datetime.utcnow() + timedelta(days=self.cache_ttl_days)
            
            # Upsert pattern
            existing = VEPAnnotation.query.filter_by(rs_id=rs_id).first()
            if existing:
                existing.most_severe_consequence = parsed_result.get('most_severe_consequence')
                existing.impact = parsed_result.get('impact')
                existing.gene_symbol = parsed_result.get('gene_symbol')
                existing.cadd_phred = parsed_result.get('cadd_score')
                existing.protein_change = parsed_result.get('protein_change')
                existing.population_frequencies = json.dumps(parsed_result.get('population_frequencies', {}))
                existing.full_response = json.dumps(full_response)
                existing.cached_at = datetime.utcnow()
                existing.expires_at = expires_at
            else:
                annotation = VEPAnnotation(
                    rs_id=rs_id,
                    most_severe_consequence=parsed_result.get('most_severe_consequence'),
                    impact=parsed_result.get('impact'),
                    gene_symbol=parsed_result.get('gene_symbol'),
                    cadd_phred=parsed_result.get('cadd_score'),
                    protein_change=parsed_result.get('protein_change'),
                    population_frequencies=json.dumps(parsed_result.get('population_frequencies', {})),
                    full_response=json.dumps(full_response),
                    cached_at=datetime.utcnow(),
                    expires_at=expires_at
                )
                db.session.add(annotation)
            
            db.session.commit()
        except Exception as e:
            logger.debug(f"Failed to save to DB cache for {rs_id}: {e}")
            try:
                from database import db
                db.session.rollback()
            except:
                pass
    
    def _parse_vep_result(self, result: Dict) -> Dict[str, Any]:
        """Parse VEP result into standardized GenovaAI format"""
        parsed = {
            "rs_id": result.get("id", ""),
            "input": result.get("input", ""),
            "most_severe_consequence": result.get("most_severe_consequence", ""),
            "impact": "MODIFIER",  # Default impact
            "gene_symbol": None,
            "gene_id": None,
            "transcript_id": None,
            "biotype": None,
            "protein_change": None,
            "codon_change": None,
            "amino_acids": None,
            "cadd_score": None,
            "cadd_raw": None,
            "sift_prediction": None,
            "sift_score": None,
            "polyphen_prediction": None,
            "polyphen_score": None,
            "population_frequencies": {},
            "clinical_significance": [],
            "consequences": []
        }
        
        # Parse transcript consequences
        transcripts = result.get("transcript_consequences", [])
        if transcripts:
            # Prefer canonical transcript, otherwise use first
            canonical = next((t for t in transcripts if t.get("canonical")), transcripts[0])
            
            parsed["gene_symbol"] = canonical.get("gene_symbol")
            parsed["gene_id"] = canonical.get("gene_id")
            parsed["transcript_id"] = canonical.get("transcript_id")
            parsed["biotype"] = canonical.get("biotype")
            parsed["impact"] = canonical.get("impact", "MODIFIER")
            
            # Protein-level changes
            parsed["protein_change"] = canonical.get("hgvsp")
            parsed["codon_change"] = canonical.get("codons")
            parsed["amino_acids"] = canonical.get("amino_acids")
            
            # Pathogenicity predictions
            if "cadd_phred" in canonical:
                parsed["cadd_score"] = canonical["cadd_phred"]
            if "cadd_raw" in canonical:
                parsed["cadd_raw"] = canonical["cadd_raw"]
            
            if "sift_prediction" in canonical:
                parsed["sift_prediction"] = canonical["sift_prediction"]
                parsed["sift_score"] = canonical.get("sift_score")
            
            if "polyphen_prediction" in canonical:
                parsed["polyphen_prediction"] = canonical["polyphen_prediction"]
                parsed["polyphen_score"] = canonical.get("polyphen_score")
            
            # All consequence terms
            parsed["consequences"] = canonical.get("consequence_terms", [])
        
        # Parse colocated variants for population frequencies and clinical data
        colocated = result.get("colocated_variants", [])
        for var in colocated:
            # Population frequencies
            if "frequencies" in var:
                parsed["population_frequencies"] = var["frequencies"]
            
            # Clinical significance from ClinVar
            if "clin_sig" in var:
                clin_sig = var["clin_sig"]
                if isinstance(clin_sig, list):
                    parsed["clinical_significance"] = clin_sig
                else:
                    parsed["clinical_significance"] = [clin_sig]
        
        return parsed
    
    def get_single_variant(self, rs_id: str) -> Dict[str, Any]:
        """
        Analyze a single SNP by rsID
        
        Args:
            rs_id: SNP rsID (e.g., rs4040617)
        
        Returns:
            Dict with success status and VEP annotation data
        """
        if not self.enabled:
            return {"success": False, "error": "VEP service is disabled"}
        
        # Normalize rsID
        rs_id = rs_id.strip().lower()
        if not rs_id.startswith('rs'):
            rs_id = f"rs{rs_id}"
        
        # Check memory cache first
        cached = self._get_from_cache(rs_id)
        if cached:
            return {"success": True, "data": cached, "source": "memory_cache"}
        
        # Check database cache
        db_cached = self._get_from_db_cache(rs_id)
        if db_cached:
            self._set_cache(rs_id, db_cached)  # Warm memory cache
            return {"success": True, "data": db_cached, "source": "db_cache"}
        
        # Make API request
        url = f"{self.BASE_URL}/vep/human/id/{rs_id}"
        params = {
            "CADD": 1,
            "canonical": 1,
            "protein": 1,
            "hgvs": 1,
            "numbers": 1,
            "domains": 1,
            "regulatory": 1,
            "sift": "b",  # Include SIFT predictions
            "polyphen": "b",  # Include PolyPhen predictions
        }
        
        try:
            response = self._make_request('GET', url, params=params)
            
            if response is None:
                return {"success": False, "error": "VEP service unavailable"}
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    parsed = self._parse_vep_result(data[0])
                    
                    # Cache results
                    self._set_cache(rs_id, parsed)
                    self._save_to_db_cache(rs_id, parsed, data[0])
                    
                    return {"success": True, "data": parsed, "source": "api"}
                else:
                    return {"success": False, "error": f"No VEP data found for {rs_id}"}
            
            elif response.status_code == 400:
                return {"success": False, "error": f"Invalid rsID: {rs_id}"}
            elif response.status_code == 404:
                return {"success": False, "error": f"SNP not found: {rs_id}"}
            else:
                return {"success": False, "error": f"VEP API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"VEP single variant error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_batch_variants(self, rs_ids: List[str]) -> Dict[str, Any]:
        """
        Analyze multiple SNPs in batches
        
        Args:
            rs_ids: List of SNP rsIDs
        
        Returns:
            Dict with success status, annotated variants, and errors
        """
        if not self.enabled:
            return {"success": False, "error": "VEP service is disabled"}
        
        if not rs_ids:
            return {"success": False, "error": "No rsIDs provided"}
        
        # Normalize and deduplicate rsIDs
        normalized_ids = []
        for rs_id in rs_ids:
            rs_id = rs_id.strip().lower()
            if not rs_id.startswith('rs'):
                rs_id = f"rs{rs_id}"
            if rs_id not in normalized_ids:
                normalized_ids.append(rs_id)
        
        all_results = []
        errors = []
        cache_hits = 0
        api_calls = 0
        
        # Check caches first
        uncached_ids = []
        for rs_id in normalized_ids:
            cached = self._get_from_cache(rs_id)
            if cached:
                all_results.append(cached)
                cache_hits += 1
                continue
            
            db_cached = self._get_from_db_cache(rs_id)
            if db_cached:
                all_results.append(db_cached)
                self._set_cache(rs_id, db_cached)
                cache_hits += 1
                continue
            
            uncached_ids.append(rs_id)
        
        # Process uncached IDs in batches
        for i in range(0, len(uncached_ids), self.batch_size):
            batch = uncached_ids[i:i + self.batch_size]
            
            url = f"{self.BASE_URL}/vep/human/id"
            payload = {
                "ids": batch,
                "CADD": 1,
                "canonical": 1,
                "protein": 1,
                "hgvs": 1,
                "numbers": 1,
                "sift": "b",
                "polyphen": "b",
            }
            
            try:
                response = self._make_request('POST', url, json=payload)
                api_calls += 1
                
                if response is None:
                    errors.extend([{"rs_id": rs_id, "error": "API unavailable"} for rs_id in batch])
                    continue
                
                if response.status_code == 200:
                    results = response.json()
                    
                    # Track which IDs we got results for
                    found_ids = set()
                    
                    for result in results:
                        parsed = self._parse_vep_result(result)
                        all_results.append(parsed)
                        found_ids.add(parsed["rs_id"].lower())
                        
                        # Cache results
                        self._set_cache(parsed["rs_id"], parsed)
                        self._save_to_db_cache(parsed["rs_id"], parsed, result)
                    
                    # Track not found IDs
                    for rs_id in batch:
                        if rs_id.lower() not in found_ids:
                            errors.append({"rs_id": rs_id, "error": "Not found in VEP"})
                else:
                    errors.extend([
                        {"rs_id": rs_id, "error": f"API error: {response.status_code}"} 
                        for rs_id in batch
                    ])
                    
            except Exception as e:
                logger.error(f"VEP batch error: {e}")
                errors.extend([{"rs_id": rs_id, "error": str(e)} for rs_id in batch])
        
        return {
            "success": True,
            "total_queried": len(normalized_ids),
            "total_annotated": len(all_results),
            "cache_hits": cache_hits,
            "api_calls": api_calls,
            "data": all_results,
            "errors": errors
        }
    
    def analyze_patient_csv(self, csv_path: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze variants from an uploaded patient CSV file
        
        Args:
            csv_path: Path to the CSV file (can also be .ped file that was converted)
            limit: Optional limit on number of SNPs to analyze
        
        Returns:
            Dict with analysis results and statistics
        """
        if not self.enabled:
            return {"success": False, "error": "VEP service is disabled"}
        
        try:
            import pandas as pd
            
            if not os.path.exists(csv_path):
                return {"success": False, "error": f"File not found: {csv_path}"}
            
            # Read CSV file
            try:
                df = pd.read_csv(csv_path)
            except Exception as e:
                return {"success": False, "error": f"Could not read CSV file: {str(e)}"}
            
            # Check for SNP column (case-insensitive)
            snp_column = None
            for col in df.columns:
                if col.upper() == 'SNP':
                    snp_column = col
                    break
            
            if not snp_column:
                return {"success": False, "error": "CSV file must have 'SNP' column with rsID values (rs12345...)"}
            
            if not snp_column:
                return {"success": False, "error": "CSV file must have 'SNP' column with rsID values (rs12345...)"}
            
            # Extract rsIDs from the SNP column
            rs_ids = df[snp_column].dropna().tolist()
            
            # Filter out invalid entries (keep only rsIDs that start with 'rs' or are numeric)
            valid_rs_ids = []
            invalid_count = 0
            for rs_id in rs_ids:
                rs_str = str(rs_id).strip()
                # Check if it's a valid rsID (starts with 'rs' or is just a number)
                if rs_str.lower().startswith('rs'):
                    valid_rs_ids.append(rs_str)
                elif rs_str.isdigit():
                    valid_rs_ids.append(f"rs{rs_str}")
                else:
                    invalid_count += 1
            
            if not valid_rs_ids:
                # Check if this looks like a converted PED file without proper rsIDs
                sample_values = [str(x) for x in rs_ids[:5]]
                if any('SNP_' in v for v in sample_values):
                    return {
                        "success": False, 
                        "error": "This appears to be a PED file converted without a MAP file. "
                                "The SNP column contains placeholder values (SNP_1, SNP_2, etc.) instead of real rsIDs. "
                                "Please either:\n"
                                "1. Upload a CSV file with real rsIDs (rs12345, rs67890, etc.)\n"
                                "2. Upload your PED file with its accompanying .map file in the same folder"
                    }
                return {
                    "success": False, 
                    "error": f"No valid rsIDs found in SNP column. Found {len(rs_ids)} entries but none are valid rsIDs. "
                            "Values should be like 'rs12345' or 'rs4040617'. "
                            f"Sample values found: {sample_values}"
                }
            
            if limit:
                valid_rs_ids = valid_rs_ids[:limit]
            
            logger.info(f"Found {len(valid_rs_ids)} valid rsIDs out of {len(rs_ids)} total entries ({invalid_count} invalid)")
            
            # Get patient metadata
            patient_id = df['Patient_ID'].iloc[0] if 'Patient_ID' in df.columns else "Unknown"
            population = df['Population'].iloc[0] if 'Population' in df.columns else "Unknown"
            
            # Analyze variants
            result = self.get_batch_variants(valid_rs_ids)
            
            if not result["success"]:
                return result
            
            # Calculate impact statistics
            impact_counts = {"HIGH": 0, "MODERATE": 0, "LOW": 0, "MODIFIER": 0}
            consequence_counts = {}
            genes_affected = set()
            pathogenic_variants = []
            
            for variant in result["data"]:
                impact = variant.get("impact", "MODIFIER")
                impact_counts[impact] = impact_counts.get(impact, 0) + 1
                
                # Count consequences
                for cons in variant.get("consequences", []):
                    consequence_counts[cons] = consequence_counts.get(cons, 0) + 1
                
                # Track genes
                if variant.get("gene_symbol"):
                    genes_affected.add(variant["gene_symbol"])
                
                # Identify potentially pathogenic variants
                cadd = variant.get("cadd_score")
                if cadd and cadd >= 20:  # CADD >= 20 suggests pathogenicity
                    pathogenic_variants.append(variant)
            
            # Sort consequences by count
            top_consequences = sorted(
                consequence_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
            
            return {
                "success": True,
                "patient_id": patient_id,
                "population": population,
                "file_analyzed": csv_path,
                "total_snps_in_file": len(df),
                "snps_analyzed": len(valid_rs_ids),
                "snps_annotated": result["total_annotated"],
                "cache_hits": result["cache_hits"],
                "api_calls": result["api_calls"],
                "impact_distribution": impact_counts,
                "top_consequences": dict(top_consequences),
                "genes_affected_count": len(genes_affected),
                "genes_affected": sorted(list(genes_affected))[:50],  # Top 50 genes
                "high_impact_count": impact_counts["HIGH"],
                "pathogenic_variants_count": len(pathogenic_variants),
                "pathogenic_variants": pathogenic_variants[:20],  # Top 20
                "variants": result["data"],
                "errors": result["errors"]
            }
            
        except Exception as e:
            logger.error(f"VEP CSV analysis error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_service_status(self) -> Dict[str, Any]:
        """Check VEP service status and connectivity"""
        status = {
            "enabled": self.enabled,
            "base_url": self.BASE_URL,
            "batch_limit": self.batch_size,
            "cache_ttl_days": self.cache_ttl_days,
            "memory_cache_size": len(self._memory_cache),
            "api_available": False,
            "response_time_ms": None
        }
        
        if not self.enabled:
            return status
        
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.BASE_URL}/info/ping",
                headers={"Accept": "application/json"},
                timeout=10
            )
            elapsed_ms = (time.time() - start_time) * 1000
            
            status["api_available"] = response.status_code == 200
            status["response_time_ms"] = round(elapsed_ms, 2)
            
        except Exception as e:
            status["error"] = str(e)
        
        return status
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        memory_count = len(self._memory_cache)
        
        db_count = 0
        try:
            from database.models import VEPAnnotation
            db_count = VEPAnnotation.query.count()
        except:
            pass
        
        return {
            "memory_cache_entries": memory_count,
            "db_cache_entries": db_count,
            "cache_ttl_days": self.cache_ttl_days
        }
    
    def clear_expired_cache(self) -> Dict[str, Any]:
        """Clear expired entries from caches"""
        cleared_memory = 0
        cleared_db = 0
        
        # Clear memory cache
        with self._cache_lock:
            now = datetime.utcnow()
            expired_keys = []
            for key, value in self._memory_cache.items():
                expires_at = value.get('_expires_at')
                if expires_at and datetime.fromisoformat(expires_at) <= now:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._memory_cache[key]
                cleared_memory += 1
        
        # Clear database cache
        try:
            from database.models import VEPAnnotation
            from database import db
            
            result = VEPAnnotation.query.filter(
                VEPAnnotation.expires_at <= datetime.utcnow()
            ).delete()
            db.session.commit()
            cleared_db = result
        except Exception as e:
            logger.error(f"Failed to clear DB cache: {e}")
        
        return {
            "cleared_memory": cleared_memory,
            "cleared_db": cleared_db
        }


# Singleton instance
vep_service = VEPService()

