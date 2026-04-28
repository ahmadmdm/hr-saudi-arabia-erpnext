from __future__ import annotations

import base64
import difflib
import importlib.metadata
import json
import os
import re
import secrets
import sys
import tempfile
from contextlib import suppress

import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime


VOICE_PROFILE_STATUS_NOT_ENROLLED = "Not Enrolled / غير مسجل"
VOICE_PROFILE_STATUS_ENROLLED = "Enrolled / مسجل"
VOICE_PROFILE_STATUS_SUSPENDED = "Suspended / موقوف"

VOICE_PROFILE_RESET_ROLES = ("HR Manager", "HR User", "System Manager")

VOICE_VERIFICATION_STATUS_NOT_REQUIRED = "Not Required / غير مطلوب"
VOICE_VERIFICATION_STATUS_PENDING = "Pending / بانتظار"
VOICE_VERIFICATION_STATUS_PASSED = "Passed / ناجح"
VOICE_VERIFICATION_STATUS_FAILED = "Failed / فشل"

_MODEL_CACHE = {}
_ARABIC_NUMERAL_TRANSLATION = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_DIGIT_WORDS = {
	"zero": "0",
	"صفر": "0",
	"one": "1",
	"واحد": "1",
	"واحدة": "1",
	"two": "2",
	"اثنين": "2",
	"اثنان": "2",
	"ثنين": "2",
	"twoo": "2",
	"three": "3",
	"ثلاثة": "3",
	"ثلاثه": "3",
	"four": "4",
	"اربعة": "4",
	"أربعة": "4",
	"اربعه": "4",
	"أربعه": "4",
	"five": "5",
	"خمسة": "5",
	"خمسه": "5",
	"six": "6",
	"ستة": "6",
	"سته": "6",
	"seven": "7",
	"سبعة": "7",
	"سبعه": "7",
	"eight": "8",
	"ثمانية": "8",
	"ثمانيه": "8",
	"ثمانية": "8",
	"ثمانيه": "8",
	"nine": "9",
	"تسعة": "9",
	"تسعه": "9",
}


def get_voice_runtime_settings():
	settings = frappe.get_single("Saudi HR Settings")
	bonafide_labels = [
		item.strip().lower()
		for item in (getattr(settings, "voice_bonafide_labels", "") or "bonafide,genuine,human,real").split(",")
		if item.strip()
	]

	return {
		"enabled": cint(getattr(settings, "enable_voice_verification", 0) or 0),
		"speaker_model_source": getattr(settings, "speaker_model_source", "") or "speechbrain/spkrec-ecapa-voxceleb",
		"anti_spoof_model_source": getattr(settings, "anti_spoof_model_source", "") or "",
		"whisper_model_size": getattr(settings, "voice_whisper_model_size", "") or "small",
		"voice_language": getattr(settings, "voice_language", "") or "ar",
		"speaker_threshold": flt(getattr(settings, "voice_speaker_threshold", 0.25) or 0.25),
		"speech_match_threshold": flt(getattr(settings, "voice_speech_match_threshold", 0.75) or 0.75),
		"anti_spoof_threshold": flt(getattr(settings, "voice_anti_spoof_threshold", 0.5) or 0.5),
		"compute_type": getattr(settings, "voice_compute_type", "") or "int8",
		"bonafide_labels": bonafide_labels or ["bonafide", "genuine", "human", "real"],
	}


def get_voice_runtime_status():
	runtime_packages = {
		"torch": "torch",
		"torchaudio": "torchaudio",
		"speechbrain": "speechbrain",
		"faster_whisper": "faster-whisper",
	}
	missing = []
	for label, package_name in runtime_packages.items():
		try:
			importlib.metadata.version(package_name)
		except importlib.metadata.PackageNotFoundError:
			missing.append(label)
		except Exception as exc:
			missing.append(f"{label}:{type(exc).__name__}")

	settings = get_voice_runtime_settings()
	return {
		"enabled": bool(settings["enabled"]),
		"runtime_ready": not missing,
		"missing_dependencies": missing,
	}


