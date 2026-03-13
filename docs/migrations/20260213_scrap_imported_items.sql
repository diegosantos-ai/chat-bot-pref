-- ========================================
-- TABELA: scrap_imported_items - 13/02/2026
-- ========================================
-- Rastrear itens importados para deduplicação

CREATE TABLE scrap_imported_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id       UUID REFERENCES scrap_configs(id) ON DELETE CASCADE,
    result_id       UUID REFERENCES scrap_results(id) ON DELETE CASCADE,
    item_hash       VARCHAR(64) NOT NULL,
    item_title      TEXT,
    item_url        TEXT,
    imported_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_scrap_imported_items_config ON scrap_imported_items(config_id);
CREATE INDEX idx_scrap_imported_items_hash ON scrap_imported_items(item_hash);
CREATE INDEX idx_scrap_imported_items_result ON scrap_imported_items(result_id);

COMMENT ON TABLE scrap_imported_items IS 'Itens já importados para evitar duplicatas';
COMMENT ON COLUMN scrap_imported_items.item_hash IS 'Hash MD5/SHA do item para dedup';
COMMENT ON COLUMN scrap_imported_items.item_url IS 'URL do item original';
