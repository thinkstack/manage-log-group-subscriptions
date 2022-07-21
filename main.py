#!/usr/bin/env python
import os
import sys

import boto3
from aws_lambda_powertools import Logger
from botocore.config import Config
from distutils.util import strtobool
from progress.bar import Bar

function_to_execute = ""
excluded_log_group_names = os.getenv("EXCLUDED_LOG_GROUPS", "").split(",")
old_lambda_name = os.getenv("OLD_LAMBDA_NAME", "")
new_lambda_name = os.getenv("NEW_LAMBDA_NAME", "")

config = Config(retries=dict(max_attempts=10))
lambda_client = boto3.client("lambda", region_name="eu-west-2", config=config)
log_client = boto3.client("logs", region_name="eu-west-2", config=config)
logger = Logger(service="manage-log-group-subscriptions")


def get_function_name(log_group_name):
    arr = log_group_name.split("/")
    if len(arr[-1]) == 0:
        return arr[-2]
    else:
        return arr[-1]


def get_lambda_arn(function_name):
    response = lambda_client.get_function_configuration(FunctionName=function_name)
    return response["FunctionArn"]


def get_paginated_log_groups(next_token):
    if next_token:
        return log_client.describe_log_groups(nextToken=next_token)
    else:
        return log_client.describe_log_groups()


def get_log_group_names(previous_group_names, next_token):
    response = get_paginated_log_groups(next_token)
    group_names = previous_group_names + list(
        map(lambda x: x["logGroupName"], response["logGroups"])
    )
    if "nextToken" in response:
        return get_log_group_names(group_names, response["nextToken"])
    else:
        return group_names


def get_lambda_and_log_groups_details():
    log_handler_arn = get_lambda_arn(old_lambda_name)
    aws_lambda_log_handler_arn = get_lambda_arn(new_lambda_name)
    log_groups = get_log_group_names([], None)
    return log_handler_arn, aws_lambda_log_handler_arn, log_groups


def debug_subscription_filters():
    (
        log_handler_arn,
        aws_lambda_log_handler_arn,
        log_groups,
    ) = get_lambda_and_log_groups_details()
    logger.debug(f"Found {len(log_groups)} log groups")

    messages = []
    bar = Bar("Processing", max=len(log_groups))
    for log_group_name in log_groups:
        try:
            response = log_client.describe_subscription_filters(
                logGroupName=log_group_name,
                limit=5,
            )

            if len(response["subscriptionFilters"]) > 0:
                for subscription_filter in response["subscriptionFilters"]:
                    if subscription_filter["destinationArn"].endswith(
                        ":function:log_handler"
                    ):
                        logger.debug(
                            f"Log Group Name: {subscription_filter['logGroupName']}, Lambda: {subscription_filter['destinationArn']}"
                        )
                        messages.append(
                            f"Log Group Name: {subscription_filter['logGroupName']}, Lambda: {subscription_filter['destinationArn']}"
                        )
            bar.next()
        except log_client.exceptions.LimitExceededException:
            logger.warning("Limit exceeded exception, ignoring.")
            pass
        except log_client.exceptions.InvalidParameterException:
            logger.warning("Invalid parameter exception, ignoring.")
            pass

    bar.finish()
    print(messages)
    return


def delete_duplicate_filters():
    (
        log_handler_arn,
        aws_lambda_log_handler_arn,
        log_groups,
    ) = get_lambda_and_log_groups_details()
    logger.debug(f"Found {len(log_groups)} log groups")

    messages = []
    bar = Bar("Processing", max=len(log_groups))
    dry_run = strtobool(os.getenv("DRY_RUN", "true"))
    logger.info(f"Running DRY_RUN mode = {str(bool(dry_run))}")

    for log_group_name in log_groups:
        if log_group_name in excluded_log_group_names:
            continue
        function_name = get_function_name(log_group_name)
        subscription_filter_name = f"{function_name}-log-handler-lambda-subscription"
        try:
            response = log_client.describe_subscription_filters(
                logGroupName=log_group_name,
                limit=5,
            )

            filters = response["subscriptionFilters"]

            if (
                len(filters) == 2
                and filters[0]["destinationArn"] == filters[1]["destinationArn"]
            ):
                logger.debug(filters)
                if not dry_run:
                    messages.append(
                        f"Deleting the following filter: {subscription_filter_name} from {log_group_name}"
                    )
                    response = log_client.delete_subscription_filter(
                        logGroupName=log_group_name,
                        filterName=subscription_filter_name,
                    )
                    logger.debug(response)
                else:
                    messages.append(
                        f"We would be deleting the following filter: {subscription_filter_name} from {log_group_name}"
                    )
            bar.next()
        except log_client.exceptions.LimitExceededException:
            logger.warning("Limit exceeded exception, ignoring.")
            pass
        except log_client.exceptions.InvalidParameterException:
            logger.warning("Invalid parameter exception, ignoring.")
            pass

    bar.finish()
    print(messages)
    return


def get_formatted_subscription_filters():
    (
        log_handler_arn,
        aws_lambda_log_handler_arn,
        log_groups,
    ) = get_lambda_and_log_groups_details()

    logger.debug(f"Found {len(log_groups)} log groups")
    subscription_filter_map = {}

    bar = Bar("Processing", max=len(log_groups))
    for log_group_name in log_groups:
        if log_group_name in excluded_log_group_names:
            continue
        function_name = get_function_name(log_group_name)
        subscription_filter_name = f"{function_name}-log-handler-lambda-subscription"
        try:
            response = log_client.describe_subscription_filters(
                logGroupName=log_group_name,
                filterNamePrefix=subscription_filter_name,
                limit=5,
            )

            if len(response["subscriptionFilters"]) > 0:
                for subscription_filter in response["subscriptionFilters"]:
                    if subscription_filter["destinationArn"].endswith(
                        ":function:log_handler"
                    ):
                        subscription_filter_map[
                            log_group_name
                        ] = subscription_filter_name
            bar.next()
        except log_client.exceptions.LimitExceededException:
            logger.warning("Limit exceeded exception, ignoring.")
            pass
        except log_client.exceptions.InvalidParameterException:
            logger.warning("Invalid parameter exception, ignoring.")
            pass

    bar.finish()
    print(
        "\n".join('"{}"="{}"'.format(k, v) for k, v in subscription_filter_map.items())
    )
    return


if __name__ == "__main__":
    function_to_execute = sys.argv[1:][0]
    logger.debug(f"Requested function: {function_to_execute}")

    try:
        globals()[function_to_execute]()
    except KeyError as key_error:
        logger.error(f"The function {key_error} does not exist. Exiting...")
        exit(1)