def _sanitize_speechbrain_lazy_modules():
	# SpeechBrain registers optional integrations as lazy redirects that break
	# Werkzeug's reloader when it inspects module.__file__.
	for module_name, module in list(sys.modules.items()):
		if not module_name.startswith("speechbrain"):
			continue
		try:
			getattr(module, "__file__", None)
		except ImportError:
			sys.modules.pop(module_name, None)


def get_employee_voice_profile_status(employee):
	profile = frappe.db.get_value(
		"Saudi Employee Voice Profile",
		employee,
		[
			"employee",
			"enrollment_status",
			"is_active",
			"last_enrolled_on",
			"transcript_preview",
			"last_anti_spoof_score",
			"last_speech_match_score",
			"last_speaker_match_score",
		],
		as_dict=True,
	)
	has_voice_profile = bool(
		profile and cint(profile.is_active) and profile.enrollment_status == VOICE_PROFILE_STATUS_ENROLLED
	)
	can_self_enroll = not profile or (
		not cint(profile.is_active) and profile.enrollment_status == VOICE_PROFILE_STATUS_NOT_ENROLLED
	)

	return {
		"has_voice_profile": has_voice_profile,
		"profile_exists": bool(profile),
		"can_self_enroll": can_self_enroll,
		"status": (profile or {}).get("enrollment_status") or VOICE_PROFILE_STATUS_NOT_ENROLLED,
		"is_active": bool((profile or {}).get("is_active") or 0),
		"last_enrolled_on": str((profile or {}).get("last_enrolled_on") or "") or None,
		"transcript_preview": (profile or {}).get("transcript_preview"),
		"last_anti_spoof_score": flt((profile or {}).get("last_anti_spoof_score") or 0),
		"last_speech_match_score": flt((profile or {}).get("last_speech_match_score") or 0),
		"last_speaker_match_score": flt((profile or {}).get("last_speaker_match_score") or 0),
	}


def issue_voice_challenge(employee, ttl_seconds):
	settings = get_voice_runtime_settings()
	if not settings["enabled"]:
		frappe.throw(_("Voice verification is disabled in Saudi HR Settings."))

	ttl_seconds = max(30, int(ttl_seconds or 300))
	challenge_text = "".join(secrets.choice("0123456789") for _ in range(4))
	token = secrets.token_urlsafe(24)
	frappe.cache().set_value(
		_voice_cache_key(token),
		json.dumps(
			{
				"employee": employee,
				"challenge_text": challenge_text,
				"issued_at": str(now_datetime()),
			}
		),
		expires_in_sec=ttl_seconds,
	)
	return {
		"challenge_token": token,
		"challenge_text": challenge_text,
		"issued_at": str(now_datetime()),
		"ttl_seconds": ttl_seconds,
	}


def enroll_employee_voice_profile(employee, voice_payload, challenge_token):
	settings = get_voice_runtime_settings()
	if not settings["enabled"]:
		frappe.throw(_("Voice verification is disabled in Saudi HR Settings."))
	profile_status = get_employee_voice_profile_status(employee)
	if profile_status.get("profile_exists") and not profile_status.get("can_self_enroll"):
		frappe.throw(
			_(
				"البصمة الصوتية مسجلة لهذا الموظف ولا يمكن تغييرها من صفحة الحضور. اطلب من الموارد البشرية إعادة التهيئة أولاً."
			),
			frappe.PermissionError,
		)

	verification = _run_voice_verification(
		employee,
		voice_payload,
		challenge_token,
		require_enrollment=False,
	)
	profile = _get_or_create_voice_profile(employee)
	profile.voiceprint_embedding = json.dumps(verification["embedding"])
	profile.enrollment_status = VOICE_PROFILE_STATUS_ENROLLED
	profile.is_active = 1
	profile.last_enrolled_on = now_datetime()
	profile.transcript_preview = verification["transcript"][:140] if verification["transcript"] else None
	profile.last_challenge_text = verification["challenge_text"]
	profile.last_anti_spoof_score = verification["anti_spoof_score"]
	profile.last_speech_match_score = verification["speech_match_score"]
	profile.last_speaker_match_score = verification.get("speaker_match_score") or 0
	profile.flags.ignore_permissions = True
	if profile.is_new():
		profile.insert()
	else:
		profile.save()

	return {
		"profile_name": profile.name,
		"status": profile.enrollment_status,
		"challenge_text": verification["challenge_text"],
		"transcript": verification["transcript"],
		"anti_spoof_score": verification["anti_spoof_score"],
		"speech_match_score": verification["speech_match_score"],
		"speaker_match_score": verification.get("speaker_match_score") or 0,
	}


