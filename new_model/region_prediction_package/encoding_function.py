
def improved_encoding(genotype_data, verbose=False):
    """Improved encoding for genetic data with validation and diagnostics"""
    if verbose:
        print(f"Encoding genotype data of shape {genotype_data.shape}")
    
    # Ensure we have an even number of columns (pairs of alleles)
    if genotype_data.shape[1] % 2 != 0:
        raise ValueError(f"Genotype data must have an even number of columns, got {genotype_data.shape[1]}")
    
    import numpy as np
    encoded_data = np.zeros((genotype_data.shape[0], genotype_data.shape[1] // 2), dtype=np.float32)
    
    # Count allele statistics for validation
    unique_allele_counts = {}
    
    for i in range(0, genotype_data.shape[1], 2):
        allele1 = genotype_data[:, i]
        allele2 = genotype_data[:, i+1]
        snp_idx = i // 2
        
        # Count allele types for this SNP
        all_alleles = np.concatenate([allele1, allele2])
        unique_alleles, counts = np.unique(all_alleles, return_counts=True)
        
        # Store allele distribution for diagnostics
        for ua, count in zip(unique_alleles, counts):
            if ua not in unique_allele_counts:
                unique_allele_counts[ua] = 0
            unique_allele_counts[ua] += count
        
        if len(unique_alleles) > 0:
            ref_allele = unique_alleles[np.argmax(counts)]
            
            alt_count = np.zeros(allele1.shape[0], dtype=np.float32)
            alt_count += (allele1 != ref_allele) & (allele1 != '0')
            alt_count += (allele2 != ref_allele) & (allele2 != '0')
            
            encoded_data[:, snp_idx] = alt_count
    
    if verbose:
        print("Encoding complete.")
        print(f"Encoded data shape: {encoded_data.shape}")
        
        # Show allele statistics if requested
        if verbose > 1:
            print("Allele statistics:")
            for allele, count in sorted(unique_allele_counts.items()):
                print(f"  Allele '{allele}': {count} occurrences")
    
    return encoded_data
