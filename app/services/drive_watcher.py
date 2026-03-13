import json
import logging
import os
from pathlib import Path
from typing import Dict, Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from pypdf import PdfReader
from docx import Document

from app.settings import settings
from app.rag.ingest import ingest_document

logger = logging.getLogger(__name__)

# Arquivo para persistir estado (quais arquivos já processamos)
STATE_FILE = Path("data/drive_state.json")

class DriveWatcher:
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    FOLDER_MIME = "application/vnd.google-apps.folder"
    GOOGLE_DOC_MIME = "application/vnd.google-apps.document"
    SUPPORTED_DOWNLOAD_MIME_TYPES = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/markdown",
    }
    SUPPORTED_EXPORT_MIME_TYPES = {
        GOOGLE_DOC_MIME: ("text/plain", ".txt"),
    }

    def __init__(self):
        self.creds = None
        self.folder_id = settings.GOOGLE_DRIVE_FOLDER_ID
        self.service_account_file = settings.GOOGLE_APPLICATION_CREDENTIALS

    def _authenticate(self):
        """Autentica usando Service Account."""
        if not self.creds:
            # Verifica se arquivo existe, senão tenta usar o caminho relativo
            if not os.path.exists(self.service_account_file):
                # Tenta no diretório raiz se o path for relativo
                root_path = Path(settings.BASE_DIR) / self.service_account_file
                if root_path.exists():
                    self.service_account_file = str(root_path)
                else:
                    logger.error(f"Arquivo de credenciais não encontrado: {self.service_account_file}")
                    return None
            
            self.creds = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=self.SCOPES
            )
        return self.creds

    def _get_service(self):
        creds = self._authenticate()
        if not creds:
            return None
        return build('drive', 'v3', credentials=creds)

    def _load_state(self) -> Dict[str, str]:
        """Carrega estado dos arquivos processados (ID -> MD5/ModifiedTime)."""
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_state(self, state: Dict[str, str]):
        """Salva estado."""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def _sanitize_filename(self, name: str) -> str:
        """Sanitiza nome para uso em filesystem local."""
        invalid_chars = '<>:"/\\|?*'
        safe = "".join("_" if c in invalid_chars else c for c in (name or ""))
        safe = safe.strip().strip(".")
        return safe or "arquivo_drive"

    def _is_supported_mime(self, mime_type: str) -> bool:
        """Valida se mime type é elegível para ingestão."""
        return (
            mime_type in self.SUPPORTED_DOWNLOAD_MIME_TYPES
            or mime_type in self.SUPPORTED_EXPORT_MIME_TYPES
        )

    def _list_folder_children(self, service, folder_id: str) -> list[Dict[str, Any]]:
        """Lista filhos diretos de uma pasta do Drive, com paginação."""
        files: list[Dict[str, Any]] = []
        page_token = None

        while True:
            response = service.files().list(
                q=f"'{folder_id}' in parents and trashed = false",
                pageSize=100,
                fields="nextPageToken,files(id,name,mimeType,modifiedTime)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                pageToken=page_token,
            ).execute()

            files.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return files

    def _collect_supported_files_recursive(
        self,
        service,
        root_folder_id: str,
    ) -> tuple[list[Dict[str, Any]], int]:
        """
        Percorre subpastas recursivamente e retorna arquivos suportados.
        """
        files_to_process: list[Dict[str, Any]] = []
        pending_folders: list[tuple[str, str]] = [(root_folder_id, "")]
        visited_folders: set[str] = set()
        folders_scanned = 0

        while pending_folders:
            current_folder_id, current_prefix = pending_folders.pop()
            if current_folder_id in visited_folders:
                continue

            visited_folders.add(current_folder_id)
            folders_scanned += 1

            children = self._list_folder_children(service, current_folder_id)
            for child in children:
                child_id = child.get("id")
                child_name = child.get("name", "sem_nome")
                child_mime = child.get("mimeType", "")
                child_path = (
                    f"{current_prefix}/{child_name}" if current_prefix else child_name
                )

                if child_mime == self.FOLDER_MIME and child_id:
                    pending_folders.append((child_id, child_path))
                    continue

                if self._is_supported_mime(child_mime):
                    child["drive_path"] = child_path
                    files_to_process.append(child)

        return files_to_process, folders_scanned

    def _download_or_export_file(self, service, file_data: Dict[str, Any]) -> Path:
        """Baixa arquivo binário ou exporta Google Docs para texto."""
        file_id = file_data["id"]
        file_name = self._sanitize_filename(file_data.get("name", "arquivo"))
        mime_type = file_data.get("mimeType", "")

        temp_dir = Path("temp_drive_downloads")
        temp_dir.mkdir(exist_ok=True)

        if mime_type in self.SUPPORTED_EXPORT_MIME_TYPES:
            export_mime, export_suffix = self.SUPPORTED_EXPORT_MIME_TYPES[mime_type]
            request = service.files().export_media(fileId=file_id, mimeType=export_mime)
            file_path = temp_dir / f"{file_name}{export_suffix}"
        else:
            request = service.files().get_media(fileId=file_id)
            file_path = temp_dir / file_name

        with open(file_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                _, done = downloader.next_chunk()
        
        return file_path

    def _extract_text(self, file_path: Path) -> str:
        """Extrai texto de PDF, DOCX ou lê TXT/MD."""
        suffix = file_path.suffix.lower()
        
        if suffix == '.pdf':
            try:
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
            except Exception as e:
                logger.error(f"Erro ao ler PDF {file_path}: {e}")
                return ""
                
        elif suffix == '.docx':
            try:
                doc = Document(file_path)
                return "\n".join([p.text for p in doc.paragraphs])
            except Exception as e:
                logger.error(f"Erro ao ler DOCX {file_path}: {e}")
                return ""
                
        else:
            # Assume texto plano (md, txt)
            try:
                return file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                logger.error(f"Erro ao ler arquivo texto {file_path}: {e}")
                return ""

    def check_for_updates(self) -> Dict[str, Any]:
        """Verifica pasta do Drive por arquivos novos/modificados."""
        summary: Dict[str, Any] = {
            "status": "ok",
            "folder_id": self.folder_id,
            "files_seen": 0,
            "files_updated": 0,
            "files_processed": [],
            "errors": [],
            "folders_scanned": 0,
        }

        if not self.folder_id:
            msg = "GOOGLE_DRIVE_FOLDER_ID nao configurado."
            logger.warning(msg)
            summary["status"] = "skipped"
            summary["errors"].append(msg)
            return summary

        service = self._get_service()
        if not service:
            msg = "Falha ao conectar no Google Drive API."
            logger.error(msg)
            summary["status"] = "error"
            summary["errors"].append(msg)
            return summary

        logger.info(f"Monitorando pasta Drive: {self.folder_id}")

        try:
            files, folders_scanned = self._collect_supported_files_recursive(
                service, self.folder_id
            )
            summary["folders_scanned"] = folders_scanned
        except Exception as e:
            msg = f"Erro ao listar arquivos do Drive: {e}"
            logger.error(msg)
            summary["status"] = "error"
            summary["errors"].append(msg)
            return summary

        summary["files_seen"] = len(files)
        state = self._load_state()
        updates_count = 0
        processed_files: list[str] = []

        for file in files:
            file_id = file['id']
            name = file['name']
            drive_path = file.get("drive_path", name)
            modified_time = file['modifiedTime']
            
            # Verifica se precisa processar (novo ou modificado)
            last_processed_time = state.get(file_id)
            
            if last_processed_time != modified_time:
                logger.info("Processando arquivo do Drive: %s (%s)", drive_path, file_id)
                
                local_path = None
                converted_path = None

                try:
                    # 1. Download/Export
                    local_path = self._download_or_export_file(service, file)
                    
                    # 2. Extração de Texto
                    text_content = self._extract_text(local_path)
                    
                    if not text_content.strip():
                        logger.warning("Arquivo vazio ou ilegivel: %s", drive_path)
                        continue

                    # Salva como .txt temporário para ingestão compatível
                    converted_path = local_path.with_suffix(".txt")
                    converted_path.write_text(text_content, encoding="utf-8")

                    # 3. Ingestão
                    chunks_count = ingest_document(
                        file_path=converted_path,
                        doc_id=f"drive_{file_id}",
                        title=f"[Drive] {drive_path}",
                        tags=["drive", "auto-import"],
                        force=True # Força atualização pois modifiedTime mudou
                    )

                    # 4. Atualiza estado
                    if chunks_count > 0:
                        state[file_id] = modified_time
                        updates_count += 1
                        processed_files.append(drive_path)
                    
                except Exception as e:
                    msg = f"Erro ao processar arquivo {drive_path}: {e}"
                    logger.error(msg)
                    summary["errors"].append(msg)
                
                finally:
                    # Limpeza
                    if local_path and local_path.exists():
                        try:
                            os.remove(local_path)
                        except OSError as e:
                            logger.debug(
                                "Erro ao remover arquivo temporario %s: %s",
                                local_path,
                                e,
                            )
                    if converted_path and converted_path.exists():
                        try:
                            os.remove(converted_path)
                        except OSError as e:
                            logger.debug(
                                "Erro ao remover arquivo temporario convertido %s: %s",
                                converted_path,
                                e,
                            )

        if updates_count > 0:
            self._save_state(state)
            logger.info(f"Drive Sync completo. {updates_count} arquivos atualizados.")
        else:
            logger.info("Nenhuma alteração encontrada no Drive.")

        summary["files_updated"] = updates_count
        summary["files_processed"] = processed_files
        if summary["errors"] and summary["status"] == "ok":
            summary["status"] = "partial"

        return summary

if __name__ == "__main__":
    # Teste manual
    logging.basicConfig(level=logging.INFO)
    watcher = DriveWatcher()
    watcher.check_for_updates()
