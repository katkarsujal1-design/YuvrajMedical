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
