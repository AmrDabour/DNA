"""
SNP Routes - REST API for SNP Database
Analysis Service Microservice
"""
from flask import Blueprint, request, jsonify
import os
import sys
from sqlalchemy import or_, func

snp_bp = Blueprint('snp', __name__)


# Helper function to get database models
def get_db_models():
    """Import and return database models"""
    from database import db, SNPInfo
    return db, SNPInfo


@snp_bp.route('/api/snp', methods=['GET'])
def list_snps():
    """
    List SNPs with pagination and filters
    
    GET /api/snp?page=1&per_page=50&chromosome=1&gene=BRCA1
    
    Returns: {"success": true, "snps": [...], "pagination": {...}}
    """
    try:
        db, SNPInfo = get_db_models()
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        per_page = min(per_page, 200)  # Max 200 per page
        
        # Filters
        chromosome = request.args.get('chromosome')
        gene = request.args.get('gene')
        
        # Build query
        query = SNPInfo.query
        
        if chromosome:
            query = query.filter(SNPInfo.chromosome == chromosome)
        
        if gene:
            query = query.filter(SNPInfo.gene.ilike(f'%{gene}%'))
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            "success": True,
            "snps": [s.to_dict() for s in pagination.items],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@snp_bp.route('/api/snp/<string:rs_id>', methods=['GET'])
