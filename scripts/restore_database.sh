#!/bin/bash

# ====================================
# SCRIPT DE RESTORE DE BACKUP
# ControlHS API - PostgreSQL Restore
# ====================================

# Verificar argumentos
if [ -z "$1" ]; then
    echo "Uso: $0 <arquivo_backup.sql.gz>"
    echo ""
    echo "Exemplo:"
    echo "  $0 /backups/controlhs/backup_controlhs_20250118_140530.sql.gz"
    echo ""
    exit 1
fi

BACKUP_FILE="$1"

# Verificar se arquivo existe
if [ ! -f "$BACKUP_FILE" ]; then
    echo "✗ Erro: Arquivo não encontrado: $BACKUP_FILE"
    exit 1
fi

# Configurações
DB_NAME="${DB_NAME:-controlhs}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "=========================================="
echo "ControlHS - Restore do Banco de Dados"
echo "=========================================="
echo "ATENÇÃO: Este processo irá SOBRESCREVER o banco de dados atual!"
echo ""
echo "Banco: $DB_NAME"
echo "Backup: $BACKUP_FILE"
echo ""
read -p "Tem certeza que deseja continuar? (digite 'sim' para confirmar): " CONFIRM

if [ "$CONFIRM" != "sim" ]; then
    echo "Operação cancelada."
    exit 0
fi

echo ""
echo "[1/4] Criando backup de segurança antes do restore..."
SAFETY_BACKUP="/tmp/controlhs_safety_backup_$(date +%Y%m%d_%H%M%S).sql"
if PGPASSWORD="$DB_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -F p \
    -f "$SAFETY_BACKUP"; then
    echo "✓ Backup de segurança criado: $SAFETY_BACKUP"
else
    echo "✗ Erro ao criar backup de segurança"
    exit 1
fi

echo "[2/4] Descomprimindo backup..."
TEMP_SQL="/tmp/controlhs_restore_$(date +%Y%m%d_%H%M%S).sql"
if gunzip -c "$BACKUP_FILE" > "$TEMP_SQL"; then
    echo "✓ Backup descomprimido"
else
    echo "✗ Erro ao descomprimir backup"
    exit 1
fi

echo "[3/4] Restaurando banco de dados..."
echo "  Desconectando usuários ativos..."
PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d postgres \
    -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '$DB_NAME' AND pid <> pg_backend_pid();" \
    > /dev/null 2>&1

echo "  Dropando banco atual..."
PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d postgres \
    -c "DROP DATABASE IF EXISTS $DB_NAME;" \
    > /dev/null 2>&1

echo "  Criando novo banco..."
PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d postgres \
    -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" \
    > /dev/null 2>&1

echo "  Importando dados..."
if PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -f "$TEMP_SQL" \
    > /dev/null 2>&1; then
    echo "✓ Dados restaurados com sucesso"
else
    echo "✗ Erro ao restaurar dados"
    echo "  Backup de segurança disponível em: $SAFETY_BACKUP"
    exit 1
fi

echo "[4/4] Limpando arquivos temporários..."
rm -f "$TEMP_SQL"
echo "✓ Arquivos temporários removidos"

echo ""
echo "=========================================="
echo "Restore concluído com sucesso!"
echo "=========================================="
echo "Backup de segurança: $SAFETY_BACKUP"
echo "(Este arquivo pode ser removido após validação)"
echo ""

exit 0
