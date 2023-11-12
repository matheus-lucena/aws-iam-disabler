import boto3
from datetime import datetime

from utils import log

class IamService:

    def __init__(self):
        self.client = boto3.client('iam')
        self.logger = log.get_logger('IamService')

    def get_users(self):
        self.logger.info('get users')
        paginator = self.client.get_paginator('list_users')
        iam_users = []
        for page in paginator.paginate():
            response_metadata = page['ResponseMetadata']
            if response_metadata['HTTPStatusCode'] != 200:
                self.logger.error(f'error to get users, aws_error={response_metadata}')
            iam_users.extend(page['Users'])
        list_username = [user['UserName'] for user in iam_users]
        self.logger.info(f'recupered {len(iam_users)} users, usernames={list_username}')
        return iam_users

    def get_access_keys(self):
        access_keys = []
        for user in self.get_users():
            username = user['UserName']
            arn = user['Arn']
            response = self.client.list_access_keys(UserName=username)
            response_metadata = response['ResponseMetadata']
            if response_metadata['HTTPStatusCode'] != 200:
                self.logger.error(f'error to get access keys to user={arn}, aws_error={response_metadata}')
            access_keys.extend(response['AccessKeyMetadata'])
        list_access_keys_id = [user['AccessKeyId'] for user in access_keys]
        self.logger.info(f'recupered {len(access_keys)} access keys, access_key_ids={list_access_keys_id}')
        return access_keys
    
    def get_old_usage_access_keys(self, days):
        datetime_now = datetime.now()
        old_access_keys = []
        active_access_keys = [access_key for access_key in self.get_access_keys() if access_key['Status'] == 'Active']
        for access_key in active_access_keys:
            access_key_id = access_key['AccessKeyId']
            username = access_key['UserName']
            response = self.client.get_access_key_last_used(
                AccessKeyId=access_key_id
            )
            response_metadata = response['ResponseMetadata']
            if response_metadata['HTTPStatusCode'] != 200:
                self.logger.error(f'error to get access_key_id={access_key_id}, aws_error={response_metadata}')
            last_used = response['AccessKeyLastUsed']
            if 'LastUsedDate' in last_used:
                last_use_days = (datetime_now - last_used['LastUsedDate'].replace(tzinfo=None)).days
            else:
                last_use_days = (datetime_now - access_key['CreateDate'].replace(tzinfo=None)).days

            if last_use_days > days:
                self.logger.info(f'identified old access_key_id={access_key_id}, username={username}')
                old_access_keys.append({
                    'id': access_key_id,
                    'username': username,
                    **last_used
                })
        return old_access_keys
    
    def disable_old_access_keys(self, days):
        for item in self.get_old_usage_access_keys(days):
            username = item['username']
            id = item['id']
            response = self.client.update_access_key(
                UserName=username,
                AccessKeyId=id,
                Status='Inactive'
            )
            response_metadata = response['ResponseMetadata']
            if response_metadata['HTTPStatusCode'] != 200:
                self.logger.error(f'error to disable access_key_id={id}, username={username} aws_error={response_metadata}')
            self.logger.info(f'access_key_id={id}, username={username} disabled')
        
    