"""
File Storage Service

Handles image upload, processing, and storage for profile pictures.
Implements validation, resizing, and secure file handling.
"""

import os
import uuid
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageOps
import io

from app.config import settings


class FileStorageService:
    """Service for managing file storage and image processing."""

    # Allowed image formats and their MIME types
    ALLOWED_MIME_TYPES = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }

    # Maximum file size (5MB)
    MAX_FILE_SIZE = 5 * 1024 * 1024

    # Profile picture dimensions
    PROFILE_PICTURE_SIZE = (200, 200)

    # Base upload directory
    UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads" / "profile_pictures"

    def __init__(self) -> None:
        """Initialize file storage service and ensure upload directory exists."""
        self._ensure_upload_directory()

    def _ensure_upload_directory(self) -> None:
        """Create upload directory if it doesn't exist."""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def validate_image(self, file_content: bytes, content_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate image file.

        Args:
            file_content: Raw file content bytes
            content_type: MIME type from upload

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check content type
        if content_type not in self.ALLOWED_MIME_TYPES:
            return False, f"Invalid file type. Allowed types: {', '.join(self.ALLOWED_MIME_TYPES.keys())}"

        # Check file size
        if len(file_content) > self.MAX_FILE_SIZE:
            max_size_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"File size exceeds maximum allowed size of {max_size_mb}MB"

        # Validate image can be opened by PIL
        try:
            image = Image.open(io.BytesIO(file_content))
            image.verify()  # Verify it's a valid image
        except Exception as e:
            return False, f"Invalid or corrupted image file: {str(e)}"

        return True, None

    def process_profile_picture(
        self,
        file_content: bytes,
        content_type: str,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Process and save profile picture.

        Args:
            file_content: Raw file content bytes
            content_type: MIME type from upload

        Returns:
            Tuple of (filename, error_message)
        """
        # Validate image
        is_valid, error_message = self.validate_image(file_content, content_type)
        if not is_valid:
            return None, error_message

        try:
            # Open and process image
            image = Image.open(io.BytesIO(file_content))

            # Convert RGBA to RGB if necessary (for JPEG compatibility)
            if image.mode in ("RGBA", "LA", "P"):
                # Create white background
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(image, mask=image.split()[-1] if image.mode in ("RGBA", "LA") else None)
                image = background

            # Resize and crop to square maintaining aspect ratio
            image = ImageOps.fit(
                image,
                self.PROFILE_PICTURE_SIZE,
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )

            # Generate unique filename
            file_extension = self.ALLOWED_MIME_TYPES[content_type]
            filename = f"{uuid.uuid4()}{file_extension}"
            file_path = self.UPLOAD_DIR / filename

            # Save image with optimization
            save_kwargs = {"optimize": True}
            if file_extension == ".jpg":
                save_kwargs["quality"] = 85
                image.save(file_path, "JPEG", **save_kwargs)
            elif file_extension == ".png":
                save_kwargs["compress_level"] = 9
                image.save(file_path, "PNG", **save_kwargs)
            elif file_extension == ".webp":
                save_kwargs["quality"] = 85
                image.save(file_path, "WEBP", **save_kwargs)

            return filename, None

        except Exception as e:
            return None, f"Failed to process image: {str(e)}"

    def delete_profile_picture(self, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a profile picture file.

        Args:
            filename: Name of the file to delete

        Returns:
            Tuple of (success, error_message)
        """
        if not filename:
            return True, None  # Nothing to delete

        try:
            file_path = self.UPLOAD_DIR / filename
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
            return True, None
        except Exception as e:
            return False, f"Failed to delete file: {str(e)}"

    def get_file_path(self, filename: str) -> Optional[Path]:
        """
        Get full path to a file if it exists.

        Args:
            filename: Name of the file

        Returns:
            Path object if file exists, None otherwise
        """
        if not filename:
            return None

        file_path = self.UPLOAD_DIR / filename
        if file_path.exists() and file_path.is_file():
            return file_path
        return None

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal attacks.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Get just the filename, removing any path components
        filename = os.path.basename(filename)
        # Remove any potentially dangerous characters
        return "".join(c for c in filename if c.isalnum() or c in ".-_")
