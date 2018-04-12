from mock import MagicMock, patch, call
import log_handler_subscription
import unittest
import os


class TestLambda(unittest.TestCase):

    def setUp(self):
        self.log_group_name_prefix = '/aws/prefix/'
        self.log_group_names = {
            self.log_group_name_prefix + 'group_1',
            self.log_group_name_prefix + 'group_2',
            'group_3'
        }
        self.log_handler_arn = '12345678A'


    def test_get_lambda_log_groups(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(dir_path + "/test-data/log-group-response.json") as json_data:
            lambda_client = MagicMock()
            lambda_client.describe_log_groups.return_value = json_data
            response = log_handler_subscription.get_log_group_names(lambda_client)

            lambda_client.describe_log_groups.assert_called_once_with()
            self.assertEqual(response, self.log_group_names)

    def test_get_log_groups_with_subscription_filters(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(dir_path + "/test-data/subscription-filters-response.json") as json_data:
            lambda_client = MagicMock()
            lambda_client.describe_subscription_filters.return_value = json_data
            response = log_handler_subscription.get_log_groups_with_subscription_filters(lambda_client)

            lambda_client.describe_subscription_filters.assert_called_once_with()
            self.assertEqual(response, {self.log_group_name_prefix + 'group_1'})

    def test_groups_with_no_subscriptions(self):
        result = log_handler_subscription.log_groups_with_no_subscriptions(self.log_group_names, {'/aws/prefix/group_2'})

        self.assertEqual(result, {self.log_group_name_prefix + 'group_1', 'group_3'})

    def test_get_log_handler_arn(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(dir_path + "/test-data/log_handler.json") as json_data:
            lambda_client = MagicMock()
            lambda_client.get_function.return_value = json_data
            response = log_handler_subscription.get_log_handler_arn(lambda_client)

            lambda_client.get_function.assert_called_once_with(FunctionName='log_handler')
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