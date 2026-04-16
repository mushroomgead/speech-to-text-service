"""
Security and validation tests for transcriber.py.
Whisper model is always mocked — no GPU/CPU required to run these tests.
"""
import os
import pytest
from unittest.mock import MagicMock, patch


def make_mock_model(text="ทดสอบ"):
    model = MagicMock()
    model.transcribe.return_value = {"text": text}
    return model


# ---------------------------------------------------------------------------
# _validate_extension
# ---------------------------------------------------------------------------

class TestValidateExtension:
    def test_accepts_mp3(self):
        from app.transcriber import _validate_extension
        _validate_extension(".mp3")  # should not raise

    def test_accepts_webm(self):
        from app.transcriber import _validate_extension
        _validate_extension(".webm")

    def test_accepts_ogg(self):
        from app.transcriber import _validate_extension
        _validate_extension(".ogg")

    def test_rejects_exe(self):
        from app.transcriber import _validate_extension
        with pytest.raises(ValueError, match="Unsupported file format"):
            _validate_extension(".exe")

    def test_rejects_empty(self):
        from app.transcriber import _validate_extension
        with pytest.raises(ValueError):
            _validate_extension("")

    def test_rejects_py(self):
        from app.transcriber import _validate_extension
        with pytest.raises(ValueError):
            _validate_extension(".py")


# ---------------------------------------------------------------------------
# transcribe — path traversal
# ---------------------------------------------------------------------------

class TestTranscribePathSecurity:
    def test_rejects_path_traversal(self, tmp_path):
        from app.transcriber import transcribe
        model = make_mock_model()
        evil_path = str(tmp_path / ".." / ".." / "etc" / "passwd.mp3")
        with patch("app.transcriber.settings") as mock_settings:
            mock_settings.audio_base_path = str(tmp_path / "audio")
            with pytest.raises(ValueError, match="Access denied"):
                transcribe(model, evil_path, "th")

    def test_rejects_absolute_path_outside_base(self, tmp_path):
        from app.transcriber import transcribe
        model = make_mock_model()
        with patch("app.transcriber.settings") as mock_settings:
            mock_settings.audio_base_path = str(tmp_path / "audio")
            with pytest.raises(ValueError, match="Access denied"):
                transcribe(model, "/etc/passwd.mp3", "th")

    def test_accepts_valid_path_inside_base(self, tmp_path):
        from app.transcriber import transcribe
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        audio_file = audio_dir / "test.mp3"
        audio_file.write_bytes(b"fake audio")

        model = make_mock_model("สวัสดี")
        with patch("app.transcriber.settings") as mock_settings:
            mock_settings.audio_base_path = str(audio_dir)
            result = transcribe(model, str(audio_file), "th")
        assert result == "สวัสดี"

    def test_rejects_sibling_directory_with_similar_prefix(self, tmp_path):
        """Ensure /audio-evil is not treated as inside /audio"""
        from app.transcriber import transcribe
        model = make_mock_model()
        evil_dir = tmp_path / "audio-evil"
        evil_dir.mkdir()
        evil_file = evil_dir / "test.mp3"
        evil_file.write_bytes(b"fake")

        with patch("app.transcriber.settings") as mock_settings:
            mock_settings.audio_base_path = str(tmp_path / "audio")
            with pytest.raises(ValueError, match="Access denied"):
                transcribe(model, str(evil_file), "th")

    def test_rejects_missing_file(self, tmp_path):
        from app.transcriber import transcribe
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        with patch("app.transcriber.settings") as mock_settings:
            mock_settings.audio_base_path = str(audio_dir)
            with pytest.raises(FileNotFoundError):
                transcribe(model=make_mock_model(), file_path=str(audio_dir / "missing.mp3"), language="th")


# ---------------------------------------------------------------------------
# transcribe_from_url — URL validation
# ---------------------------------------------------------------------------

class TestTranscribeFromUrlSecurity:
    def test_rejects_file_scheme(self):
        from app.transcriber import transcribe_from_url
        with pytest.raises(ValueError, match="Only http/https"):
            transcribe_from_url(make_mock_model(), "file:///etc/passwd.mp3", "th")

    def test_rejects_ftp_scheme(self):
        from app.transcriber import transcribe_from_url
        with pytest.raises(ValueError, match="Only http/https"):
            transcribe_from_url(make_mock_model(), "ftp://evil.com/audio.mp3", "th")

    def test_rejects_unsupported_extension_in_url(self):
        from app.transcriber import transcribe_from_url
        with pytest.raises(ValueError, match="Unsupported file format"):
            transcribe_from_url(make_mock_model(), "https://example.com/audio.wav", "th")

    def test_rejects_empty_download(self, tmp_path):
        from app.transcriber import transcribe_from_url
        empty_file = tmp_path / "empty.webm"
        empty_file.write_bytes(b"")

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.__enter__ = lambda s: s
            mock_response.__exit__ = MagicMock(return_value=False)
            mock_response.read.return_value = b""
            mock_urlopen.return_value = mock_response

            with pytest.raises(ValueError, match="empty"):
                transcribe_from_url(make_mock_model(), "https://example.com/audio.webm", "th")

    def test_accepts_valid_https_url(self, tmp_path):
        from app.transcriber import transcribe_from_url
        fake_audio = b"fake audio content"

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.__enter__ = lambda s: s
            mock_response.__exit__ = MagicMock(return_value=False)
            mock_response.read.return_value = fake_audio
            mock_urlopen.return_value = mock_response

            model = make_mock_model("ทดสอบ")
            result = transcribe_from_url(model, "https://example.com/audio.mp3", "th")

        assert result == "ทดสอบ"
