#!/bin/bash

# ====================================
# SCRIPT DE BACKUP AUTOMÁTICO
# ControlHS API - PostgreSQL Backup
# ====================================

# Configurações (ou ler do .env)
BACKUP_DIR="${BACKUP_DIR:-/backups/controlhs}"
DB_NAME="${DB_NAME:-controlhs}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# Criar diretório de backup se não existir
mkdir -p "$BACKUP_DIR"

# Nome do arquivo com timestamp
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_${DB_NAME}_${DATE}.sql"
BACKUP_FILE_GZ="$BACKUP_FILE.gz"

echo "=========================================="
echo "ControlHS - Backup do Banco de Dados"
echo "=========================================="
echo "Data/Hora: $(date)"
echo "Banco: $DB_NAME"
echo "Arquivo: $BACKUP_FILE_GZ"
echo ""

# Executar backup
echo "[1/4] Iniciando backup..."
if PGPASSWORD="$DB_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -F p \
    -f "$BACKUP_FILE"; then
    echo "✓ Backup criado com sucesso"
else
    echo "✗ Erro ao criar backup"
    exit 1
fi

# Comprimir backup
echo "[2/4] Comprimindo backup..."
if gzip "$BACKUP_FILE"; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE_GZ" | cut -f1)
    echo "✓ Backup comprimido: $BACKUP_SIZE"
else
    echo "✗ Erro ao comprimir backup"
    exit 1
fi

# Limpar backups antigos
echo "[3/4] Removendo backups antigos (>${RETENTION_DAYS} dias)..."
REMOVED=$(find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
echo "✓ Removidos $REMOVED backups antigos"

# Listar backups existentes
echo "[4/4] Backups disponíveis:"
ls -lh "$BACKUP_DIR"/backup_*.sql.gz | tail -n 5

echo ""
echo "=========================================="
echo "Backup concluído com sucesso!"
echo "=========================================="
echo "Arquivo: $BACKUP_FILE_GZ"
echo "Tamanho: $BACKUP_SIZE"
echo ""

# Log
echo "$(date): Backup realizado - $BACKUP_FILE_GZ ($BACKUP_SIZE)" >> "$BACKUP_DIR/backup.log"

exit 0
