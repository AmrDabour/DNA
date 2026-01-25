
def improved_encoding(genotype_data, verbose=False):
    if verbose:
        print(f"Encoding genotype data of shape {genotype_data.shape}")
    
    # Ensure we have an even number of columns (pairs of alleles)
    if genotype_data.shape[1] % 2 != 0:
        raise ValueError(f"Genotype data must have an even number of columns, got {genotype_data.shape[1]}")
    
    import numpy as np
    encoded_data = np.zeros((genotype_data.shape[0], genotype_data.shape[1] // 2), dtype=np.float32)
    
    for i in range(0, genotype_data.shape[1], 2):
        allele1 = genotype_data[:, i]
        allele2 = genotype_data[:, i+1]
        snp_idx = i // 2
        
        unique_alleles, counts = np.unique(np.concatenate([allele1, allele2]), return_counts=True)
        
        if len(unique_alleles) > 0:
            ref_allele = unique_alleles[np.argmax(counts)]
            
            alt_count = np.zeros(allele1.shape[0], dtype=np.float32)
            alt_count += (allele1 != ref_allele) & (allele1 != '0')
            alt_count += (allele2 != ref_allele) & (allele2 != '0')
            
            encoded_data[:, snp_idx] = alt_count
    
    if verbose:
        print("Encoding complete.")
        print(f"Encoded data shape: {encoded_data.shape}")
    
    return encoded_data
