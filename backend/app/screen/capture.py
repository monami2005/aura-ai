import io
from datetime import datetime
from typing import Tuple, Optional
from .models import ScreenCaptureMetadata

def capture_primary_screen() -> Tuple[Optional[bytes], Optional[ScreenCaptureMetadata], Optional[str]]:
    """
    Explicit, user-triggered in-memory capture of the primary display.
    Avoids permanent disk storage by default for strict privacy.
    Returns: (image_bytes, metadata, error_message)
    """
    try:
        try:
            from PIL import Image, ImageGrab
        except ImportError:
            return None, None, "Pillow is not installed. Run 'pip install Pillow' to enable screen capture."

        screenshot = ImageGrab.grab()
        if screenshot is None:
            return None, None, "Could not access the primary display device."

        width, height = screenshot.size
        ts = datetime.utcnow().isoformat() + "Z"
        
        # Encode to in-memory PNG bytes
        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()
        buffer.close()

        metadata = ScreenCaptureMetadata(
            width=width,
            height=height,
            timestamp=ts,
            format="PNG"
        )
        return image_bytes, metadata, None
    except Exception as e:
        return None, None, f"Screen capture error: {str(e)}"
