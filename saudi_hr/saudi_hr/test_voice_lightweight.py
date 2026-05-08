from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from saudi_hr.saudi_hr import voice_verification as voice_module


class TestLightweightVoiceVerification(FrappeTestCase):
	def test_challenge_only_runtime_is_ready_without_heavy_dependencies(self):
		settings = {
			"enabled": 1,
			"mode": voice_module.VOICE_RUNTIME_MODE_CHALLENGE_ONLY,
			"voice_language": "ar",
		}

		with patch.object(voice_module, "get_voice_runtime_settings", return_value=settings):
			status = voice_module.get_voice_runtime_status()

		self.assertTrue(status["enabled"])
		self.assertTrue(status["runtime_ready"])
		self.assertFalse(status["missing_dependencies"])
		self.assertFalse(status["requires_enrollment"])
		self.assertFalse(status["enrollment_supported"])
		self.assertTrue(status["accepts_browser_transcript"])

	def test_challenge_only_verifier_accepts_arabic_digit_transcript(self):
		result = voice_module._run_challenge_only_verification(
			{"challenge_text": "4821"},
			{"transcript": "اربعة ثمانية اثنين واحد"},
			{"speech_match_threshold": 0.75},
		)

		self.assertEqual(result["challenge_text"], "4821")
		self.assertEqual(result["speech_match_score"], 1.0)
		self.assertEqual(result["anti_spoof_label"], "not_required")
		self.assertEqual(result["embedding"], [])
		self.assertIsNone(result["speaker_match_score"])

	def test_challenge_only_verifier_rejects_missing_browser_transcript(self):
		with self.assertRaises(frappe.PermissionError):
			voice_module._run_challenge_only_verification(
				{"challenge_text": "4821"},
				{"filename": "voice.webm"},
				{"speech_match_threshold": 0.75},
			)

	def test_voiceprint_enrollment_is_blocked_in_challenge_only_mode(self):
		settings = {
			"enabled": 1,
			"mode": voice_module.VOICE_RUNTIME_MODE_CHALLENGE_ONLY,
			"voice_language": "ar",
		}

		with patch.object(voice_module, "get_voice_runtime_settings", return_value=settings):
			with self.assertRaises(frappe.ValidationError):
				voice_module.enroll_employee_voice_profile("EMP-0001", {"transcript": "1234"}, "token")

	def test_full_biometric_runtime_reports_missing_dependencies(self):
		settings = {
			"enabled": 1,
			"mode": voice_module.VOICE_RUNTIME_MODE_FULL_BIOMETRIC,
			"voice_language": "ar",
		}

		with patch.object(voice_module, "get_voice_runtime_settings", return_value=settings), patch.object(
			voice_module.importlib.metadata,
			"version",
			side_effect=voice_module.importlib.metadata.PackageNotFoundError,
		):
			status = voice_module.get_voice_runtime_status()

		self.assertFalse(status["runtime_ready"])
		self.assertTrue(status["requires_enrollment"])
		self.assertTrue(status["enrollment_supported"])
		self.assertEqual(
			status["missing_dependencies"],
			["torch", "torchaudio", "speechbrain", "faster_whisper"],
		)