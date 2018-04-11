from mock import MagicMock, patch, call
import log_handler_subscription as log_handler
import unittest
import os


class TestLambda(unittest.TestCase):

    def setUp(self):
        self.log_group_name_prefix = '/aws/prefix/'
        self.log_group_names = set([
            self.log_group_name_prefix + 'group_1',
            self.log_group_name_prefix + 'group_2',
            self.log_group_name_prefix + 'group_3'
        ])


    def test_get_lambda_log_groups(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(dir_path + "/test-data/log-group-response.json") as json_data:
            lambda_client = MagicMock()
            lambda_client.describe_log_groups.return_value = json_data
            response = log_handler.get_lambda_log_group_names(lambda_client)

            lambda_client.describe_log_groups.assert_called_once_with()
            self.assertEqual(response, self.log_group_names)

    def test_get_log_groups_with_subscription_filters(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(dir_path + "/test-data/subscription-filters-response.json") as json_data:
            lambda_client = MagicMock()
            lambda_client.describe_subscription_filters.return_value = json_data
            response = log_handler.get_log_groups_with_subscription_filters(lambda_client)

            lambda_client.describe_subscription_filters.assert_called_once_with()
            self.assertEqual(response, set([self.log_group_name_prefix + 'group_1']))

