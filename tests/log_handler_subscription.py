from mock import MagicMock, patch, call
import log_handler_subscription
import unittest
import os
import json
import boto3
import botocore
from botocore.stub import Stubber


class TestLambda(unittest.TestCase):

    def setUp(self):
        self.log_group_name_prefix = '/aws/prefix/'
        self.log_group_names = [
            self.log_group_name_prefix + 'group_1',
            self.log_group_name_prefix + 'group_2',
            'group_3'
        ]
        self.log_handler_arn = '12345678A'


    def test_get_lambda_log_groups(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(dir_path + "/test-data/log-group-response.json") as json_data:
            lambda_client = MagicMock()
            lambda_client.describe_log_groups.return_value = json.load(json_data)
            response = log_handler_subscription.get_log_group_names(lambda_client)

            lambda_client.describe_log_groups.assert_called_once_with()
            self.assertEqual(response, self.log_group_names)

    def test_get_log_handler_arn(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(dir_path + "/test-data/log_handler.json") as json_data:
            lambda_client = MagicMock()
            lambda_client.get_function_configuration.return_value = json.load(json_data)
            response = log_handler_subscription.get_log_handler_arn(lambda_client)

            lambda_client.get_function_configuration.assert_called_once_with(FunctionName='log_handler')
            self.assertEqual(response, self.log_handler_arn)

    def test_create_subscription_filters(self):
        log_client = MagicMock()
        log_handler_subscription.create_subscription_filters(log_client, self.log_group_names, self.log_handler_arn)
        calls = [
            call(logGroupName=self.log_group_name_prefix + 'group_1', filterName='group_1-log-handler-lambda-subscription', filterPattern='', destinationArn=self.log_handler_arn),
            call(logGroupName=self.log_group_name_prefix + 'group_2', filterName='group_2-log-handler-lambda-subscription', filterPattern='', destinationArn=self.log_handler_arn),
            call(logGroupName='group_3', filterName='group_3-log-handler-lambda-subscription', filterPattern='', destinationArn=self.log_handler_arn)
        ]

        log_client.put_subscription_filter.assert_has_calls(calls, any_order=True)

    def test_subsciption_filters_name_ending_in_slash(self):
        log_client = MagicMock()
        log_handler_subscription.create_subscription_filters(log_client, {'/weird_name/'}, self.log_handler_arn)
        calls = [
            call(logGroupName='/weird_name/', filterName='weird_name-log-handler-lambda-subscription', filterPattern='', destinationArn=self.log_handler_arn)
        ]

        log_client.put_subscription_filter.assert_has_calls(calls, any_order=True)

    def test_subscription_filters_already_exist_for_log_group(self):
        log_client = boto3.client('logs')
        stubber = Stubber(log_client)
        stubber.activate()
        params = {'logGroupName': 'logGroup', 'filterName': 'logGroup-log-handler-lambda-subscription', 'filterPattern': '', 'destinationArn': self.log_handler_arn}
        stubber.add_client_error(method='put_subscription_filter', service_error_code='LimitExceededException', expected_params=params)
        log_handler_subscription.create_subscription_filters(log_client, ['logGroup'], self.log_handler_arn)

        stubber.assert_no_pending_responses()
        stubber.deactivate()

    def test_subscription_filters_sending_loggers_log_group(self):
        log_client = boto3.client('logs')
        stubber = Stubber(log_client)
        stubber.activate()
        success_params = {'logGroupName': 'logGroup2', 'filterName': 'logGroup2-log-handler-lambda-subscription', 'filterPattern': '', 'destinationArn': self.log_handler_arn}
        stubber.add_response(method='put_subscription_filter', service_response={}, expected_params=success_params)
        error_params = {'logGroupName': 'logGroup', 'filterName': 'logGroup-log-handler-lambda-subscription', 'filterPattern': '', 'destinationArn': self.log_handler_arn}
        stubber.add_client_error(method='put_subscription_filter', service_error_code='InvalidParameterException', expected_params=error_params)
        log_handler_subscription.create_subscription_filters(log_client, ['logGroup2', 'logGroup'], self.log_handler_arn)

        stubber.assert_no_pending_responses()
        stubber.deactivate()

    def test_subscription_filters_uncaught_exception(self):
        log_client = boto3.client('logs')
        stubber = Stubber(log_client)
        stubber.activate()

        error_params = {'logGroupName': 'logGroup', 'filterName': 'logGroup-log-handler-lambda-subscription', 'filterPattern': '', 'destinationArn': self.log_handler_arn}
        stubber.add_client_error(method='put_subscription_filter', service_error_code='RandomError', expected_params=error_params)
        success_params = {'logGroupName': 'logGroup2', 'filterName': 'logGroup2-log-handler-lambda-subscription', 'filterPattern': '', 'destinationArn': self.log_handler_arn}
        stubber.add_response(method='put_subscription_filter', service_response={}, expected_params=success_params)

        try:
            log_handler_subscription.create_subscription_filters(log_client, ['logGroup', 'logGroup2'], self.log_handler_arn)
        except botocore.exceptions.ClientError as e:
            self.assertEqual(e.response['Error']['Code'], 'RandomError')

        self.assertEqual(len(stubber._queue), 1)
        stubber.deactivate()
