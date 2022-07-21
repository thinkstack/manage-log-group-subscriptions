# Manage Log Group Subscriptions

This repository is intended to help teams migrate CloudWatch Log Group subscription filters from one Lambda to
another. Please consume this repo with care as it's only intended as a set of helper scripts. The code may need to be
tweaked based on user requirements.

## Pre-requisites

* Python 3.9+
* Poetry 1.1.13+
* AWS Credentials


## Setup

### Environment Variables
Here's an example of my `.envrc` file, it is a good starter

```shell
export EXCLUDED_LOG_GROUPS=""
export LOG_LEVEL=DEBUG
export NEW_LAMBDA_NAME="aws-lambda-log-handler"
export OLD_LAMBDA_NAME="log_handler"
export POETRY_VIRTUALENVS_IN_PROJECT=true
export PYTHONPATH=/path/to/source/manage-log-group-subscriptions
```

##  Usage

### Install dependencies

```shell
# Install dependencies
make setup

# Show the help text
make
```

### Debug Log Groups

This will iterate through the CloudWatch Log Groups in the current AWS environment and output those that have a
subscription filter set to the Lambda function defined in `OLD_LAMBDA_NAME`. After migration to the new Lambda is
complete, this should return an empty list.

```shell
make debug_log_groups
```

### Tidy Log Group Subscription Filters

Use these commands to list and then delete and CloudWatch Log Groups that have multiple filters pointing to the same
Lambda. It uses internal filters that may need to be tweaked depending upon how your filters are set up.

```shell
make display_duplicate_filters
make delete_duplicate_filters
```

### Get Terraform Map

Use this command to output a list of dictionary entries that consist of CloudWatch Log Group name and its equivalent
subscription filter name. The output can be copied into the value of a Terraform map(string) variable and used to create
instances of `aws_cloudwatch_log_subscription_filter` resource.

```shell
make get_formatted_filters
```
