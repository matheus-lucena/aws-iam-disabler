import boto3
from services.iam import IamService
from moto import mock_iam, mock_ec2
import datetime as datetime
from freezegun import freeze_time
import random
import string

import unittest
import pytest

from utils.env import DISABLE_ACCESS_KEY_DAYS

today = datetime.date.today()


@mock_iam
@mock_ec2
class TestIAM(unittest.TestCase):

    def setUp(self):
        self.iam_service = IamService()
        self.users = []
        self.active_access_keys = []
        self.inactive_access_keys = []
        self.old_active_access_keys = []
        self.create_iam_with_days(120, used=True)
        self.create_iam_with_days(10, used=True)
        self.create_iam_with_days(90, used=True, active=False)
        self.create_iam_with_days(10, used=False)

    def create_iam_with_days(self, days: int, used=False, active=True):
        with freeze_time(today - datetime.timedelta(days=days)):
            for _ in range(10):
                client = boto3.client('iam')
                username = ''.join(random.choices(string.ascii_lowercase, k=5))

                response = client.create_user(
                    UserName=username
                )

                response = client.create_access_key(
                    UserName=username
                )
                access_key = response['AccessKey']
                access_key_id = access_key['AccessKeyId']
                if days > DISABLE_ACCESS_KEY_DAYS and active:
                    self.old_active_access_keys.append(access_key_id)
                if used:
                    ec2_client = boto3.client(
                        'ec2',
                        aws_access_key_id=access_key_id,
                        aws_secret_access_key=access_key['SecretAccessKey'])

                    ec2_client.describe_instances()
                if not active:
                    response = client.update_access_key(
                        UserName=username,
                        AccessKeyId=access_key_id,
                        Status='Inactive'
                    )
                    self.inactive_access_keys.append(access_key_id)
                else:
                    self.active_access_keys.append(access_key_id)
                self.users.append(username)

    @pytest.mark.order(1)
    def test_iam_users(self):
        response = self.iam_service.get_users()
        users = [user['UserName'] for user in response]
        assert self.users == users

    @pytest.mark.order(2)
    def test_inactive_access_key(self):
        response = self.iam_service.get_access_keys()
        access_key_ids = [item['AccessKeyId'] for item in response if item['Status'] == 'Inactive']
        assert access_key_ids.sort() == self.inactive_access_keys.sort()

    @pytest.mark.order(3)
    def test_active_access_key(self):
        response = self.iam_service.get_access_keys()
        access_key_ids = [item['AccessKeyId'] for item in response
                          if item['Status'] == 'Active']
        assert access_key_ids.sort() == self.active_access_keys.sort()

    @pytest.mark.order(4)
    def test_get_old_access_key(self):
        response = self.iam_service.get_old_usage_access_keys(DISABLE_ACCESS_KEY_DAYS)
        access_key_ids = [item['id'] for item in response]
        assert access_key_ids.sort() == self.old_active_access_keys.sort()

    @pytest.mark.order(5)
    def test_disable_old_access_keys(self):
        self.iam_service.disable_old_access_keys(DISABLE_ACCESS_KEY_DAYS)
        assert len(self.iam_service.get_old_usage_access_keys(DISABLE_ACCESS_KEY_DAYS)) == 0
