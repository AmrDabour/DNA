"""
SNP Database Routes - Search and explore SNP information
"""
from flask import Blueprint, render_template, request, jsonify
from config.mongodb import get_snp_collection

snp_database_bp = Blueprint('snp_database', __name__)


@snp_database_bp.route('/snp-database')
def snp_database_page():
    """SNP Database search page"""
    return render_template('snp_database.html')


@snp_database_bp.route('/api/snp/search')
def search_snps():
    """Search SNP database"""
    try:
        collection = get_snp_collection()
        
        query = request.args.get('q', '').strip().lower()
        chromosome = request.args.get('chromosome', '')
        gene = request.args.get('gene', '').strip().lower()
        trait = request.args.get('trait', '').strip().lower()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Build MongoDB query
        mongo_query = {}
        or_conditions = []
        
        if query:
            or_conditions.append({
                '$or': [
                    {'rs_id': {'$regex': query, '$options': 'i'}},
                    {'gene_name': {'$regex': query, '$options': 'i'}},
                    {'gene_symbol': {'$regex': query, '$options': 'i'}},
                    {'description': {'$regex': query, '$options': 'i'}},
                    {'associated_traits': {'$regex': query, '$options': 'i'}}
                ]
            })
        
        if chromosome:
            mongo_query['chromosome'] = chromosome
        
        if gene:
            or_conditions.append({
                '$or': [
                    {'gene_name': {'$regex': gene, '$options': 'i'}},
                    {'gene_symbol': {'$regex': gene, '$options': 'i'}}
                ]
            })
        
        if trait:
            or_conditions.append({
                '$or': [
                    {'associated_traits': {'$regex': trait, '$options': 'i'}},
                    {'disease_associations': {'$regex': trait, '$options': 'i'}}
                ]
            })
        
        # Combine all conditions with $and if we have multiple OR conditions
        if or_conditions:
            if len(or_conditions) == 1:
                mongo_query.update(or_conditions[0])
            else:
                mongo_query['$and'] = or_conditions
        
        # Get total count
        total = collection.count_documents(mongo_query)
        
        # Pagination
        skip = (page - 1) * per_page
        cursor = collection.find(mongo_query).skip(skip).limit(per_page)
        
        # Convert to list and remove MongoDB _id field
        results = []
        for doc in cursor:
            doc.pop('_id', None)
            doc.pop('created_at', None)
            doc.pop('updated_at', None)
            results.append(doc)
        
        return jsonify({
            'success': True,
            'snps': results,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page if total > 0 else 0
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@snp_database_bp.route('/api/snp/<rs_id>')
def get_snp_info(rs_id):
    """Get detailed information about a specific SNP"""
    try:
        collection = get_snp_collection()
        
        # Normalize rs_id
        normalized_rs_id = rs_id.lower()
        if not normalized_rs_id.startswith('rs'):
            normalized_rs_id = f'rs{normalized_rs_id}'
        
        # Try exact match first
        snp = collection.find_one({'rs_id': normalized_rs_id})
        
        # If not found, try case-insensitive search
        if not snp:
            snp = collection.find_one({'rs_id': {'$regex': f'^{rs_id}$', '$options': 'i'}})
        
        if snp:
            # Remove MongoDB-specific fields
            snp.pop('_id', None)
            snp.pop('created_at', None)
            snp.pop('updated_at', None)
            
            return jsonify({
                'success': True,
                'snp': snp
            })
        
        return jsonify({
            'success': False,
            'error': f'SNP {rs_id} not found in database'
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@snp_database_bp.route('/api/snp/chromosomes')
def get_chromosomes():
    """Get list of chromosomes in database"""
    try:
        collection = get_snp_collection()
        
        # Get distinct chromosomes
        chromosomes = collection.distinct('chromosome')
        
        # Sort chromosomes (numeric first, then others)
        chromosomes = sorted(chromosomes, key=lambda x: int(x) if x.isdigit() else 99)
        
        return jsonify({
            'success': True,
            'chromosomes': chromosomes
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@snp_database_bp.route('/api/snp/genes')
def get_genes():
    """Get list of genes in database"""
    try:
        collection = get_snp_collection()
        
        # Get distinct gene symbols (filter out None/empty)
        genes = collection.distinct('gene_symbol')
        genes = [g for g in genes if g]  # Remove None/empty values
        genes = sorted(genes)
        
        return jsonify({
            'success': True,
            'genes': genes
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@snp_database_bp.route('/api/snp/traits')
def get_traits():
    """Get list of all traits and diseases in database"""
    try:
        collection = get_snp_collection()
        
        traits = set()
        diseases = set()
        
        # Iterate through all SNPs to collect traits and diseases
        for snp in collection.find({}, {'associated_traits': 1, 'disease_associations': 1}):
            if 'associated_traits' in snp:
                traits.update(snp['associated_traits'])
            if 'disease_associations' in snp:
                diseases.update(snp['disease_associations'])
        
        return jsonify({
            'success': True,
            'traits': sorted(traits),
            'diseases': sorted(diseases)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@snp_database_bp.route('/api/snp/stats')
def get_snp_stats():
    """Get statistics about the SNP database"""
    try:
        collection = get_snp_collection()
        
        total_snps = collection.count_documents({})
        chromosomes = len(collection.distinct('chromosome'))
        genes = len([g for g in collection.distinct('gene_symbol') if g])
        
        # Count unique traits and diseases
        traits = set()
        diseases = set()
        for snp in collection.find({}, {'associated_traits': 1, 'disease_associations': 1}):
            if 'associated_traits' in snp:
                traits.update(snp['associated_traits'])
            if 'disease_associations' in snp:
                diseases.update(snp['disease_associations'])
        
        return jsonify({
            'success': True,
            'stats': {
                'total_snps': total_snps,
                'chromosomes': chromosomes,
                'genes': genes,
                'traits': len(traits),
                'diseases': len(diseases)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
