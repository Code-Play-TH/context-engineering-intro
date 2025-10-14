"""
File Storage Service for managing report files and cleanup.
"""
import os
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path


class FileStorageService:
    """Service for managing file storage and cleanup operations."""
    
    def __init__(self, base_upload_dir: str = "uploads"):
        self.base_upload_dir = Path(base_upload_dir)
        self.reports_dir = self.base_upload_dir / "reports"
        self.images_dir = self.base_upload_dir / "images"
        self.templates_dir = self.base_upload_dir / "templates"
        self.archive_dir = self.base_upload_dir / "archive"
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [
            self.reports_dir,
            self.images_dir,
            self.templates_dir,
            self.archive_dir,
            self.archive_dir / "reports"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information or None if file doesn't exist
        """
        path = Path(file_path)
        
        if not path.exists():
            return None
        
        stat = path.stat()
        
        return {
            'path': str(path),
            'name': path.name,
            'size': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'extension': path.suffix.lower(),
            'exists': True
        }
    
    def get_directory_size(self, directory_path: str) -> Dict[str, Any]:
        """
        Get the total size of a directory.
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            Dictionary with directory size information
        """
        path = Path(directory_path)
        
        if not path.exists() or not path.is_dir():
            return {
                'path': str(path),
                'total_size': 0,
                'total_size_mb': 0,
                'file_count': 0,
                'exists': False
            }
        
        total_size = 0
        file_count = 0
        
        for file_path in path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1
        
        return {
            'path': str(path),
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_count': file_count,
            'exists': True
        }
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics for all directories.
        
        Returns:
            Dictionary with storage statistics
        """
        stats = {
            'reports': self.get_directory_size(self.reports_dir),
            'images': self.get_directory_size(self.images_dir),
            'templates': self.get_directory_size(self.templates_dir),
            'archive': self.get_directory_size(self.archive_dir),
        }
        
        # Calculate totals
        total_size = sum(stat['total_size'] for stat in stats.values())
        total_files = sum(stat['file_count'] for stat in stats.values())
        
        stats['total'] = {
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2),
            'file_count': total_files
        }
        
        return stats
    
    def cleanup_old_files(
        self, 
        directory_path: str, 
        max_age_days: int = 90,
        file_patterns: List[str] = None
    ) -> Dict[str, Any]:
        """
        Clean up old files in a directory.
        
        Args:
            directory_path: Path to the directory to clean
            max_age_days: Maximum age of files to keep (in days)
            file_patterns: List of file patterns to match (e.g., ['*.pdf', '*.pptx'])
            
        Returns:
            Dictionary with cleanup results
        """
        path = Path(directory_path)
        
        if not path.exists() or not path.is_dir():
            return {
                'success': False,
                'error': f"Directory {directory_path} does not exist",
                'files_deleted': 0,
                'space_freed_mb': 0
            }
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        files_deleted = 0
        space_freed = 0
        errors = []
        
        # Get files to delete
        files_to_delete = []
        
        if file_patterns:
            for pattern in file_patterns:
                files_to_delete.extend(path.glob(pattern))
        else:
            files_to_delete = [f for f in path.iterdir() if f.is_file()]
        
        # Delete old files
        for file_path in files_to_delete:
            try:
                if file_path.is_file():
                    file_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if file_modified < cutoff_date:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        files_deleted += 1
                        space_freed += file_size
                        
            except Exception as e:
                errors.append(f"Failed to delete {file_path}: {str(e)}")
        
        return {
            'success': True,
            'files_deleted': files_deleted,
            'space_freed': space_freed,
            'space_freed_mb': round(space_freed / (1024 * 1024), 2),
            'errors': errors,
            'cutoff_date': cutoff_date.isoformat()
        }
    
    def archive_old_files(
        self, 
        source_directory: str, 
        max_age_days: int = 30,
        file_patterns: List[str] = None
    ) -> Dict[str, Any]:
        """
        Archive old files to the archive directory.
        
        Args:
            source_directory: Source directory to archive from
            max_age_days: Maximum age of files to keep in source (in days)
            file_patterns: List of file patterns to match
            
        Returns:
            Dictionary with archive results
        """
        source_path = Path(source_directory)
        
        if not source_path.exists() or not source_path.is_dir():
            return {
                'success': False,
                'error': f"Source directory {source_directory} does not exist",
                'files_archived': 0
            }
        
        # Create archive subdirectory
        archive_subdir = self.archive_dir / source_path.name
        archive_subdir.mkdir(exist_ok=True)
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        files_archived = 0
        errors = []
        
        # Get files to archive
        files_to_archive = []
        
        if file_patterns:
            for pattern in file_patterns:
                files_to_archive.extend(source_path.glob(pattern))
        else:
            files_to_archive = [f for f in source_path.iterdir() if f.is_file()]
        
        # Archive old files
        for file_path in files_to_archive:
            try:
                if file_path.is_file():
                    file_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if file_modified < cutoff_date:
                        # Create archive filename with timestamp
                        timestamp = file_modified.strftime("%Y%m%d_%H%M%S")
                        archive_filename = f"{timestamp}_{file_path.name}"
                        archive_path = archive_subdir / archive_filename
                        
                        # Move file to archive
                        shutil.move(str(file_path), str(archive_path))
                        files_archived += 1
                        
            except Exception as e:
                errors.append(f"Failed to archive {file_path}: {str(e)}")
        
        return {
            'success': True,
            'files_archived': files_archived,
            'archive_directory': str(archive_subdir),
            'errors': errors,
            'cutoff_date': cutoff_date.isoformat()
        }
    
    def generate_secure_filename(self, original_filename: str, prefix: str = "") -> str:
        """
        Generate a secure filename with timestamp.
        
        Args:
            original_filename: Original filename
            prefix: Optional prefix for the filename
            
        Returns:
            Secure filename with timestamp
        """
        # Get file extension
        path = Path(original_filename)
        extension = path.suffix.lower()
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
        
        # Create secure filename
        if prefix:
            filename = f"{prefix}_{timestamp}{extension}"
        else:
            filename = f"{timestamp}{extension}"
        
        return filename
    
    def get_available_space(self, directory_path: str = None) -> Dict[str, Any]:
        """
        Get available disk space.
        
        Args:
            directory_path: Path to check (defaults to base upload directory)
            
        Returns:
            Dictionary with disk space information
        """
        if directory_path is None:
            directory_path = self.base_upload_dir
        
        path = Path(directory_path)
        
        try:
            stat = shutil.disk_usage(path)
            
            return {
                'total': stat.total,
                'used': stat.used,
                'free': stat.free,
                'total_gb': round(stat.total / (1024 ** 3), 2),
                'used_gb': round(stat.used / (1024 ** 3), 2),
                'free_gb': round(stat.free / (1024 ** 3), 2),
                'used_percent': round((stat.used / stat.total) * 100, 1),
                'free_percent': round((stat.free / stat.total) * 100, 1)
            }
            
        except Exception as e:
            return {
                'error': f"Failed to get disk usage: {str(e)}",
                'total': 0,
                'used': 0,
                'free': 0
            }
    
    def validate_file_size(self, file_path: str, max_size_mb: int = 100) -> Dict[str, Any]:
        """
        Validate file size against maximum allowed size.
        
        Args:
            file_path: Path to the file
            max_size_mb: Maximum allowed size in MB
            
        Returns:
            Dictionary with validation results
        """
        path = Path(file_path)
        
        if not path.exists():
            return {
                'valid': False,
                'error': 'File does not exist',
                'size_mb': 0,
                'max_size_mb': max_size_mb
            }
        
        file_size = path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        return {
            'valid': file_size_mb <= max_size_mb,
            'size_mb': round(file_size_mb, 2),
            'max_size_mb': max_size_mb,
            'error': f'File size ({file_size_mb:.2f} MB) exceeds maximum allowed size ({max_size_mb} MB)' if file_size_mb > max_size_mb else None
        }


# Global instance
file_storage_service = FileStorageService()