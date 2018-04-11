#!/usr/bin/env python
import json

#Add exception handling for all IO

def get_lambda_log_group_names(lambda_client):
    response = lambda_client.describe_log_groups()
    # retry on token
    response_json = json.load(response)
    return set(map(lambda x: x['logGroupName'], response_json['logGroups']))

def get_log_groups_with_subscription_filters(lambda_client):
    response = lambda_client.describe_subscription_filters()
    #retry on token
    response_json = json.load(response)
    return set(map(lambda x: x['logGroupName'], response_json['subscriptionFilters']))

def log_groups_with_no_subscriptions(group_names, groups_with_subscriptions):
    return group_names - groups_with_subscriptions