#!/usr/bin/env python
import boto3
import json

# TODO: Add exception handling for all IO


def lambda_handler(event, context):
    log_client = boto3.client('logs')
    lambda_client = boto3.client('lambda')
    log_handler_arn = get_log_handler_arn(lambda_client)
    log_groups = get_log_group_names(log_client)
    log_groups_with_subscription_filters = get_log_groups_with_subscription_filters(log_client)
    target_log_groups = log_groups_with_no_subscriptions(log_groups, log_groups_with_subscription_filters)
    create_subscription_filters(log_client, target_log_groups, log_handler_arn)


def get_log_group_names(log_client):
    response = log_client.describe_log_groups()
    # TODO: retry on token
    response_json = json.load(response)
    return set(map(lambda x: x['logGroupName'], response_json['logGroups']))


def get_log_groups_with_subscription_filters(log_client):
    response = log_client.describe_subscription_filters()
    # TODO: retry on token
    response_json = json.load(response)
    return set(map(lambda x: x['logGroupName'], response_json['subscriptionFilters']))


def log_groups_with_no_subscriptions(group_names, groups_with_subscriptions):
    return group_names - groups_with_subscriptions


def get_log_handler_arn(lambda_client):
    response = lambda_client.get_function(FunctionName='log_handler')
    response_json = json.load(response)
    return response_json['Configuration']['FunctionArn']


def create_subscription_filters(log_client, log_group_names, log_handler_arn):
    for log_group_name in log_group_names:
        function_name = get_function_name(log_group_name)
        log_client.put_subscription_filter(
            logGroupName=log_group_name,
            filterName=function_name + '-log-handler-lambda-subscription',
            filterPattern='',
            destinationArn=log_handler_arn
        )
    return


def get_function_name(log_group_name):
    arr = log_group_name.split('/')
    if len(arr[-1]) == 0:
        return arr[-2]
    else:
        return arr[-1]
