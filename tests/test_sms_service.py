import os
import unittest
from unittest import mock

from services import sms_service


class SmsServiceTests(unittest.TestCase):
    def test_normalize_indian_phone_accepts_common_formats(self):
        cases = {
            "9876543210": "+919876543210",
            "+919876543210": "+919876543210",
            "919876543210": "+919876543210",
            "00919876543210": "+919876543210",
        }
        for raw, normalized in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(sms_service.normalize_indian_phone(raw), normalized)

    def test_normalize_indian_phone_rejects_invalid_values(self):
        for raw in ["", "12345", "+911234567890", "abcdef9876"]:
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    sms_service.normalize_indian_phone(raw)

    def test_send_otp_uses_test_mode_without_provider_call(self):
        with mock.patch.dict(os.environ, {"SMS_ENABLED": "false"}, clear=False):
            result = sms_service.send_otp("9876543210", purpose="register_account")
        self.assertTrue(result.ok)
        self.assertTrue(result.session_id)
        self.assertEqual(result.provider_status, "test")

    def test_verify_otp_uses_test_code_when_sms_disabled(self):
        with mock.patch.dict(os.environ, {"SMS_ENABLED": "false", "SMS_TEST_OTP": "654321"}, clear=False):
            self.assertTrue(sms_service.verify_otp("test-session", "654321").ok)
            self.assertFalse(sms_service.verify_otp("test-session", "111111").ok)

    def test_send_manual_otp_uses_2factor_template_url(self):
        env = {
            "SMS_ENABLED": "true",
            "TWOFACTOR_API_KEY": "test-key",
            "TWOFACTOR_OTP_TRANSPORT": "otp_sms",
            "TWOFACTOR_OTP_TEMPLATE": "LOGIN_TEMPLATE",
            "TWOFACTOR_LEGACY_URL": "https://2factor.in/API/V1",
        }
        with mock.patch.dict(os.environ, env, clear=False), mock.patch.object(
            sms_service, "_post_empty_json", return_value={"Status": "Success", "Details": "ok"}
        ) as provider_call:
            result = sms_service.send_manual_otp("+919876543210", "654321", purpose="register_account")

        self.assertTrue(result.ok)
        provider_call.assert_called_once_with(
            "https://2factor.in/API/V1/test-key/SMS/9876543210/654321/LOGIN_TEMPLATE"
        )

    def test_send_manual_otp_accepts_queued_provider_status(self):
        env = {
            "SMS_ENABLED": "true",
            "TWOFACTOR_API_KEY": "test-key",
            "TWOFACTOR_OTP_TRANSPORT": "otp_sms",
        }
        with mock.patch.dict(os.environ, env, clear=False), mock.patch.object(
            sms_service, "_post_empty_json", return_value={"Status": "Queued", "Details": "queued"}
        ):
            result = sms_service.send_manual_otp("9876543210", "654321")

        self.assertTrue(result.ok)
        self.assertEqual(result.provider_status, "queued")

    def test_transactional_sms_skips_provider_when_disabled(self):
        with mock.patch.dict(os.environ, {"SMS_ENABLED": "false"}, clear=False):
            result = sms_service.send_transactional_sms(
                "9876543210",
                sms_service.render_sms_template("order_delivered", order_id=123),
                template_key="order_delivered",
            )
        self.assertTrue(result.ok)
        self.assertEqual(result.provider_status, "test")


if __name__ == "__main__":
    unittest.main()
