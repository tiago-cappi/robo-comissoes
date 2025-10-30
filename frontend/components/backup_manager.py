"""
Gerenciador de Backups.
Gerencia backups automáticos dos arquivos de regras.
"""

import streamlit as st
from pathlib import Path
from datetime import datetime
import shutil
from typing import List, Optional


class BackupManager:
    """Gerencia backups de arquivos Excel."""

    def __init__(self, backup_dir: Path):
        """
        Inicializa o gerenciador de backups.

        Args:
            backup_dir: Diretório onde os backups serão salvos
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True, parents=True)

    def create_backup(self, file_path: Path, prefix: str = "backup") -> Optional[Path]:
        """
        Cria um backup de um arquivo.

        Args:
            file_path: Caminho do arquivo original
            prefix: Prefixo para o nome do backup

        Returns:
            Path do backup criado ou None em caso de erro
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{prefix}_{timestamp}{file_path.suffix}"
            backup_path = self.backup_dir / backup_name

            # Copiar arquivo
            shutil.copy2(file_path, backup_path)

            return backup_path

        except Exception as e:
            st.error(f"❌ Erro ao criar backup: {e}")
            return None

    def list_backups(self, file_pattern: str = "*.xlsx", limit: int = 10) -> List[Path]:
        """
        Lista os backups disponíveis.

        Args:
            file_pattern: Padrão de arquivo para filtrar
            limit: Número máximo de backups a retornar

        Returns:
            Lista de paths dos backups (mais recentes primeiro)
        """
        try:
            backups = sorted(
                self.backup_dir.glob(file_pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            return backups[:limit]

        except Exception as e:
            st.error(f"❌ Erro ao listar backups: {e}")
            return []

    def get_backup_info(self, backup_path: Path) -> dict:
        """
        Obtém informações sobre um backup.

        Args:
            backup_path: Caminho do backup

        Returns:
            Dicionário com informações do backup
        """
        try:
            stat = backup_path.stat()
            return {
                "name": backup_path.name,
                "size": stat.st_size / 1024,  # KB
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "path": backup_path,
            }
        except Exception as e:
            return {
                "name": backup_path.name,
                "error": str(e),
            }

    def restore_backup(self, backup_path: Path, target_path: Path) -> bool:
        """
        Restaura um backup.

        Args:
            backup_path: Path do backup
            target_path: Path do arquivo de destino

        Returns:
            True se restaurado com sucesso
        """
        try:
            # Criar backup do arquivo atual antes de restaurar
            if target_path.exists():
                self.create_backup(target_path, prefix="before_restore")

            # Restaurar backup
            shutil.copy2(backup_path, target_path)

            return True

        except Exception as e:
            st.error(f"❌ Erro ao restaurar backup: {e}")
            return False

    def delete_backup(self, backup_path: Path) -> bool:
        """
        Deleta um backup.

        Args:
            backup_path: Path do backup a deletar

        Returns:
            True se deletado com sucesso
        """
        try:
            backup_path.unlink()
            return True

        except Exception as e:
            st.error(f"❌ Erro ao deletar backup: {e}")
            return False

    def cleanup_old_backups(self, keep_last: int = 20) -> int:
        """
        Remove backups antigos, mantendo apenas os mais recentes.

        Args:
            keep_last: Número de backups a manter

        Returns:
            Número de backups removidos
        """
        try:
            all_backups = sorted(
                self.backup_dir.glob("*.xlsx"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )

            removed = 0
            for backup in all_backups[keep_last:]:
                if self.delete_backup(backup):
                    removed += 1

            return removed

        except Exception as e:
            st.error(f"❌ Erro ao limpar backups: {e}")
            return 0


def render_backup_panel(backup_manager: BackupManager):
    """
    Renderiza um painel de gerenciamento de backups.

    Args:
        backup_manager: Instância do BackupManager
    """
    st.subheader("💾 Gerenciamento de Backups")

    # Listar backups
    backups = backup_manager.list_backups(limit=10)

    if not backups:
        st.info("Nenhum backup encontrado.")
        return

    st.write(f"**{len(backups)} backups encontrados** (mostrando últimos 10):")

    # Tabela de backups
    for backup in backups:
        info = backup_manager.get_backup_info(backup)

        with st.container():
            col_info, col_actions = st.columns([3, 1])

            with col_info:
                size_kb = info.get("size", 0)
                modified = info.get("modified", datetime.now())

                st.markdown(
                    f"**{info['name']}**  \n"
                    f"📊 {size_kb:.1f} KB | "
                    f"🕐 {modified.strftime('%d/%m/%Y %H:%M:%S')}"
                )

            with col_actions:
                col_restore, col_delete = st.columns(2)

                with col_restore:
                    if st.button(
                        "↩️",
                        key=f"restore_{backup.name}",
                        help="Restaurar este backup",
                    ):
                        st.warning(
                            "⚠️ Restaurar backup substituirá o arquivo atual. "
                            "Tem certeza?"
                        )

                with col_delete:
                    if st.button(
                        "🗑️",
                        key=f"delete_{backup.name}",
                        help="Deletar este backup",
                    ):
                        if backup_manager.delete_backup(backup):
                            st.success(f"✅ Backup deletado: {backup.name}")
                            st.rerun()

            st.markdown("---")

    # Botões de ação
    col_cleanup, col_info = st.columns(2)

    with col_cleanup:
        if st.button("🧹 Limpar Backups Antigos", use_container_width=True):
            removed = backup_manager.cleanup_old_backups(keep_last=10)
            if removed > 0:
                st.success(f"✅ {removed} backups antigos removidos.")
                st.rerun()
            else:
                st.info("Nenhum backup antigo para remover.")

    with col_info:
        total_size = sum(backup.stat().st_size for backup in backups if backup.exists())
        st.metric("💾 Espaço em Disco", f"{total_size / 1024 / 1024:.2f} MB")
