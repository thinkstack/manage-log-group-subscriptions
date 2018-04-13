#!/usr/bin/env python
import boto3
import json

# TODO: Add exception handling for all IO


def lambda_handler(event, context):
    log_client = boto3.client('logs', region_name='eu-west-2')
    lambda_client = boto3.client('lambda', region_name='eu-west-2')
    log_handler_arn = get_log_handler_arn(lambda_client)
    log_groups = get_log_group_names(log_client)
    create_subscription_filters(log_client, log_groups, log_handler_arn)


def get_log_group_names(log_client):
    response = log_client.describe_log_groups()
    # TODO: retry on token
    return set(map(lambda x: x['logGroupName'], response['logGroups']))


def get_log_handler_arn(lambda_client):
    response = lambda_client.get_function_configuration(FunctionName='log_handler')
    return response['FunctionArn']


def create_subscription_filters(log_client, log_group_names, log_handler_arn):
    for log_group_name in log_group_names:
        function_name = get_function_name(log_group_name)
        try:
            log_client.put_subscription_filter(
                logGroupName=log_group_name,
                filterName=function_name + '-log-handler-lambda-subscription',
                filterPattern='',
                destinationArn=log_handler_arn
            )
        except log_client.exceptions.LimitExceededException:
            # subscription filter already exists
            pass
        except log_client.exceptions.InvalidParameterException:
            # attempting to subscribe log_handler logs to log_handler
            pass
    return


def get_function_name(log_group_name):
    arr = log_group_name.split('/')
    if len(arr[-1]) == 0:
        return arr[-2]
    else:
        return arr[-1]
