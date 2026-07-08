from .local.storage import LocalStorage

try:
    from .s3.storage import S3Storage
except ImportError:
    S3Storage = None  # type: ignore[assignment,misc]

try:
    from .supabase.storage import SupabaseStorage
except ImportError:
    SupabaseStorage = None  # type: ignore[assignment,misc]

__all__ = ["S3Storage", "LocalStorage", "SupabaseStorage"]