@frappe.whitelist()
def reset_employee_voice_profile(profile_name=None, employee=None):
	frappe.only_for(VOICE_PROFILE_RESET_ROLES)
	if not profile_name and not employee:
		frappe.throw(_("حدد البصمة الصوتية أو الموظف المطلوب إعادة تهيئته."))

	target_name = profile_name or employee
	if employee and not profile_name:
		target_name = frappe.db.exists("Saudi Employee Voice Profile", employee)
	if not target_name:
		frappe.throw(_("لا توجد بصمة صوتية مرتبطة بهذا الموظف."), frappe.DoesNotExistError)

	profile = frappe.get_doc("Saudi Employee Voice Profile", target_name)
	profile.voiceprint_embedding = None
	profile.is_active = 0
	profile.enrollment_status = VOICE_PROFILE_STATUS_NOT_ENROLLED
	profile.last_enrolled_on = None
	profile.transcript_preview = None
	profile.last_challenge_text = None
	profile.last_anti_spoof_score = None
	profile.last_speech_match_score = None
	profile.last_speaker_match_score = None
	profile.flags.ignore_permissions = True
	profile.save()
	frappe.db.commit()

	return {
		"name": profile.name,
		"employee": profile.employee,
		"status": profile.enrollment_status,
		"message": _("تمت إعادة تهيئة البصمة الصوتية، ويمكن تسجيلها من جديد من صفحة الحضور."),
	}


def verify_checkin_voice(employee, voice_payload, challenge_token):
	return _run_voice_verification(employee, voice_payload, challenge_token, require_enrollment=True)


def _voice_cache_key(token):
	return f"saudi_hr:voice_challenge:{token}"


def _consume_voice_challenge(employee, challenge_token):
	if not challenge_token:
		frappe.throw(_("ابدأ تحديًا صوتيًا جديدًا قبل تسجيل أو التحقق."), frappe.PermissionError)

	key = _voice_cache_key(challenge_token)
	payload = frappe.cache().get_value(key)
	frappe.cache().delete_value(key)
	if not payload:
		frappe.throw(_("انتهت صلاحية التحدي الصوتي. اطلب تحديًا جديدًا."), frappe.PermissionError)

	if isinstance(payload, bytes):
		payload = payload.decode("utf-8")
	if isinstance(payload, str):
		payload = json.loads(payload)

	if payload.get("employee") != employee:
		frappe.throw(_("التحدي الصوتي لا يخص هذا المستخدم."), frappe.PermissionError)

	return payload


def _ensure_torch_amp_compatibility(torch):
	amp_module = getattr(torch, "amp", None)
	if not amp_module:
		return

	def _noop_amp_wrapper(function=None, *_args, **_kwargs):
		if callable(function):
			return function

		def _decorator(inner_function):
			return inner_function

		return _decorator

	if not hasattr(amp_module, "custom_fwd"):
		amp_module.custom_fwd = _noop_amp_wrapper
	if not hasattr(amp_module, "custom_bwd"):
		amp_module.custom_bwd = _noop_amp_wrapper


def _load_runtime_libraries():
	try:
		import torch
		import torchaudio
		_ensure_torch_amp_compatibility(torch)
		from faster_whisper import WhisperModel
		from speechbrain.inference.classifiers import AudioClassifier
		from speechbrain.inference.speaker import SpeakerRecognition
	except ModuleNotFoundError:
		frappe.throw(
			_("Voice verification runtime is not installed yet. Install torch, torchaudio, speechbrain, and faster-whisper first.")
		)

	_sanitize_speechbrain_lazy_modules()

	return {
		"torch": torch,
		"torchaudio": torchaudio,
		"WhisperModel": WhisperModel,
		"AudioClassifier": AudioClassifier,
		"SpeakerRecognition": SpeakerRecognition,
	}


