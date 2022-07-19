#!/usr/bin/env python
import os

import boto3
import pprint

from botocore.config import Config


def lambda_handler(event, context):
    config = Config(
        retries=dict(
            max_attempts=10
        )
    )
    log_client = boto3.client("logs", region_name="eu-west-2", config=config)
    lambda_client = boto3.client("lambda", region_name="eu-west-2")
    log_handler_arn = get_log_handler_arn(lambda_client)
    aws_lambda_log_handler_arn = get_aws_lambda_log_handler_arn(lambda_client)
    log_groups = get_log_group_names(log_client, [], None)
    # create_subscription_filters(log_client, log_groups, log_handler_arn)
    update_subscription_filters(log_client, log_groups, log_handler_arn, aws_lambda_log_handler_arn)


def get_log_group_names(log_client, previous_group_names, next_token):
    response = get_paginated_log_groups(log_client, next_token)
    group_names = previous_group_names + list(
        map(lambda x: x["logGroupName"], response["logGroups"])
    )
    if "nextToken" in response:
        return get_log_group_names(log_client, group_names, response["nextToken"])
    else:
        return group_names


def get_paginated_log_groups(log_client, next_token):
    if next_token:
        return log_client.describe_log_groups(nextToken=next_token)
    else:
        return log_client.describe_log_groups()


def get_log_handler_arn(lambda_client):
    response = lambda_client.get_function_configuration(FunctionName="log_handler_old")
    return response["FunctionArn"]


def get_aws_lambda_log_handler_arn(lambda_client):
    response = lambda_client.get_function_configuration(FunctionName="log_handler")
    return response["FunctionArn"]


def create_subscription_filters(log_client, log_group_names, log_handler_arn):
    excluded_log_group_names = os.getenv("EXCLUDED_LOG_GROUPS", "").split(",")
    for log_group_name in log_group_names:
        if log_group_name in excluded_log_group_names:
            continue
        function_name = get_function_name(log_group_name)
        try:
            log_client.put_subscription_filter(
                logGroupName=log_group_name,
                filterName=function_name + "-log-handler-lambda-subscription",
                filterPattern="",
                destinationArn=log_handler_arn,
            )
        except log_client.exceptions.LimitExceededException:
            # subscription filter already exists
            pass
        except log_client.exceptions.InvalidParameterException:
            # attempting to subscribe log_handler logs to log_handler
            pass
    return


def update_subscription_filters(log_client, log_group_names, log_handler_arn, aws_lambda_log_handler_arn):
    excluded_log_group_names = os.getenv("EXCLUDED_LOG_GROUPS", "").split(",")
    for log_group_name in log_group_names:
        if log_group_name in excluded_log_group_names:
            continue
        function_name = get_function_name(log_group_name)
        try:
            response = log_client.describe_subscription_filters(
                logGroupName=log_group_name,
                filterNamePrefix=f"{function_name}-log-handler-lambda-subscription",
                limit=5
            )

            if len(response["subscriptionFilters"]) == 2 and response["subscriptionFilters"][0]["destinationArn"] == response["subscriptionFilters"][0]["destinationArn"]:
                print("we got one!")

            for subscription_filter in response["subscriptionFilters"]:
                # print(f"Log Group Name: {subscription_filter['logGroupName']}, Subscription Filter Name: {subscription_filter['filterName']}")
                pprint.pprint(subscription_filter)

        except log_client.exceptions.LimitExceededException:
            # subscription filter already exists
            pass
        except log_client.exceptions.InvalidParameterException:
            # attempting to subscribe log_handler logs to log_handler
            pass
    return


def get_function_name(log_group_name):
    arr = log_group_name.split("/")
    if len(arr[-1]) == 0:
        return arr[-2]
    else:
        return arr[-1]


if __name__ == "__main__":
    event = []
    context = []
    lambda_handler(event, context)
