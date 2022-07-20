import json
import os
import unittest

import boto3
import botocore
from botocore.exceptions import ClientError
from botocore.stub import Stubber
from mock import call
from mock import MagicMock

import log_handler_subscription


class TestLambda(unittest.TestCase):
    def setUp(self):
        try:
            del os.environ["EXCLUDED_LOG_GROUPS"]
        except KeyError:
            pass
        self.log_group_name_prefix = "/aws/prefix/"
        self.log_group_names = [
            self.log_group_name_prefix + "group_1",
            self.log_group_name_prefix + "group_2",
            "group_3",
        ]
        self.log_handler_arn = "12345678A"

    def test_get_lambda_log_groups_with_pagination(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(dir_path + "/test-data/log-group-response.json") as json_data_1:
            with open(
                dir_path + "/test-data/log-group-response-no-token.json"
            ) as json_data_2:
                lambda_client = MagicMock()
                lambda_client.describe_log_groups.side_effect = [
                    json.load(json_data_1),
                    json.load(json_data_2),
                ]
                response = log_handler_subscription.get_log_group_names(
                    lambda_client, [], None
                )

                lambda_client.describe_log_groups.assert_has_calls(
                    [call(), call(nextToken="abcd")]
                )
                self.assertEqual(response, self.log_group_names + ["group_4"])

    def test_get_lambda_log_groups_without_pagination(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(
            dir_path + "/test-data/log-group-response-no-token.json"
        ) as json_data:
            lambda_client = MagicMock()
            lambda_client.describe_log_groups.return_value = json.load(json_data)
            response = log_handler_subscription.get_log_group_names(
                lambda_client, [], None
            )

            lambda_client.describe_log_groups.assert_called_once_with()
            self.assertEqual(response, ["group_4"])

    def test_get_log_handler_arn(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(dir_path + "/test-data/log_handler.json") as json_data:
            lambda_client = MagicMock()
            lambda_client.get_function_configuration.return_value = json.load(json_data)
            response = log_handler_subscription.get_log_handler_arn(lambda_client)

            lambda_client.get_function_configuration.assert_called_once_with(
                FunctionName="log_handler"
            )
            self.assertEqual(response, self.log_handler_arn)

    def test_create_subscription_filters(self):
        log_client = MagicMock()
        log_handler_subscription.create_subscription_filters(
            log_client, self.log_group_names, self.log_handler_arn
        )
        calls = [
            call(
                logGroupName=self.log_group_name_prefix + "group_1",
                filterName="group_1-log-handler-lambda-subscription",
                filterPattern="",
                destinationArn=self.log_handler_arn,
            ),
            call(
                logGroupName=self.log_group_name_prefix + "group_2",
                filterName="group_2-log-handler-lambda-subscription",
                filterPattern="",
                destinationArn=self.log_handler_arn,
            ),
            call(
                logGroupName="group_3",
                filterName="group_3-log-handler-lambda-subscription",
                filterPattern="",
                destinationArn=self.log_handler_arn,
            ),
        ]

        log_client.put_subscription_filter.assert_has_calls(calls, any_order=True)
        assert 3 == log_client.put_subscription_filter.call_count

    def test_create_subscription_filters_excludes_the_requested_log_groups(self):
        log_client = MagicMock()
        os.environ[
            "EXCLUDED_LOG_GROUPS"
        ] = "mdtp-log-flows,psn-log-flows,hmrc_core_connectivity-flow-logs"
        self.log_group_names.extend(
            ["mdtp-log-flows", "psn-log-flows", "hmrc_core_connectivity-flow-logs"]
        )
        log_handler_subscription.create_subscription_filters(
            log_client, self.log_group_names, self.log_handler_arn
        )
        calls = [
            call(
                logGroupName=self.log_group_name_prefix + "group_1",
                filterName="group_1-log-handler-lambda-subscription",
                filterPattern="",
                destinationArn=self.log_handler_arn,
            ),
            call(
                logGroupName=self.log_group_name_prefix + "group_2",
                filterName="group_2-log-handler-lambda-subscription",
                filterPattern="",
                destinationArn=self.log_handler_arn,
            ),
            call(
                logGroupName="group_3",
                filterName="group_3-log-handler-lambda-subscription",
                filterPattern="",
                destinationArn=self.log_handler_arn,
            ),
        ]

        log_client.put_subscription_filter.assert_has_calls(calls, any_order=True)
        assert 3 == log_client.put_subscription_filter.call_count

    def test_subsciption_filters_name_ending_in_slash(self):
        log_client = MagicMock()
        log_handler_subscription.create_subscription_filters(
            log_client, {"/weird_name/"}, self.log_handler_arn
        )
        calls = [
            call(
                logGroupName="/weird_name/",
                filterName="weird_name-log-handler-lambda-subscription",
                filterPattern="",
                destinationArn=self.log_handler_arn,
            )
        ]

        log_client.put_subscription_filter.assert_has_calls(calls, any_order=True)

    def test_subscription_filters_already_exist_for_log_group(self):
        log_client = boto3.client("logs")
        stubber = Stubber(log_client)
        stubber.activate()
        params = {
            "logGroupName": "logGroup",
            "filterName": "logGroup-log-handler-lambda-subscription",
            "filterPattern": "",
            "destinationArn": self.log_handler_arn,
        }
        stubber.add_client_error(
            method="put_subscription_filter",
            service_error_code="LimitExceededException",
            expected_params=params,
        )
        log_handler_subscription.create_subscription_filters(
            log_client, ["logGroup"], self.log_handler_arn
        )

        stubber.assert_no_pending_responses()
        stubber.deactivate()

    def test_subscription_filters_sending_loggers_log_group(self):
        log_client = boto3.client("logs")
        stubber = Stubber(log_client)
        stubber.activate()
        success_params = {
            "logGroupName": "logGroup2",
            "filterName": "logGroup2-log-handler-lambda-subscription",
            "filterPattern": "",
            "destinationArn": self.log_handler_arn,
        }
        stubber.add_response(
            method="put_subscription_filter",
            service_response={},
            expected_params=success_params,
        )
        error_params = {
            "logGroupName": "logGroup",
            "filterName": "logGroup-log-handler-lambda-subscription",
            "filterPattern": "",
            "destinationArn": self.log_handler_arn,
        }
        stubber.add_client_error(
            method="put_subscription_filter",
            service_error_code="InvalidParameterException",
            expected_params=error_params,
        )
        log_handler_subscription.create_subscription_filters(
            log_client, ["logGroup2", "logGroup"], self.log_handler_arn
        )

        stubber.assert_no_pending_responses()
        stubber.deactivate()

    def test_subscription_filters_uncaught_exception(self):
        log_client = boto3.client("logs")
        stubber = Stubber(log_client)
        stubber.activate()

        error_params = {
            "logGroupName": "logGroup",
            "filterName": "logGroup-log-handler-lambda-subscription",
            "filterPattern": "",
            "destinationArn": self.log_handler_arn,
        }
        stubber.add_client_error(
            method="put_subscription_filter",
            service_error_code="RandomError",
            expected_params=error_params,
        )
        success_params = {
            "logGroupName": "logGroup2",
            "filterName": "logGroup2-log-handler-lambda-subscription",
            "filterPattern": "",
            "destinationArn": self.log_handler_arn,
        }
        stubber.add_response(
            method="put_subscription_filter",
            service_response={},
            expected_params=success_params,
        )

        try:
            log_handler_subscription.create_subscription_filters(
                log_client, ["logGroup", "logGroup2"], self.log_handler_arn
            )
        except botocore.exceptions.ClientError as e:
            self.assertEqual(e.response["Error"]["Code"], "RandomError")

        self.assertEqual(len(stubber._queue), 1)
        stubber.deactivate()
