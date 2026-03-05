-- Create indexes for boost_configs
CREATE INDEX IF NOT EXISTS idx_boost_configs_tipo ON boost_configs(tipo);
CREATE INDEX IF NOT EXISTS idx_boost_configs_ativo ON boost_configs(ativo) WHERE ativo = TRUE;

-- Check if we need to import acronyms
DO $$
DECLARE
    cnt INTEGER;
BEGIN
    SELECT COUNT(*) INTO cnt FROM boost_configs WHERE tipo = 'sigla';
    
    IF cnt = 0 THEN
        -- Import acronyms from the hardcoded file
        INSERT INTO boost_configs (nome, tipo, valor, boost_value, prioridade, ativo) VALUES
            ('REFIS', 'sigla', 'REFIS', 0.2, 1, true),
            ('IPTU', 'sigla', 'IPTU', 0.2, 2, true),
            ('ITBI', 'sigla', 'ITBI', 0.2, 3, true),
            ('ISS', 'sigla', 'ISS', 0.2, 4, true),
            ('ICMS', 'sigla', 'ICMS', 0.2, 5, true),
            ('NFS-E', 'sigla', 'NFS-E', 0.2, 6, true),
            ('NFS', 'sigla', 'NFS', 0.2, 7, true),
            ('NF-E', 'sigla', 'NF-E', 0.2, 8, true),
            ('NFE', 'sigla', 'NFE', 0.2, 9, true),
            ('DAS', 'sigla', 'DAS', 0.2, 10, true),
            ('DASN', 'sigla', 'DASN', 0.2, 11, true),
            ('DASN-SIMEI', 'sigla', 'DASN-SIMEI', 0.2, 12, true),
            ('CCMEI', 'sigla', 'CCMEI', 0.2, 13, true),
            ('PGMEI', 'sigla', 'PGMEI', 0.2, 14, true),
            ('MEI', 'sigla', 'MEI', 0.2, 15, true),
            ('CNPJ', 'sigla', 'CNPJ', 0.2, 16, true),
            ('CPF', 'sigla', 'CPF', 0.2, 17, true),
            ('ME', 'sigla', 'ME', 0.2, 18, true),
            ('EPP', 'sigla', 'EPP', 0.2, 19, true),
            ('SEBRAE', 'sigla', 'SEBRAE', 0.2, 20, true),
            ('JUCEPAR', 'sigla', 'JUCEPAR', 0.2, 21, true),
            ('SUS', 'sigla', 'SUS', 0.2, 22, true),
            ('PSF', 'sigla', 'PSF', 0.2, 23, true),
            ('UBS', 'sigla', 'UBS', 0.2, 24, true),
            ('UBSF', 'sigla', 'UBSF', 0.2, 25, true),
            ('PA', 'sigla', 'PA', 0.2, 26, true),
            ('NASF', 'sigla', 'NASF', 0.2, 27, true),
            ('CEO', 'sigla', 'CEO', 0.2, 28, true),
            ('CAPS', 'sigla', 'CAPS', 0.2, 29, true),
            ('SAMU', 'sigla', 'SAMU', 0.2, 30, true),
            ('CRAS', 'sigla', 'CRAS', 0.2, 31, true),
            ('CADUNICO', 'sigla', 'CADUNICO', 0.2, 32, true),
            ('CADÚNICO', 'sigla', 'CADÚNICO', 0.2, 33, true),
            ('BPC', 'sigla', 'BPC', 0.2, 34, true),
            ('LOAS', 'sigla', 'LOAS', 0.2, 35, true),
            ('BPC/LOAS', 'sigla', 'BPC/LOAS', 0.2, 36, true),
            ('INSS', 'sigla', 'INSS', 0.2, 37, true),
            ('CMEI', 'sigla', 'CMEI', 0.2, 38, true),
            ('CEI', 'sigla', 'CEI', 0.2, 39, true),
            ('NEE', 'sigla', 'NEE', 0.2, 40, true),
            ('DETRAN', 'sigla', 'DETRAN', 0.2, 41, true),
            ('CIRETRAN', 'sigla', 'CIRETRAN', 0.2, 42, true),
            ('CONTRAN', 'sigla', 'CONTRAN', 0.2, 43, true),
            ('JARI', 'sigla', 'JARI', 0.2, 44, true),
            ('COSIP', 'sigla', 'COSIP', 0.2, 45, true),
            ('COPEL', 'sigla', 'COPEL', 0.2, 46, true),
            ('PPA', 'sigla', 'PPA', 0.2, 47, true),
            ('LOA', 'sigla', 'LOA', 0.2, 48, true),
            ('LDO', 'sigla', 'LDO', 0.2, 49, true),
            ('PM', 'sigla', 'PM', 0.2, 50, true),
            ('BM', 'sigla', 'BM', 0.2, 51, true);
        
        RAISE NOTICE 'Imported 51 acronyms';
    ELSE
        RAISE NOTICE 'Already have % acronyms, skipping import', cnt;
    END IF;
END $$;
