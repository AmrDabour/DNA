"""
SNP Database Routes - Search and explore SNP information
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import current_user

snp_database_bp = Blueprint('snp_database', __name__)


# Common SNP database with detailed information
SNP_DATABASE = {
    'rs1426654': {
        'rs_id': 'rs1426654',
        'chromosome': '15',
        'position': 48426484,
        'gene_name': 'SLC24A5',
        'gene_symbol': 'SLC24A5',
        'ref_allele': 'G',
        'alt_allele': 'A',
        'minor_allele': 'A',
        'maf': 0.35,
        'function_class': 'missense',
        'clinical_significance': 'Benign',
        'associated_traits': ['Skin pigmentation', 'Eye color', 'Hair color'],
        'disease_associations': [],
        'risk_allele': 'A',
        'odds_ratio': None,
        'population_specific': 'Higher frequency in European populations',
        'description': 'Major contributor to light skin pigmentation in Europeans. The A allele is associated with lighter skin.',
        'source': 'dbSNP, GWAS Catalog'
    },
    'rs12913832': {
        'rs_id': 'rs12913832',
        'chromosome': '15',
        'position': 28365618,
        'gene_name': 'HERC2',
        'gene_symbol': 'HERC2',
        'ref_allele': 'A',
        'alt_allele': 'G',
        'minor_allele': 'G',
        'maf': 0.25,
        'function_class': 'regulatory',
        'clinical_significance': 'Benign',
        'associated_traits': ['Eye color', 'Blue eyes', 'Brown eyes'],
        'disease_associations': [],
        'risk_allele': 'G',
        'odds_ratio': None,
        'population_specific': 'Strong predictor of blue eye color',
        'description': 'Primary genetic determinant of blue vs brown eye color. The G allele is strongly associated with blue eyes.',
        'source': 'dbSNP, GWAS Catalog'
    },
    'rs16891982': {
        'rs_id': 'rs16891982',
        'chromosome': '5',
        'position': 33951693,
        'gene_name': 'SLC45A2',
        'gene_symbol': 'SLC45A2',
        'ref_allele': 'C',
        'alt_allele': 'G',
        'minor_allele': 'G',
        'maf': 0.28,
        'function_class': 'missense',
        'clinical_significance': 'Benign',
        'associated_traits': ['Skin pigmentation', 'Hair color'],
        'disease_associations': [],
        'risk_allele': 'G',
        'odds_ratio': None,
        'population_specific': 'European populations',
        'description': 'Associated with lighter skin and hair pigmentation in European populations.',
        'source': 'dbSNP, GWAS Catalog'
    },
    'rs1805007': {
        'rs_id': 'rs1805007',
        'chromosome': '16',
        'position': 89919709,
        'gene_name': 'MC1R',
        'gene_symbol': 'MC1R',
        'ref_allele': 'C',
        'alt_allele': 'T',
        'minor_allele': 'T',
        'maf': 0.08,
        'function_class': 'missense',
        'clinical_significance': 'Risk factor',
        'associated_traits': ['Red hair', 'Fair skin', 'Freckling'],
        'disease_associations': ['Melanoma susceptibility', 'Skin cancer risk'],
        'risk_allele': 'T',
        'odds_ratio': 2.4,
        'population_specific': 'Northern European, Irish, Scottish',
        'description': 'R151C variant of MC1R gene. Strongly associated with red hair, fair skin, and increased melanoma risk.',
        'source': 'dbSNP, ClinVar, GWAS Catalog'
    },
    'rs7495174': {
        'rs_id': 'rs7495174',
        'chromosome': '15',
        'position': 28344238,
        'gene_name': 'OCA2',
        'gene_symbol': 'OCA2',
        'ref_allele': 'G',
        'alt_allele': 'A',
        'minor_allele': 'A',
        'maf': 0.22,
        'function_class': 'intron',
        'clinical_significance': 'Benign',
        'associated_traits': ['Eye color', 'Hair color'],
        'disease_associations': [],
        'risk_allele': 'A',
        'odds_ratio': None,
        'population_specific': 'European populations',
        'description': 'Variant in OCA2 gene associated with blue eye color and lighter hair.',
        'source': 'dbSNP, GWAS Catalog'
    },
    'rs4988235': {
        'rs_id': 'rs4988235',
        'chromosome': '2',
        'position': 136608646,
        'gene_name': 'MCM6',
        'gene_symbol': 'MCM6',
        'ref_allele': 'G',
        'alt_allele': 'A',
        'minor_allele': 'A',
        'maf': 0.35,
        'function_class': 'regulatory',
        'clinical_significance': 'Benign',
        'associated_traits': ['Lactase persistence', 'Lactose tolerance'],
        'disease_associations': ['Lactose intolerance'],
        'risk_allele': 'G',
        'odds_ratio': None,
        'population_specific': 'Northern European populations',
        'description': 'Controls lactase persistence in adults. The A allele allows continued lactose digestion into adulthood.',
        'source': 'dbSNP, OMIM'
    },
    'rs1801133': {
        'rs_id': 'rs1801133',
        'chromosome': '1',
        'position': 11796321,
        'gene_name': 'MTHFR',
        'gene_symbol': 'MTHFR',
        'ref_allele': 'G',
        'alt_allele': 'A',
        'minor_allele': 'A',
        'maf': 0.30,
        'function_class': 'missense',
        'clinical_significance': 'Risk factor',
        'associated_traits': ['Folate metabolism'],
        'disease_associations': ['Neural tube defects', 'Cardiovascular disease', 'Homocysteinemia'],
        'risk_allele': 'A',
        'odds_ratio': 1.5,
        'population_specific': 'Higher in Mediterranean populations',
        'description': 'C677T polymorphism affecting folate metabolism. The A allele (T at DNA level) reduces enzyme activity.',
        'source': 'dbSNP, ClinVar, OMIM'
    },
    'rs429358': {
        'rs_id': 'rs429358',
        'chromosome': '19',
        'position': 44908684,
        'gene_name': 'APOE',
        'gene_symbol': 'APOE',
        'ref_allele': 'T',
        'alt_allele': 'C',
        'minor_allele': 'C',
        'maf': 0.15,
        'function_class': 'missense',
        'clinical_significance': 'Risk factor',
        'associated_traits': ['Lipid metabolism', 'Cholesterol levels'],
        'disease_associations': ['Alzheimer\'s disease', 'Cardiovascular disease', 'Hyperlipidemia'],
        'risk_allele': 'C',
        'odds_ratio': 3.7,
        'population_specific': 'All populations',
        'description': 'Part of APOE ε4 allele. Major genetic risk factor for late-onset Alzheimer\'s disease.',
        'source': 'dbSNP, ClinVar, GWAS Catalog'
    },
    'rs7412': {
        'rs_id': 'rs7412',
        'chromosome': '19',
        'position': 44908822,
        'gene_name': 'APOE',
        'gene_symbol': 'APOE',
        'ref_allele': 'C',
        'alt_allele': 'T',
        'minor_allele': 'T',
        'maf': 0.08,
        'function_class': 'missense',
        'clinical_significance': 'Protective',
        'associated_traits': ['Lipid metabolism'],
        'disease_associations': ['Alzheimer\'s disease (protective)', 'Cardiovascular disease'],
        'risk_allele': 'C',
        'odds_ratio': 0.6,
        'population_specific': 'All populations',
        'description': 'Part of APOE ε2 allele. The T allele may be protective against Alzheimer\'s disease.',
        'source': 'dbSNP, ClinVar, GWAS Catalog'
    },
    'rs334': {
        'rs_id': 'rs334',
        'chromosome': '11',
        'position': 5227002,
        'gene_name': 'HBB',
        'gene_symbol': 'HBB',
        'ref_allele': 'A',
        'alt_allele': 'T',
        'minor_allele': 'T',
        'maf': 0.05,
        'function_class': 'missense',
        'clinical_significance': 'Pathogenic',
        'associated_traits': ['Sickle cell trait', 'Malaria resistance'],
        'disease_associations': ['Sickle cell disease', 'Sickle cell anemia'],
        'risk_allele': 'T',
        'odds_ratio': None,
        'population_specific': 'African, Mediterranean, Middle Eastern populations',
        'description': 'Sickle cell mutation (E6V). Causes sickle cell disease in homozygotes, provides malaria resistance in heterozygotes.',
        'source': 'dbSNP, ClinVar, OMIM'
    },
    'rs1799971': {
        'rs_id': 'rs1799971',
        'chromosome': '6',
        'position': 154360797,
        'gene_name': 'OPRM1',
        'gene_symbol': 'OPRM1',
        'ref_allele': 'A',
        'alt_allele': 'G',
        'minor_allele': 'G',
        'maf': 0.12,
        'function_class': 'missense',
        'clinical_significance': 'Drug response',
        'associated_traits': ['Opioid sensitivity', 'Pain perception', 'Alcohol dependence'],
        'disease_associations': ['Opioid addiction susceptibility', 'Alcohol use disorder'],
        'risk_allele': 'G',
        'odds_ratio': 1.3,
        'population_specific': 'Variable across populations',
        'description': 'A118G variant affecting opioid receptor function. Influences pain sensitivity and addiction risk.',
        'source': 'dbSNP, PharmGKB'
    },
    'rs1800497': {
        'rs_id': 'rs1800497',
        'chromosome': '11',
        'position': 113400106,
        'gene_name': 'ANKK1',
        'gene_symbol': 'ANKK1',
        'ref_allele': 'G',
        'alt_allele': 'A',
        'minor_allele': 'A',
        'maf': 0.18,
        'function_class': 'missense',
        'clinical_significance': 'Risk factor',
        'associated_traits': ['Dopamine signaling', 'Reward processing'],
        'disease_associations': ['Addiction susceptibility', 'ADHD', 'Obesity'],
        'risk_allele': 'A',
        'odds_ratio': 1.4,
        'population_specific': 'All populations',
        'description': 'Taq1A polymorphism near DRD2 gene. Associated with reduced dopamine receptor density.',
        'source': 'dbSNP, GWAS Catalog'
    },
    'rs10774671': {
        'rs_id': 'rs10774671',
        'chromosome': '12',
        'position': 112919388,
        'gene_name': 'OAS1',
        'gene_symbol': 'OAS1',
        'ref_allele': 'G',
        'alt_allele': 'A',
        'minor_allele': 'A',
        'maf': 0.35,
        'function_class': 'splice_region',
        'clinical_significance': 'Risk factor',
        'associated_traits': ['Antiviral response'],
        'disease_associations': ['COVID-19 severity', 'Viral infections'],
        'risk_allele': 'G',
        'odds_ratio': 1.6,
        'population_specific': 'All populations',
        'description': 'Affects OAS1 enzyme activity involved in antiviral defense. Associated with COVID-19 susceptibility.',
        'source': 'dbSNP, GWAS Catalog'
    },
    'rs6983267': {
        'rs_id': 'rs6983267',
        'chromosome': '8',
        'position': 128413305,
        'gene_name': 'CCAT2',
        'gene_symbol': 'CCAT2',
        'ref_allele': 'G',
        'alt_allele': 'T',
        'minor_allele': 'T',
        'maf': 0.48,
        'function_class': 'regulatory',
        'clinical_significance': 'Risk factor',
        'associated_traits': ['Cancer susceptibility'],
        'disease_associations': ['Colorectal cancer', 'Prostate cancer', 'Breast cancer'],
        'risk_allele': 'G',
        'odds_ratio': 1.27,
        'population_specific': 'All populations',
        'description': 'Located in a cancer susceptibility locus. The G allele increases risk of several cancer types.',
        'source': 'dbSNP, GWAS Catalog'
    },
    'rs1229984': {
        'rs_id': 'rs1229984',
        'chromosome': '4',
        'position': 99318162,
        'gene_name': 'ADH1B',
        'gene_symbol': 'ADH1B',
        'ref_allele': 'G',
        'alt_allele': 'A',
        'minor_allele': 'A',
        'maf': 0.25,
        'function_class': 'missense',
        'clinical_significance': 'Protective',
        'associated_traits': ['Alcohol metabolism', 'Alcohol flushing'],
        'disease_associations': ['Alcohol use disorder (protective)'],
        'risk_allele': 'G',
        'odds_ratio': 0.4,
        'population_specific': 'High frequency in East Asian populations',
        'description': 'His48Arg variant causing rapid alcohol metabolism. The A allele causes alcohol flush reaction and is protective against alcoholism.',
        'source': 'dbSNP, PharmGKB'
    },
    'rs762551': {
        'rs_id': 'rs762551',
        'chromosome': '15',
        'position': 75041917,
        'gene_name': 'CYP1A2',
        'gene_symbol': 'CYP1A2',
        'ref_allele': 'A',
        'alt_allele': 'C',
        'minor_allele': 'C',
        'maf': 0.32,
        'function_class': 'intron',
        'clinical_significance': 'Drug response',
        'associated_traits': ['Caffeine metabolism', 'Coffee consumption'],
        'disease_associations': ['Heart attack risk with high caffeine intake'],
        'risk_allele': 'A',
        'odds_ratio': 1.6,
        'population_specific': 'All populations',
        'description': 'Determines fast vs slow caffeine metabolism. The C allele is associated with fast caffeine metabolism.',
        'source': 'dbSNP, PharmGKB'
    },
    'rs1815739': {
        'rs_id': 'rs1815739',
        'chromosome': '11',
        'position': 66560624,
        'gene_name': 'ACTN3',
        'gene_symbol': 'ACTN3',
        'ref_allele': 'C',
        'alt_allele': 'T',
        'minor_allele': 'T',
        'maf': 0.42,
        'function_class': 'stop_gained',
        'clinical_significance': 'Benign',
        'associated_traits': ['Muscle performance', 'Athletic ability', 'Sprint performance'],
        'disease_associations': [],
        'risk_allele': None,
        'odds_ratio': None,
        'population_specific': 'All populations',
        'description': 'R577X variant. The C allele produces functional alpha-actinin-3 protein associated with sprint/power performance.',
        'source': 'dbSNP, GWAS Catalog'
    },
    'rs4680': {
        'rs_id': 'rs4680',
        'chromosome': '22',
        'position': 19963748,
        'gene_name': 'COMT',
        'gene_symbol': 'COMT',
        'ref_allele': 'G',
        'alt_allele': 'A',
        'minor_allele': 'A',
        'maf': 0.48,
        'function_class': 'missense',
        'clinical_significance': 'Benign',
        'associated_traits': ['Dopamine metabolism', 'Pain sensitivity', 'Stress response', 'Memory'],
        'disease_associations': ['Anxiety', 'ADHD', 'Schizophrenia risk'],
        'risk_allele': None,
        'odds_ratio': None,
        'population_specific': 'All populations',
        'description': 'Val158Met polymorphism. The A allele (Met) results in slower dopamine breakdown and better executive function.',
        'source': 'dbSNP, GWAS Catalog'
    },
    'rs1801282': {
        'rs_id': 'rs1801282',
        'chromosome': '3',
        'position': 12393125,
        'gene_name': 'PPARG',
        'gene_symbol': 'PPARG',
        'ref_allele': 'C',
        'alt_allele': 'G',
        'minor_allele': 'G',
        'maf': 0.12,
        'function_class': 'missense',
        'clinical_significance': 'Protective',
        'associated_traits': ['Insulin sensitivity', 'Fat metabolism'],
        'disease_associations': ['Type 2 diabetes (protective)', 'Obesity'],
        'risk_allele': 'C',
        'odds_ratio': 0.86,
        'population_specific': 'All populations',
        'description': 'Pro12Ala variant. The G allele (Ala) is protective against type 2 diabetes and improves insulin sensitivity.',
        'source': 'dbSNP, ClinVar, GWAS Catalog'
    },
    'rs9939609': {
        'rs_id': 'rs9939609',
        'chromosome': '16',
        'position': 53820527,
        'gene_name': 'FTO',
        'gene_symbol': 'FTO',
        'ref_allele': 'T',
        'alt_allele': 'A',
        'minor_allele': 'A',
        'maf': 0.42,
        'function_class': 'intron',
        'clinical_significance': 'Risk factor',
        'associated_traits': ['Body mass index', 'Obesity', 'Food intake'],
        'disease_associations': ['Obesity', 'Type 2 diabetes'],
        'risk_allele': 'A',
        'odds_ratio': 1.67,
        'population_specific': 'All populations',
        'description': 'Major obesity-associated variant. The A allele increases BMI and obesity risk.',
        'source': 'dbSNP, GWAS Catalog'
    },
    'rs53576': {
        'rs_id': 'rs53576',
        'chromosome': '3',
        'position': 8762685,
        'gene_name': 'OXTR',
        'gene_symbol': 'OXTR',
        'ref_allele': 'G',
        'alt_allele': 'A',
        'minor_allele': 'A',
        'maf': 0.38,
        'function_class': 'intron',
        'clinical_significance': 'Benign',
        'associated_traits': ['Social behavior', 'Empathy', 'Social bonding'],
        'disease_associations': ['Autism spectrum (associated)', 'Social anxiety'],
        'risk_allele': 'A',
        'odds_ratio': None,
        'population_specific': 'All populations',
        'description': 'Oxytocin receptor variant. The G allele is associated with increased empathy and social skills.',
        'source': 'dbSNP, GWAS Catalog'
    },
    'rs2228570': {
        'rs_id': 'rs2228570',
        'chromosome': '12',
        'position': 48272895,
        'gene_name': 'VDR',
        'gene_symbol': 'VDR',
        'ref_allele': 'C',
        'alt_allele': 'T',
        'minor_allele': 'T',
        'maf': 0.37,
        'function_class': 'start_lost',
        'clinical_significance': 'Risk factor',
        'associated_traits': ['Vitamin D metabolism', 'Bone density'],
        'disease_associations': ['Osteoporosis', 'Autoimmune diseases', 'Cancer risk'],
        'risk_allele': 'T',
        'odds_ratio': 1.2,
        'population_specific': 'All populations',
        'description': 'FokI polymorphism affecting vitamin D receptor. The C allele is associated with better vitamin D function.',
        'source': 'dbSNP, GWAS Catalog'
    },
    'rs1800562': {
        'rs_id': 'rs1800562',
        'chromosome': '6',
        'position': 26092913,
        'gene_name': 'HFE',
        'gene_symbol': 'HFE',
        'ref_allele': 'G',
        'alt_allele': 'A',
        'minor_allele': 'A',
        'maf': 0.06,
        'function_class': 'missense',
        'clinical_significance': 'Pathogenic',
        'associated_traits': ['Iron metabolism', 'Iron absorption'],
        'disease_associations': ['Hereditary hemochromatosis', 'Iron overload'],
        'risk_allele': 'A',
        'odds_ratio': None,
        'population_specific': 'Northern European populations',
        'description': 'C282Y mutation. Major cause of hereditary hemochromatosis leading to excessive iron absorption.',
        'source': 'dbSNP, ClinVar, OMIM'
    },
    'rs5219': {
        'rs_id': 'rs5219',
        'chromosome': '11',
        'position': 17409572,
        'gene_name': 'KCNJ11',
        'gene_symbol': 'KCNJ11',
        'ref_allele': 'C',
        'alt_allele': 'T',
        'minor_allele': 'T',
        'maf': 0.35,
        'function_class': 'missense',
        'clinical_significance': 'Risk factor',
        'associated_traits': ['Insulin secretion', 'Glucose metabolism'],
        'disease_associations': ['Type 2 diabetes'],
        'risk_allele': 'T',
        'odds_ratio': 1.14,
        'population_specific': 'All populations',
        'description': 'E23K variant affecting pancreatic beta cell function and insulin secretion.',
        'source': 'dbSNP, GWAS Catalog'
    },
    'rs1333049': {
        'rs_id': 'rs1333049',
        'chromosome': '9',
        'position': 22125504,
        'gene_name': 'CDKN2A/CDKN2B',
        'gene_symbol': 'CDKN2A',
        'ref_allele': 'C',
        'alt_allele': 'G',
        'minor_allele': 'G',
        'maf': 0.48,
        'function_class': 'intergenic',
        'clinical_significance': 'Risk factor',
        'associated_traits': ['Cardiovascular health'],
        'disease_associations': ['Coronary artery disease', 'Heart attack', 'Stroke'],
        'risk_allele': 'G',
        'odds_ratio': 1.29,
        'population_specific': 'All populations',
        'description': 'Major cardiovascular disease risk locus. The G allele increases risk of coronary artery disease.',
        'source': 'dbSNP, GWAS Catalog'
    },
    'rs6265': {
        'rs_id': 'rs6265',
        'chromosome': '11',
        'position': 27679916,
        'gene_name': 'BDNF',
        'gene_symbol': 'BDNF',
        'ref_allele': 'C',
        'alt_allele': 'T',
        'minor_allele': 'T',
        'maf': 0.20,
        'function_class': 'missense',
        'clinical_significance': 'Risk factor',
        'associated_traits': ['Neuroplasticity', 'Memory', 'Learning'],
        'disease_associations': ['Depression', 'Anxiety', 'Alzheimer\'s disease', 'Schizophrenia'],
        'risk_allele': 'T',
        'odds_ratio': 1.2,
        'population_specific': 'All populations',
        'description': 'Val66Met polymorphism. The T allele (Met) affects brain-derived neurotrophic factor secretion and memory.',
        'source': 'dbSNP, GWAS Catalog'
    },
    'rs1042713': {
        'rs_id': 'rs1042713',
        'chromosome': '5',
        'position': 148826877,
        'gene_name': 'ADRB2',
        'gene_symbol': 'ADRB2',
        'ref_allele': 'A',
        'alt_allele': 'G',
        'minor_allele': 'G',
        'maf': 0.38,
        'function_class': 'missense',
        'clinical_significance': 'Drug response',
        'associated_traits': ['Beta-blocker response', 'Exercise performance'],
        'disease_associations': ['Asthma', 'COPD', 'Obesity'],
        'risk_allele': None,
        'odds_ratio': None,
        'population_specific': 'All populations',
        'description': 'Gly16Arg variant in beta-2 adrenergic receptor. Affects response to asthma medications and exercise capacity.',
        'source': 'dbSNP, PharmGKB'
    },
    'rs1695': {
        'rs_id': 'rs1695',
        'chromosome': '11',
        'position': 67585218,
        'gene_name': 'GSTP1',
        'gene_symbol': 'GSTP1',
        'ref_allele': 'A',
        'alt_allele': 'G',
        'minor_allele': 'G',
        'maf': 0.32,
        'function_class': 'missense',
        'clinical_significance': 'Risk factor',
        'associated_traits': ['Detoxification', 'Drug metabolism'],
        'disease_associations': ['Cancer susceptibility', 'Chemotherapy response'],
        'risk_allele': 'G',
        'odds_ratio': 1.15,
        'population_specific': 'All populations',
        'description': 'Ile105Val variant affecting glutathione S-transferase activity and cancer drug response.',
        'source': 'dbSNP, PharmGKB'
    },
    'rs7903146': {
        'rs_id': 'rs7903146',
        'chromosome': '10',
        'position': 112998590,
        'gene_name': 'TCF7L2',
        'gene_symbol': 'TCF7L2',
        'ref_allele': 'C',
        'alt_allele': 'T',
        'minor_allele': 'T',
        'maf': 0.28,
        'function_class': 'intron',
        'clinical_significance': 'Risk factor',
        'associated_traits': ['Glucose metabolism', 'Insulin secretion'],
        'disease_associations': ['Type 2 diabetes'],
        'risk_allele': 'T',
        'odds_ratio': 1.45,
        'population_specific': 'All populations',
        'description': 'Strongest common genetic risk factor for type 2 diabetes. The T allele impairs insulin secretion.',
        'source': 'dbSNP, GWAS Catalog'
    }
}


@snp_database_bp.route('/snp-database')
def snp_database_page():
    """SNP Database search page"""
    return render_template('snp_database.html')


@snp_database_bp.route('/api/snp/search')
def search_snps():
    """Search SNP database"""
    query = request.args.get('q', '').strip().lower()
    chromosome = request.args.get('chromosome', '')
    gene = request.args.get('gene', '').strip().lower()
    trait = request.args.get('trait', '').strip().lower()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    results = []
    
    for rs_id, snp in SNP_DATABASE.items():
        # Check if SNP matches search criteria
        matches = True
        
        if query:
            query_match = (
                query in snp['rs_id'].lower() or
                query in snp.get('gene_name', '').lower() or
                query in snp.get('gene_symbol', '').lower() or
                query in snp.get('description', '').lower() or
                any(query in trait.lower() for trait in snp.get('associated_traits', []))
            )
            if not query_match:
                matches = False
        
        if chromosome and snp['chromosome'] != chromosome:
            matches = False
        
        if gene and gene not in snp.get('gene_name', '').lower() and gene not in snp.get('gene_symbol', '').lower():
            matches = False
        
        if trait:
            trait_match = any(trait in t.lower() for t in snp.get('associated_traits', []))
            disease_match = any(trait in d.lower() for d in snp.get('disease_associations', []))
            if not trait_match and not disease_match:
                matches = False
        
        if matches:
            results.append(snp)
    
    # Pagination
    total = len(results)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_results = results[start:end]
    
    return jsonify({
        'success': True,
        'snps': paginated_results,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    })


@snp_database_bp.route('/api/snp/<rs_id>')
def get_snp_info(rs_id):
    """Get detailed information about a specific SNP"""
    snp = SNP_DATABASE.get(rs_id.lower()) or SNP_DATABASE.get(rs_id)
    
    if not snp:
        # Try to find with 'rs' prefix
        if not rs_id.startswith('rs'):
            snp = SNP_DATABASE.get(f'rs{rs_id}')
    
    if snp:
        return jsonify({
            'success': True,
            'snp': snp
        })
    
    return jsonify({
        'success': False,
        'error': f'SNP {rs_id} not found in database'
    }), 404


@snp_database_bp.route('/api/snp/chromosomes')
def get_chromosomes():
    """Get list of chromosomes in database"""
    chromosomes = sorted(set(snp['chromosome'] for snp in SNP_DATABASE.values()), 
                         key=lambda x: int(x) if x.isdigit() else 99)
    return jsonify({
        'success': True,
        'chromosomes': chromosomes
    })


@snp_database_bp.route('/api/snp/genes')
def get_genes():
    """Get list of genes in database"""
    genes = sorted(set(snp['gene_symbol'] for snp in SNP_DATABASE.values() if snp.get('gene_symbol')))
    return jsonify({
        'success': True,
        'genes': genes
    })


@snp_database_bp.route('/api/snp/traits')
def get_traits():
    """Get list of all traits and diseases in database"""
    traits = set()
    diseases = set()
    
    for snp in SNP_DATABASE.values():
        traits.update(snp.get('associated_traits', []))
        diseases.update(snp.get('disease_associations', []))
    
    return jsonify({
        'success': True,
        'traits': sorted(traits),
        'diseases': sorted(diseases)
    })


@snp_database_bp.route('/api/snp/stats')
def get_snp_stats():
    """Get statistics about the SNP database"""
    total_snps = len(SNP_DATABASE)
    chromosomes = len(set(snp['chromosome'] for snp in SNP_DATABASE.values()))
    genes = len(set(snp['gene_symbol'] for snp in SNP_DATABASE.values() if snp.get('gene_symbol')))
    
    traits = set()
    diseases = set()
    for snp in SNP_DATABASE.values():
        traits.update(snp.get('associated_traits', []))
        diseases.update(snp.get('disease_associations', []))
    
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