def get_snp(rs_id):
    """
    Get SNP by RS ID
    
    GET /api/snp/rs12345
    
    Returns: {"success": true, "snp": {...}}
    """
    try:
        db, SNPInfo = get_db_models()
        
        # Normalize RS ID
        if not rs_id.lower().startswith('rs'):
            rs_id = f'rs{rs_id}'
        
        snp = SNPInfo.query.filter_by(rsid=rs_id.lower()).first()
        
        if not snp:
            return jsonify({
                "success": False,
                "error": f"SNP {rs_id} not found"
            }), 404
        
        return jsonify({
            "success": True,
            "snp": snp.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@snp_bp.route('/api/snp/chromosomes', methods=['GET'])
def get_chromosomes():
    """
    Get list of distinct chromosomes with SNPs
    
    GET /api/snp/chromosomes
    
    Returns: {"success": true, "chromosomes": [...]}
    """
    try:
        db, SNPInfo = get_db_models()
        
        # Get distinct chromosomes
        chromosomes = db.session.query(SNPInfo.chromosome)\
            .filter(SNPInfo.chromosome.isnot(None))\
            .distinct()\
            .order_by(SNPInfo.chromosome)\
            .all()
        
        # Extract chromosome values and sort properly
        chr_list = sorted([c[0] for c in chromosomes if c[0]], 
                         key=lambda x: (int(x) if x.isdigit() else 999, x))
        
        return jsonify({
            "success": True,
            "chromosomes": chr_list
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@snp_bp.route('/api/snp/genes', methods=['GET'])
def get_genes():
    """
    Get list of distinct genes with SNPs
    
    GET /api/snp/genes
    
    Returns: {"success": true, "genes": [...]}
    """
    try:
        db, SNPInfo = get_db_models()
        
        # Get distinct genes
        genes = db.session.query(SNPInfo.gene)\
            .filter(SNPInfo.gene.isnot(None))\
            .filter(SNPInfo.gene != '')\
            .distinct()\
            .order_by(SNPInfo.gene)\
            .limit(500)\
            .all()
        
        gene_list = [g[0] for g in genes if g[0]]
        
        return jsonify({
            "success": True,
            "genes": gene_list
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@snp_bp.route('/api/snp/search', methods=['GET'])
def search_snps():
    """
    Search SNPs
    
    GET /api/snp/search?q=BRCA&limit=20
    
    Returns: {"success": true, "snps": [...], "pagination": {...}}
    """
    try:
        db, SNPInfo = get_db_models()
        
        query_text = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        chromosome = request.args.get('chromosome', '').strip()
        gene = request.args.get('gene', '').strip()
        
        # Build query
        query = SNPInfo.query
        
        if query_text:
            query = query.filter(or_(
                SNPInfo.rsid.ilike(f'%{query_text}%'),
                SNPInfo.gene.ilike(f'%{query_text}%'),
                SNPInfo.phenotype.ilike(f'%{query_text}%'),
                SNPInfo.description.ilike(f'%{query_text}%')
            ))
        
        if chromosome:
            query = query.filter(SNPInfo.chromosome == chromosome)
        
        if gene:
            query = query.filter(SNPInfo.gene.ilike(f'%{gene}%'))
        
        # Paginate results
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            "success": True,
            "query": query_text,
            "snps": [s.to_dict() for s in pagination.items],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@snp_bp.route('/api/snp/batch', methods=['POST'])
def get_snps_batch():
    """
    Get multiple SNPs by RS IDs
    
    POST /api/snp/batch
    Body: {"rs_ids": ["rs12345", "rs67890"]}
    
    Returns: {"success": true, "snps": {...}}
    """
    try:
        db, SNPInfo = get_db_models()
        
        data = request.get_json() or {}
        rs_ids = data.get('rs_ids', [])
        
        if not rs_ids:
            return jsonify({
                "success": False,
                "error": "rs_ids array is required"
            }), 400
        
        # Normalize RS IDs
        normalized_ids = []
        for rs_id in rs_ids:
            if not rs_id.lower().startswith('rs'):
                rs_id = f'rs{rs_id}'
            normalized_ids.append(rs_id.lower())
        
        # Query SNPs using rsid column
        snps = SNPInfo.query.filter(SNPInfo.rsid.in_(normalized_ids)).all()
        
        # Build result dictionary
        result = {snp.rsid: snp.to_dict() for snp in snps}
        
        # Find missing SNPs
        found_ids = set(result.keys())
        missing = [rs_id for rs_id in normalized_ids if rs_id not in found_ids]
        
        return jsonify({
            "success": True,
            "snps": result,
            "found": len(result),
            "missing": missing
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@snp_bp.route('/api/snp/stats', methods=['GET'])
def get_snp_stats():
    """
    Get SNP database statistics
    
    GET /api/snp/stats
    
    Returns: {"success": true, "stats": {...}}
    """
    try:
        db, SNPInfo = get_db_models()
        
        stats = {
            "total_snps": SNPInfo.query.count(),
        }
        
        # Count unique chromosomes
        chr_count = db.session.query(func.count(func.distinct(SNPInfo.chromosome))).scalar()
        stats["chromosomes"] = chr_count or 0
        
        # Count unique genes
        gene_count = db.session.query(func.count(func.distinct(SNPInfo.gene)))\
            .filter(SNPInfo.gene.isnot(None))\
            .scalar()
        stats["genes"] = gene_count or 0
        
        # Count SNPs with phenotypes (traits)
        trait_count = db.session.query(func.count(SNPInfo.id))\
            .filter(SNPInfo.phenotype.isnot(None))\
            .scalar()
        stats["traits"] = trait_count or 0
        
        # Diseases (using phenotype as proxy)
        stats["diseases"] = 0  # Not available in current schema
        
        return jsonify({
            "success": True,
            "stats": stats
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@snp_bp.route('/api/snp/seed', methods=['POST'])
def seed_snp_database():
    """
    Seed the SNP database with sample data
    
    POST /api/snp/seed
    
    Returns: {"success": true, "message": "...", "count": ...}
    """
    try:
        db, SNPInfo = get_db_models()
        
        # Check if already seeded
        existing_count = SNPInfo.query.count()
        if existing_count > 0:
            return jsonify({
                "success": True,
                "message": f"Database already has {existing_count} SNPs",
                "count": existing_count
            }), 200
        
        # Sample SNP data for common genetic markers
        sample_snps = [
            {"rsid": "rs1426654", "chromosome": "15", "position": 48426484, "gene": "SLC24A5", "phenotype": "Skin pigmentation", "description": "Major determinant of skin color differences between Europeans and Africans", "risk_allele": "A", "normal_allele": "G"},
            {"rsid": "rs16891982", "chromosome": "5", "position": 33951693, "gene": "SLC45A2", "phenotype": "Skin pigmentation", "description": "Associated with skin, hair, and eye pigmentation", "risk_allele": "G", "normal_allele": "C"},
            {"rsid": "rs12913832", "chromosome": "15", "position": 28365618, "gene": "HERC2", "phenotype": "Eye color", "description": "Major determinant of blue vs brown eye color", "risk_allele": "A", "normal_allele": "G"},
            {"rsid": "rs1800407", "chromosome": "15", "position": 28230318, "gene": "OCA2", "phenotype": "Eye color", "description": "Associated with eye color variation", "risk_allele": "T", "normal_allele": "C"},
            {"rsid": "rs12896399", "chromosome": "14", "position": 92773663, "gene": "SLC24A4", "phenotype": "Hair color", "description": "Associated with blonde vs brown hair", "risk_allele": "T", "normal_allele": "G"},
            {"rsid": "rs1393350", "chromosome": "11", "position": 89011046, "gene": "TYR", "phenotype": "Eye color", "description": "Associated with eye color and freckling", "risk_allele": "A", "normal_allele": "G"},
            {"rsid": "rs12203592", "chromosome": "6", "position": 396321, "gene": "IRF4", "phenotype": "Hair color", "description": "Associated with hair color and freckling", "risk_allele": "T", "normal_allele": "C"},
            {"rsid": "rs1805007", "chromosome": "16", "position": 89919709, "gene": "MC1R", "phenotype": "Red hair", "description": "Associated with red hair and fair skin", "risk_allele": "T", "normal_allele": "C"},
            {"rsid": "rs1805008", "chromosome": "16", "position": 89919683, "gene": "MC1R", "phenotype": "Red hair", "description": "Associated with red hair and skin sensitivity", "risk_allele": "T", "normal_allele": "C"},
            {"rsid": "rs1805009", "chromosome": "16", "position": 89919746, "gene": "MC1R", "phenotype": "Red hair", "description": "Associated with red hair and fair skin", "risk_allele": "C", "normal_allele": "G"},
            {"rsid": "rs4988235", "chromosome": "2", "position": 136608646, "gene": "LCT", "phenotype": "Lactose intolerance", "description": "Determines ability to digest lactose in adulthood", "risk_allele": "A", "normal_allele": "G"},
            {"rsid": "rs182549", "chromosome": "2", "position": 136616754, "gene": "MCM6", "phenotype": "Lactose intolerance", "description": "Regulatory variant affecting lactase persistence", "risk_allele": "T", "normal_allele": "C"},
            {"rsid": "rs7574865", "chromosome": "2", "position": 191964633, "gene": "STAT4", "phenotype": "Autoimmune disease risk", "description": "Associated with rheumatoid arthritis and lupus risk", "risk_allele": "T", "normal_allele": "G"},
            {"rsid": "rs10488631", "chromosome": "7", "position": 128578301, "gene": "IRF5", "phenotype": "Autoimmune disease risk", "description": "Associated with lupus and rheumatoid arthritis", "risk_allele": "C", "normal_allele": "T"},
            {"rsid": "rs6457620", "chromosome": "6", "position": 32681631, "gene": "HLA-DQB1", "phenotype": "Celiac disease", "description": "Strong association with celiac disease risk", "risk_allele": "T", "normal_allele": "C"},
            {"rsid": "rs2187668", "chromosome": "6", "position": 32713862, "gene": "HLA-DQA1", "phenotype": "Celiac disease", "description": "Associated with celiac disease risk", "risk_allele": "T", "normal_allele": "C"},
            {"rsid": "rs9939609", "chromosome": "16", "position": 53820527, "gene": "FTO", "phenotype": "Obesity risk", "description": "Associated with increased BMI and obesity risk", "risk_allele": "A", "normal_allele": "T"},
            {"rsid": "rs17782313", "chromosome": "18", "position": 60183864, "gene": "MC4R", "phenotype": "Obesity risk", "description": "Associated with obesity and increased food intake", "risk_allele": "C", "normal_allele": "T"},
            {"rsid": "rs1801282", "chromosome": "3", "position": 12351626, "gene": "PPARG", "phenotype": "Type 2 diabetes", "description": "Associated with type 2 diabetes risk", "risk_allele": "G", "normal_allele": "C"},
            {"rsid": "rs5219", "chromosome": "11", "position": 17388025, "gene": "KCNJ11", "phenotype": "Type 2 diabetes", "description": "Associated with type 2 diabetes risk", "risk_allele": "T", "normal_allele": "C"},
            {"rsid": "rs7903146", "chromosome": "10", "position": 114758349, "gene": "TCF7L2", "phenotype": "Type 2 diabetes", "description": "Strongest genetic risk factor for type 2 diabetes", "risk_allele": "T", "normal_allele": "C"},
            {"rsid": "rs1801133", "chromosome": "1", "position": 11796321, "gene": "MTHFR", "phenotype": "Folate metabolism", "description": "Associated with homocysteine levels and folate metabolism", "risk_allele": "T", "normal_allele": "C"},
            {"rsid": "rs1801131", "chromosome": "1", "position": 11794419, "gene": "MTHFR", "phenotype": "Folate metabolism", "description": "Second common MTHFR variant affecting enzyme activity", "risk_allele": "C", "normal_allele": "A"},
            {"rsid": "rs1799945", "chromosome": "6", "position": 26091179, "gene": "HFE", "phenotype": "Hemochromatosis", "description": "Associated with iron overload disorder", "risk_allele": "G", "normal_allele": "C"},
            {"rsid": "rs1800562", "chromosome": "6", "position": 26093141, "gene": "HFE", "phenotype": "Hemochromatosis", "description": "Major mutation causing hereditary hemochromatosis", "risk_allele": "A", "normal_allele": "G"},
            {"rsid": "rs429358", "chromosome": "19", "position": 44908684, "gene": "APOE", "phenotype": "Alzheimer's disease", "description": "Part of APOE4 haplotype, major genetic risk factor for Alzheimer's", "risk_allele": "C", "normal_allele": "T"},
            {"rsid": "rs7412", "chromosome": "19", "position": 44908822, "gene": "APOE", "phenotype": "Alzheimer's disease", "description": "Part of APOE variants affecting Alzheimer's risk", "risk_allele": "T", "normal_allele": "C"},
            {"rsid": "rs334", "chromosome": "11", "position": 5227002, "gene": "HBB", "phenotype": "Sickle cell anemia", "description": "Causes sickle cell disease when homozygous", "risk_allele": "T", "normal_allele": "A"},
            {"rsid": "rs1799983", "chromosome": "7", "position": 150690079, "gene": "NOS3", "phenotype": "Cardiovascular disease", "description": "Associated with hypertension and cardiovascular disease", "risk_allele": "T", "normal_allele": "G"},
            {"rsid": "rs662", "chromosome": "7", "position": 95308134, "gene": "PON1", "phenotype": "Cardiovascular disease", "description": "Affects paraoxonase activity and heart disease risk", "risk_allele": "G", "normal_allele": "A"},
        ]
        
        # Insert sample SNPs
        for snp_data in sample_snps:
            snp = SNPInfo(**snp_data)
            db.session.add(snp)
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Seeded {len(sample_snps)} SNPs into database",
            "count": len(sample_snps)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
