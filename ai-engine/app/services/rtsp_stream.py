import cv2
import threading
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class RTSPStreamManager:
    """
    Manages persistent RTSP connection with automatic reconnection.
    Provides the latest frame on demand for streaming.
    """

    def __init__(self, rtsp_url: str, reconnect_delay: float = 5.0):
        self.rtsp_url = rtsp_url
        self.reconnect_delay = reconnect_delay

        self._cap: Optional[cv2.VideoCapture] = None
        self._latest_frame: Optional[bytes] = None
        self._frame_lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._is_connected = False
        self._last_frame_time: float = 0

    _TARGET_FPS = 25
    _FRAME_INTERVAL = 1.0 / _TARGET_FPS

    def start(self):
        """Start the RTSP streaming thread."""
        self._running = True
        self._thread = threading.Thread(target=self._stream_loop, daemon=True)
        self._thread.start()
        logger.info("RTSP stream manager started.")

    def stop(self):
        """Stop the RTSP streaming thread."""
        self._running = False
        if self._cap:
            self._cap.release()
        logger.info("RTSP stream manager stopped.")

    def get_frame(self) -> Optional[bytes]:
        """Get the latest frame as JPEG bytes."""
        with self._frame_lock:
            return self._latest_frame

    def is_connected(self) -> bool:
        """Check if RTSP stream is currently connected."""
        return self._is_connected

    def _open_stream(self) -> bool:
        """Open the RTSP stream with optimized settings."""
        try:
            # Use FFMPEG backend with TCP transport to avoid UDP packet-loss
            # which causes frame tearing / distortion.
            cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)

            # Force TCP transport (avoids UDP frame corruption)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # minimal buffer = latest frame only

            if not cap.isOpened():
                cap.release()
                return False

            self._cap = cap
            return True
        except Exception as e:
            logger.error("Failed to open RTSP stream: %s", e)
            return False

    def _stream_loop(self):
        """Continuously pulls frames from RTSP and encodes as JPEG."""
        while self._running:
            # ---- Connect ----
            logger.info("Connecting to RTSP: %s", self.rtsp_url)
            if not self._open_stream():
                self._is_connected = False
                logger.warning(
                    "Cannot open RTSP stream. Retrying in %.1fs...",
                    self.reconnect_delay,
                )
                time.sleep(self.reconnect_delay)
                continue

            self._is_connected = True
            logger.info("RTSP stream connected: %s", self.rtsp_url)

            # ---- Read loop ----
            # grab() in a tight loop to drain FFMPEG's internal buffer
            # so we always stay at the latest frame. Only decode+encode
            # at target FPS to keep CPU usage reasonable.
            consecutive_failures = 0
            last_encode = 0.0
            while self._running:
                try:
                    if not self._cap.grab():
                        consecutive_failures += 1
                        if consecutive_failures > 30:
                            logger.warning("Too many grab failures — reconnecting.")
                            break
                        continue

                    consecutive_failures = 0

                    now = time.monotonic()
                    if now - last_encode < self._FRAME_INTERVAL:
                        continue

                    ret, frame = self._cap.retrieve()
                    if not ret or frame is None:
                        continue

                    ok, jpeg_buf = cv2.imencode(
                        ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70]
                    )
                    if ok:
                        with self._frame_lock:
                            self._latest_frame = jpeg_buf.tobytes()
                            self._last_frame_time = now

                    last_encode = now

                except Exception as e:
                    logger.error("Frame read error: %s", e)
                    break

            # ---- Cleanup on disconnect ----
            self._is_connected = False
            if self._cap:
                self._cap.release()
                self._cap = None
            time.sleep(self.reconnect_delay)


# Global instance
_rtsp_manager: Optional[RTSPStreamManager] = None


def get_rtsp_manager() -> Optional[RTSPStreamManager]:
    """Get the global RTSP manager instance."""
    return _rtsp_manager


def init_rtsp_manager(rtsp_url: str) -> RTSPStreamManager:
    """Initialize and start the global RTSP manager."""
    global _rtsp_manager
    _rtsp_manager = RTSPStreamManager(rtsp_url)
    _rtsp_manager.start()
    return _rtsp_manager
