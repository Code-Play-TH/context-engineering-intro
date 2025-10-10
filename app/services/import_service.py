"""Import service for KOL CSV/Excel file processing."""
import os
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from sqlmodel import Session, select
from fastapi import HTTPException, status, UploadFile
from app.models.import_job import ImportJob, ImportStatus
from app.models.kol import KOL
from app.models.social_handle import SocialHandle
from app.core.config import settings


class ImportService:
    """Service for handling KOL data import from CSV/Excel files."""
    
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path("uploads/imports")
        self.pending_dir = self.upload_dir / "pending"
        self.processed_dir = self.upload_dir / "processed"
        self.failed_dir = self.upload_dir / "failed"
        
        # Create directories if they don't exist
        for directory in [self.pending_dir, self.processed_dir, self.failed_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def upload_import_file(
        self, 
        file: UploadFile, 
        created_by: int
    ) -> ImportJob:
        """
        Upload and save import file, create ImportJob record.
        
        Args:
            file: Uploaded file (CSV or Excel)
            created_by: User ID who uploaded the file
            
        Returns:
            ImportJob object with job details
            
        Raises:
            HTTPException: If file validation fails
        """
        # Validate file type
        allowed_extensions = ['.csv', '.xlsx', '.xls']
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_extension} not supported. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Validate file size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 50MB limit"
            )
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = self.pending_dir / safe_filename
        
        # Save file to pending directory
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Read file to get row count
        try:
            if file_extension == '.csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            total_rows = len(df)
        except Exception as e:
            # Clean up file if reading fails
            file_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to read file: {str(e)}"
            )
        
        # Create ImportJob record
        import_job = ImportJob(
            filename=file.filename,
            file_path=str(file_path),
            status=ImportStatus.PENDING,
            total_rows=total_rows,
            processed_rows=0,
            success_count=0,
            error_count=0,
            errors=[],
            created_by=created_by
        )
        
        self.db.add(import_job)
        self.db.commit()
        self.db.refresh(import_job)
        
        return import_job
    
    def get_import_job(self, job_id: int) -> Optional[ImportJob]:
        """
        Get import job by ID.
        
        Args:
            job_id: Import job ID
            
        Returns:
            ImportJob object or None if not found
        """
        return self.db.get(ImportJob, job_id)
    
    def validate_import_data(self, job_id: int) -> ImportJob:
        """
        Validate import data and update job status.
        
        Args:
            job_id: Import job ID
            
        Returns:
            Updated ImportJob object
            
        Raises:
            HTTPException: If job not found or validation fails
        """
        job = self.get_import_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Import job not found"
            )
        
        if job.status != ImportStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job status is {job.status}, expected pending"
            )
        
        # Update status to validating
        job.status = ImportStatus.VALIDATING
        self.db.add(job)
        self.db.commit()
        
        try:
            # Read the file
            file_path = Path(job.file_path)
            if not file_path.exists():
                raise Exception("Import file not found")
            
            file_extension = file_path.suffix.lower()
            if file_extension == '.csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Validate data
            validation_errors = self._validate_dataframe(df)
            
            # Update job with validation results
            job.errors = validation_errors
            job.error_count = len(validation_errors)
            
            if validation_errors:
                job.status = ImportStatus.FAILED
            else:
                job.status = ImportStatus.PENDING  # Ready for processing
            
            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)
            
            return job
            
        except Exception as e:
            job.status = ImportStatus.FAILED
            job.errors = [{"error": f"Validation failed: {str(e)}"}]
            job.error_count = 1
            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)
            
            return job
    
    def _validate_dataframe(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Validate DataFrame content.
        
        Args:
            df: Pandas DataFrame to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check required columns
        required_columns = ['name']
        social_columns = ['instagram', 'tiktok', 'youtube', 'twitter', 'facebook']
        
        # Check if name column exists
        if 'name' not in df.columns:
            errors.append({
                "row": "header",
                "error": "Required column 'name' is missing"
            })
            return errors
        
        # Check if at least one social media column exists
        has_social_column = any(col in df.columns for col in social_columns)
        if not has_social_column:
            errors.append({
                "row": "header",
                "error": f"At least one social media column required: {', '.join(social_columns)}"
            })
        
        # Validate each row
        for idx, row in df.iterrows():
            row_errors = []
            
            # Check required fields
            if pd.isna(row.get('name')) or str(row.get('name')).strip() == '':
                row_errors.append("Name is required")
            
            # Check if at least one social handle is provided
            has_social_handle = False
            for col in social_columns:
                if col in df.columns and not pd.isna(row.get(col)) and str(row.get(col)).strip():
                    has_social_handle = True
                    break
            
            if not has_social_handle:
                row_errors.append("At least one social media handle is required")
            
            # Validate email format if provided
            if 'email' in df.columns and not pd.isna(row.get('email')):
                email = str(row.get('email')).strip()
                if email and '@' not in email:
                    row_errors.append("Invalid email format")
            
            # Check for duplicates in current data
            name = str(row.get('name', '')).strip().lower()
            if name:
                duplicate_rows = df[df['name'].str.lower().str.strip() == name].index.tolist()
                if len(duplicate_rows) > 1 and idx == duplicate_rows[0]:
                    row_errors.append(f"Duplicate name found in rows: {', '.join(map(str, duplicate_rows))}")
            
            # Add row errors to main errors list
            if row_errors:
                errors.append({
                    "row": idx + 2,  # +2 because pandas is 0-indexed and we have header
                    "name": str(row.get('name', '')),
                    "errors": row_errors
                })
        
        return errors
    
    def process_import(self, job_id: int) -> ImportJob:
        """
        Process validated import data and create KOL records.
        
        Args:
            job_id: Import job ID
            
        Returns:
            Updated ImportJob object
            
        Raises:
            HTTPException: If job not found or processing fails
        """
        job = self.get_import_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Import job not found"
            )
        
        if job.status != ImportStatus.PENDING or job.error_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job must be validated and error-free before processing"
            )
        
        # Update status to processing
        job.status = ImportStatus.PROCESSING
        self.db.add(job)
        self.db.commit()
        
        try:
            # Read the file
            file_path = Path(job.file_path)
            file_extension = file_path.suffix.lower()
            
            if file_extension == '.csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Process in batches
            batch_size = 100
            success_count = 0
            error_count = 0
            errors = []
            
            for start_idx in range(0, len(df), batch_size):
                end_idx = min(start_idx + batch_size, len(df))
                batch_df = df.iloc[start_idx:end_idx]
                
                batch_success, batch_errors = self._process_batch(batch_df, start_idx)
                success_count += batch_success
                error_count += len(batch_errors)
                errors.extend(batch_errors)
                
                # Update progress
                job.processed_rows = end_idx
                job.success_count = success_count
                job.error_count = error_count
                job.errors = errors
                self.db.add(job)
                self.db.commit()
            
            # Move file to appropriate directory
            if error_count == 0:
                new_path = self.processed_dir / file_path.name
                job.status = ImportStatus.COMPLETED
            else:
                new_path = self.failed_dir / file_path.name
                job.status = ImportStatus.FAILED
            
            file_path.rename(new_path)
            job.file_path = str(new_path)
            job.completed_at = datetime.utcnow()
            
            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)
            
            return job
            
        except Exception as e:
            job.status = ImportStatus.FAILED
            job.errors = [{"error": f"Processing failed: {str(e)}"}]
            job.error_count += 1
            job.completed_at = datetime.utcnow()
            
            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)
            
            return job
    
    def _process_batch(self, batch_df: pd.DataFrame, start_idx: int) -> tuple[int, List[Dict[str, Any]]]:
        """
        Process a batch of rows and create KOL records.
        
        Args:
            batch_df: DataFrame batch to process
            start_idx: Starting index for error reporting
            
        Returns:
            Tuple of (success_count, errors_list)
        """
        success_count = 0
        errors = []
        social_columns = ['instagram', 'tiktok', 'youtube', 'twitter', 'facebook']
        
        for idx, row in batch_df.iterrows():
            try:
                # Create KOL record
                kol_data = {
                    'name': str(row.get('name', '')).strip(),
                    'email': str(row.get('email', '')).strip() if not pd.isna(row.get('email')) else None,
                    'phone': str(row.get('phone', '')).strip() if not pd.isna(row.get('phone')) else None,
                    'location': str(row.get('location', '')).strip() if not pd.isna(row.get('location')) else None,
                    'niche': [n.strip() for n in str(row.get('niche', '')).split(',') if n.strip()] if not pd.isna(row.get('niche')) else [],
                    'tags': [t.strip() for t in str(row.get('tags', '')).split(',') if t.strip()] if not pd.isna(row.get('tags')) else [],
                    'notes': str(row.get('notes', '')).strip() if not pd.isna(row.get('notes')) else None,
                }
                
                # Remove empty string values
                kol_data = {k: v for k, v in kol_data.items() if v not in [None, '', []]}
                
                kol = KOL(**kol_data)
                self.db.add(kol)
                self.db.flush()  # Get the ID without committing
                
                # Create social handles
                for platform in social_columns:
                    if platform in batch_df.columns and not pd.isna(row.get(platform)):
                        handle_value = str(row.get(platform)).strip()
                        if handle_value:
                            # Extract handle from URL if needed
                            if 'http' in handle_value:
                                # Extract username from URL
                                handle_value = handle_value.split('/')[-1]
                            
                            social_handle = SocialHandle(
                                kol_id=kol.id,
                                platform=platform,
                                handle=handle_value,
                                url=f"https://{platform}.com/{handle_value}",
                                follower_count=0,  # Will be updated later via enrichment
                                is_verified=False,
                                is_active=True
                            )
                            self.db.add(social_handle)
                
                self.db.commit()
                success_count += 1
                
            except Exception as e:
                self.db.rollback()
                errors.append({
                    "row": start_idx + idx + 2,  # +2 for header and 0-indexing
                    "name": str(row.get('name', '')),
                    "error": str(e)
                })
        
        return success_count, errors