def _run_voice_verification(employee, voice_payload, challenge_token, require_enrollment):
	if not voice_payload:
		frappe.throw(_("لم يتم إرسال عينة صوتية صالحة."), frappe.PermissionError)

	challenge = _consume_voice_challenge(employee, challenge_token)
	runtime = _load_runtime_libraries()
	settings = get_voice_runtime_settings()
	audio_path = _write_voice_temp_file(voice_payload)

	try:
		waveform = _load_waveform(audio_path, runtime)
		anti_spoof_result = _run_anti_spoof(waveform, settings, runtime)
		transcript_result = _transcribe_audio(audio_path, settings, runtime)
		speech_match_score = _calculate_speech_match_score(
			challenge.get("challenge_text"), transcript_result.get("transcript")
		)
		embedding = _extract_speaker_embedding(waveform, settings, runtime)
		speaker_match_score = None

		if require_enrollment:
			profile = _get_existing_voice_profile(employee)
			stored_embedding = _read_embedding(profile, runtime)
			speaker_match_score = _cosine_similarity(embedding, stored_embedding, runtime)

		if not anti_spoof_result["passed"]:
			frappe.throw(_("تم رفض العينة الصوتية لاشتباه الانتحال أو إعادة التشغيل."), frappe.PermissionError)
		if speech_match_score < settings["speech_match_threshold"]:
			frappe.throw(_("الرقم المقروء لا يطابق التحدي الصوتي المطلوب."), frappe.PermissionError)
		if require_enrollment and speaker_match_score < settings["speaker_threshold"]:
			frappe.throw(_("الصوت لا يطابق البصمة الصوتية المسجلة للموظف."), frappe.PermissionError)

		return {
			"challenge_text": challenge.get("challenge_text"),
			"transcript": transcript_result.get("transcript") or "",
			"anti_spoof_score": anti_spoof_result.get("score") or 0,
			"anti_spoof_label": anti_spoof_result.get("label"),
			"speech_match_score": speech_match_score,
			"speaker_match_score": speaker_match_score,
			"embedding": embedding.detach().cpu().reshape(-1).tolist(),
		}
	finally:
		with suppress(OSError):
			os.remove(audio_path)


def _write_voice_temp_file(voice_payload):
	content = _decode_audio_bytes((voice_payload or {}).get("content"))
	if not content:
		frappe.throw(_("العينة الصوتية فارغة أو غير قابلة للقراءة."), frappe.PermissionError)

	file_name = (voice_payload or {}).get("filename") or "voice-sample.webm"
	suffix = os.path.splitext(file_name)[1] or ".webm"
	fd, path = tempfile.mkstemp(prefix="saudi-voice-", suffix=suffix)
	with os.fdopen(fd, "wb") as handle:
		handle.write(content)
	return path


def _decode_audio_bytes(content):
	if not content:
		return b""
	if "," in content and ";base64" in content.split(",", 1)[0]:
		content = content.split(",", 1)[1]
	return base64.b64decode(content)


def _load_waveform(audio_path, runtime):
	waveform, sample_rate = runtime["torchaudio"].load(audio_path)
	if waveform.ndim == 1:
		waveform = waveform.unsqueeze(0)
	if waveform.shape[0] > 1:
		waveform = waveform.mean(dim=0, keepdim=True)
	if sample_rate != 16000:
		waveform = runtime["torchaudio"].functional.resample(waveform, sample_rate, 16000)
	return waveform


def _transcribe_audio(audio_path, settings, runtime):
	model = _get_cached_model(
		("whisper", settings["whisper_model_size"], settings["compute_type"]),
		lambda: runtime["WhisperModel"](
			settings["whisper_model_size"],
			device="cpu",
			compute_type=settings["compute_type"],
		),
	)
	segments, info = model.transcribe(
		audio_path,
		beam_size=5,
		condition_on_previous_text=False,
		language=settings["voice_language"] or None,
		vad_filter=True,
	)
	transcript = " ".join(segment.text.strip() for segment in segments if segment.text).strip()
	return {
		"transcript": transcript,
		"language": getattr(info, "language", settings["voice_language"]),
	}


