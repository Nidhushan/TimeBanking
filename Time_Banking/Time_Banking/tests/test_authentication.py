from django.core import mail
from django.contrib import auth
from django.test import TestCase, Client, override_settings
from ..models import User
from django.urls import reverse
from datetime import timedelta
import random
import json


class AuthenticationTests(TestCase):
    
    Old_password = 'OldPassword123!'
    New_password = 'NewPassword123!'
    
    def setUp(self):
        self.client = Client()
        random.seed(10)
        # Create a user for testing
        self.user = User.objects.create_user(
            username="testuser",
            password=self.Old_password,
            email="testuser@example.com",
            is_verified=True
        )
        
    def test_create_account_and_verify_code(self):
        form = {
            "username": "testuser1",
            "email": "example@example.com",
            "password1": self.Old_password,
            "password2": self.Old_password
        }
        response = self.client.post(reverse("create_account"), form)
        self.assertRedirects(response, reverse("verify_account_code"))
        # check mail
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Verify your account")
        self.assertEqual(mail.outbox[0].body, "Your verification code is: 699159")
        # check session data
        session = self.client.session
        self.assertEqual(session["user_data"], form)
        self.assertEqual(session["verification_code"], 699159)
        # verify code (bad)
        response = self.client.post(reverse("verify_account_code"), {"code": 699158})
        self.assertTemplateUsed(response, 'registration/verification_failed.html')
        # verify code (good)
        response = self.client.post(reverse("verify_account_code"), {"code": 699159})
        session = self.client.session
        self.assertRedirects(response, reverse('edit_profile'))   
        self.assertTrue("user_data" not in session)
        self.assertTrue("verification_code" not in session)
        # check user
        user = User.objects.get(username="testuser1")
        self.assertEqual(user.email, "example@example.com")
        self.assertTrue(user.check_password(self.Old_password))

    def test_create_account_and_rerequest_email(self):
        form = {
            "username": "testuser1",
            "email": "example@example.com",
            "password1": self.Old_password,
            "password2": self.Old_password
        }
        response = self.client.post(reverse("create_account"), form)
        self.assertRedirects(response, reverse("verify_account_code"))
        # check mail
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Verify your account")
        self.assertEqual(mail.outbox[0].body, "Your verification code is: 699159")
        # check session data
        session = self.client.session
        self.assertEqual(session["verification_code"], 699159)
        # resend
        response = self.client.get(reverse("resend_verification_email"))
        # check mail
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[1].subject, "Verify your account")
        self.assertEqual(mail.outbox[1].body, "Your new verification code is: 606002")
        # check session data
        session = self.client.session
        self.assertEqual(session["verification_code"], 606002)
        self.assertEqual(session["user_data"], form)

    def test_create_account_invalid_form(self):
        form = {
            "username": "testuser1",
            "email": "example@example.com",
            "password1": self.Old_password,
            "password2": self.New_password
        }
        response = self.client.post(reverse("create_account"), form)
        self.assertTemplateUsed(response, "create-account.html")
        self.assertEqual(response.status_code, 200)
        # check mail
        self.assertEqual(len(mail.outbox), 0)
        # check session data
        session = self.client.session
        self.assertTrue("user_data" not in session)
        self.assertTrue("verification_code" not in session)

    def test_correct_login(self):
        form = {
            "username": "testuser",
            "password": self.Old_password
        }
        response = self.client.post(reverse("login"), form)
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)
        self.assertEqual(user.username, "testuser")

    def test_incorrect_login(self):
        form = {
            "username": "testuser",
            "password": self.New_password
        }
        response = self.client.post(reverse("login"), form)
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)
        self.assertTemplateUsed(response, "registration/login.html")
        self.assertContains(response, "Invalid username or password.")

    def test_unverified_login(self):
        self.client.post(reverse("create_account"), {
            "username": "testuser1",
            "email": "example@example.com",
            "password1": self.Old_password,
            "password2": self.Old_password
        })
        response = self.client.post(reverse("login"), {
            "username": "testuser1",
            "password": self.Old_password
        })
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)
        self.assertTemplateUsed(response, "registration/login.html")
        # self.assertContains(response, "Please verify your email before logging in.")

    def test_forgot_password(self):
        response = self.client.post(reverse("forgot_password"), {
            "email": "testuser@example.com"
        })
        self.assertRedirects(response, reverse("verify_reset_code"))
        # check mail
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Password Reset Code")
        self.assertEqual(mail.outbox[0].body, "Your password reset code is: 699159")
        session = self.client.session
        self.assertEqual(session["reset_code"], 699159)
        # give bad code
        response = self.client.post(reverse("verify_reset_code"), {
            "code": 699158
        })
        self.assertTemplateUsed(response, "registration/verify_reset_code.html")
        self.assertContains(response, "Invalid code.")
        # give good code
        response = self.client.post(reverse("verify_reset_code"), {
            "code": 699159
        })
        self.assertRedirects(response, reverse("reset_password"))
        # give bad passwords
        response = self.client.post(reverse("reset_password"), {
            "new_password": self.Old_password,
            "confirm_password": self.New_password
        })
        self.assertTemplateUsed(response, "registration/reset_password.html")
        self.assertContains(response, "Passwords do not match.")
        # give good passwords
        response = self.client.post(reverse("reset_password"), {
            "new_password": self.New_password,
            "confirm_password": self.New_password
        })
        # login with old password
        self.assertRedirects(response, reverse("login"))
        response = self.client.post(reverse("login"), {
            "username": "testuser",
            "password": self.Old_password
        })
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)
        # login with new password
        response = self.client.post(reverse("login"), {
            "username": "testuser",
            "password": self.New_password
        })
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

    def test_forgot_password_bad_email(self):
        response = self.client.post(reverse("forgot_password"), {
            "email": "example@example.com"
        })
        self.assertTemplateUsed(response, "registration/forgot_password.html")
        self.assertContains(response, "Email not found.")