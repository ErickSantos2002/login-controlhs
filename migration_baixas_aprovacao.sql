-- ============================================
-- MIGRAÇÃO: Sistema de Aprovação de Baixas
-- ============================================
-- Data: 2025-11-17
-- Descrição: Adiciona campos de aprovação/rejeição na tabela baixas
--            e integração com sistema de anexos
-- ============================================

BEGIN;

-- ============================================
-- 1. TABELA BAIXAS - NOVOS CAMPOS
-- ============================================

-- Campos de aprovação
ALTER TABLE baixas ADD COLUMN IF NOT EXISTS data_aprovacao TIMESTAMP WITH TIME ZONE NULL;
ALTER TABLE baixas ADD COLUMN IF NOT EXISTS observacoes TEXT NULL;

-- Campos de rejeição
ALTER TABLE baixas ADD COLUMN IF NOT EXISTS rejeitado_por INTEGER NULL;
ALTER TABLE baixas ADD COLUMN IF NOT EXISTS data_rejeicao TIMESTAMP WITH TIME ZONE NULL;
ALTER TABLE baixas ADD COLUMN IF NOT EXISTS motivo_rejeicao TEXT NULL;

-- Remover coluna documento_anexo (obsoleta - agora usa tabela anexos)
ALTER TABLE baixas DROP COLUMN IF EXISTS documento_anexo;

-- ============================================
-- 2. FOREIGN KEYS
-- ============================================

-- FK para rejeitado_por
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_baixas_rejeitado_por'
    ) THEN
        ALTER TABLE baixas
        ADD CONSTRAINT fk_baixas_rejeitado_por
        FOREIGN KEY (rejeitado_por)
        REFERENCES users(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE;
    END IF;
END $$;

-- ============================================
-- 3. TABELA ANEXOS - CAMPO BAIXA_ID
-- ============================================

-- Adicionar coluna baixa_id
ALTER TABLE anexos ADD COLUMN IF NOT EXISTS baixa_id INTEGER NULL;

-- FK para baixas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_anexos_baixa_id'
    ) THEN
        ALTER TABLE anexos
        ADD CONSTRAINT fk_anexos_baixa_id
        FOREIGN KEY (baixa_id)
        REFERENCES baixas(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE;
    END IF;
END $$;

-- ============================================
-- 4. COMENTÁRIOS PARA DOCUMENTAÇÃO
-- ============================================

COMMENT ON COLUMN baixas.aprovado_por IS 'ID do usuário que aprovou a baixa (Administrador)';
COMMENT ON COLUMN baixas.data_aprovacao IS 'Data e hora da aprovação da baixa';
COMMENT ON COLUMN baixas.observacoes IS 'Observações do aprovador sobre a baixa';
COMMENT ON COLUMN baixas.rejeitado_por IS 'ID do usuário que rejeitou a baixa (Administrador)';
COMMENT ON COLUMN baixas.data_rejeicao IS 'Data e hora da rejeição da baixa';
COMMENT ON COLUMN baixas.motivo_rejeicao IS 'Motivo da rejeição da baixa';

COMMENT ON COLUMN anexos.baixa_id IS 'ID da baixa à qual o anexo está vinculado (opcional)';

-- ============================================
-- 5. VERIFICAÇÕES E VALIDAÇÕES
-- ============================================

-- Adiciona constraint para garantir que anexo está vinculado a patrimonio OU baixa
-- (não ambos ao mesmo tempo)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_anexo_vinculo_unico'
    ) THEN
        ALTER TABLE anexos
        ADD CONSTRAINT chk_anexo_vinculo_unico
        CHECK (
            (patrimonio_id IS NOT NULL AND baixa_id IS NULL) OR
            (patrimonio_id IS NULL AND baixa_id IS NOT NULL) OR
            (patrimonio_id IS NULL AND baixa_id IS NULL)
        );
    END IF;
END $$;

-- ============================================
-- 6. ÍNDICES PARA PERFORMANCE
-- ============================================

CREATE INDEX IF NOT EXISTS idx_baixas_aprovado_por ON baixas(aprovado_por);
CREATE INDEX IF NOT EXISTS idx_baixas_rejeitado_por ON baixas(rejeitado_por);
CREATE INDEX IF NOT EXISTS idx_baixas_data_aprovacao ON baixas(data_aprovacao);
CREATE INDEX IF NOT EXISTS idx_baixas_data_rejeicao ON baixas(data_rejeicao);
CREATE INDEX IF NOT EXISTS idx_anexos_baixa_id ON anexos(baixa_id);

-- ============================================
-- 7. VISUALIZAÇÕES ÚTEIS (OPCIONAL)
-- ============================================

-- View para baixas pendentes
CREATE OR REPLACE VIEW vw_baixas_pendentes AS
SELECT
    b.*,
    p.nome as patrimonio_nome,
    p.numero_serie as patrimonio_numero_serie
FROM baixas b
JOIN patrimonios p ON b.patrimonio_id = p.id
WHERE b.aprovado_por IS NULL
  AND b.rejeitado_por IS NULL
ORDER BY b.data_baixa DESC;

-- View para baixas aprovadas
CREATE OR REPLACE VIEW vw_baixas_aprovadas AS
SELECT
    b.*,
    p.nome as patrimonio_nome,
    p.numero_serie as patrimonio_numero_serie,
    u.username as aprovador_username
FROM baixas b
JOIN patrimonios p ON b.patrimonio_id = p.id
LEFT JOIN users u ON b.aprovado_por = u.id
WHERE b.aprovado_por IS NOT NULL
ORDER BY b.data_aprovacao DESC;

-- View para baixas rejeitadas
CREATE OR REPLACE VIEW vw_baixas_rejeitadas AS
SELECT
    b.*,
    p.nome as patrimonio_nome,
    p.numero_serie as patrimonio_numero_serie,
    u.username as rejeitador_username
FROM baixas b
JOIN patrimonios p ON b.patrimonio_id = p.id
LEFT JOIN users u ON b.rejeitado_por = u.id
WHERE b.rejeitado_por IS NOT NULL
ORDER BY b.data_rejeicao DESC;

COMMIT;

-- ============================================
-- 8. VERIFICAÇÃO FINAL
-- ============================================

-- Verifica se todas as colunas foram criadas
DO $$
DECLARE
    missing_columns TEXT;
BEGIN
    SELECT string_agg(column_name, ', ')
    INTO missing_columns
    FROM (
        SELECT unnest(ARRAY[
            'data_aprovacao',
            'observacoes',
            'rejeitado_por',
            'data_rejeicao',
            'motivo_rejeicao'
        ]) AS column_name
    ) expected
    WHERE NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'baixas'
        AND column_name = expected.column_name
    );

    IF missing_columns IS NOT NULL THEN
        RAISE EXCEPTION 'Colunas não criadas na tabela baixas: %', missing_columns;
    END IF;

    -- Verifica baixa_id em anexos
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'anexos'
        AND column_name = 'baixa_id'
    ) THEN
        RAISE EXCEPTION 'Coluna baixa_id não criada na tabela anexos';
    END IF;

    RAISE NOTICE '✅ Migração concluída com sucesso!';
    RAISE NOTICE '✅ Todas as colunas foram criadas corretamente.';
    RAISE NOTICE '✅ Foreign keys configuradas.';
    RAISE NOTICE '✅ Índices criados.';
    RAISE NOTICE '✅ Views criadas: vw_baixas_pendentes, vw_baixas_aprovadas, vw_baixas_rejeitadas';
END $$;