def _run_anti_spoof(waveform, settings, runtime):
	source = settings["anti_spoof_model_source"]
	if not source:
		return {"passed": True, "score": 1.0, "label": "unconfigured"}

	model = _get_cached_model(
		("anti_spoof", source),
		lambda: runtime["AudioClassifier"].from_hparams(
			source=source,
			savedir=_model_savedir("anti-spoof", source),
		),
	)
	out_prob, score, _index, labels = model.classify_batch(waveform)
	del out_prob
	label = _normalize_label(labels)
	score_value = _tensor_to_float(score)
	passed = label in settings["bonafide_labels"] if label else False
	if not passed and score_value is not None and score_value >= settings["anti_spoof_threshold"]:
		passed = True
	return {"passed": passed, "score": score_value, "label": label}


def _extract_speaker_embedding(waveform, settings, runtime):
	model = _get_cached_model(
		("speaker", settings["speaker_model_source"]),
		lambda: runtime["SpeakerRecognition"].from_hparams(
			source=settings["speaker_model_source"],
			savedir=_model_savedir("speaker", settings["speaker_model_source"]),
		),
	)
	return model.encode_batch(waveform, normalize=True).reshape(-1)


def _calculate_speech_match_score(challenge_text, transcript):
	expected = _normalize_spoken_digits(challenge_text)
	observed = _normalize_spoken_digits(transcript)
	if not expected or not observed:
		return 0.0
	if expected == observed:
		return 1.0
	return difflib.SequenceMatcher(a=expected, b=observed).ratio()


def _normalize_spoken_digits(text):
	text = (text or "").lower().translate(_ARABIC_NUMERAL_TRANSLATION)
	tokens = re.findall(r"[0-9]+|[a-zA-Z\u0600-\u06ff]+", text)
	digits = []
	for token in tokens:
		if token.isdigit():
			digits.extend(list(token))
			continue
		mapped = _DIGIT_WORDS.get(token)
		if mapped is not None:
			digits.append(mapped)
	return "".join(digits)


def _get_or_create_voice_profile(employee):
	profile = frappe.get_doc("Saudi Employee Voice Profile", employee) if frappe.db.exists(
		"Saudi Employee Voice Profile", employee
	) else frappe.new_doc("Saudi Employee Voice Profile")
	if profile.is_new():
		profile.employee = employee
	return profile


def _get_existing_voice_profile(employee):
	if not frappe.db.exists("Saudi Employee Voice Profile", employee):
		frappe.throw(_("لا توجد بصمة صوتية مسجلة لهذا الموظف. ابدأ التسجيل الصوتي أولاً."), frappe.PermissionError)
	profile = frappe.get_doc("Saudi Employee Voice Profile", employee)
	if profile.enrollment_status != VOICE_PROFILE_STATUS_ENROLLED or not profile.is_active or not profile.voiceprint_embedding:
		frappe.throw(_("البصمة الصوتية الحالية غير مفعلة أو غير مكتملة."), frappe.PermissionError)
	return profile


def _read_embedding(profile, runtime):
	data = json.loads(profile.voiceprint_embedding or "[]")
	if not data:
		frappe.throw(_("البصمة الصوتية المخزنة غير صالحة."), frappe.PermissionError)
	return runtime["torch"].tensor(data)


def _cosine_similarity(left, right, runtime):
	return float(runtime["torch"].nn.functional.cosine_similarity(left.reshape(1, -1), right.reshape(1, -1)).item())


def _tensor_to_float(value):
	if value is None:
		return None
	if hasattr(value, "detach"):
		value = value.detach().cpu().reshape(-1)
		if value.numel() == 0:
			return None
		return float(value[0].item())
	return float(value)


def _normalize_label(labels):
	if isinstance(labels, (list, tuple)) and labels:
		first = labels[0]
		if isinstance(first, (list, tuple)) and first:
			first = first[0]
		return str(first or "").strip().lower()
	return str(labels or "").strip().lower()


def _model_savedir(component, source):
	path = frappe.get_site_path("private", "voice-model-cache", component, source.replace("/", "__"))
	os.makedirs(path, exist_ok=True)
	return path


def _get_cached_model(cache_key, factory):
	if cache_key not in _MODEL_CACHE:
		_MODEL_CACHE[cache_key] = factory()
	return _MODEL_CACHE[cache_key]