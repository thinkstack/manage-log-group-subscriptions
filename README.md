# log-handler-subscription-lambda

This lambda checks for other lambdas without cloudwatch subscriptions and links them to the log-handler lambda

# Additional comments - TEL-3153

```
export EXCLUDED_LOG_GROUPS='/aws/ecs/containerinsights/protected-mdtp/performance,/aws/ecs/containerinsights/protected-rate-mdtp/performance,/aws/ecs/containerinsights/public-mdtp/performance,/aws/ecs/containerinsights/public-monolith-mdtp/performance,/aws/ecs/containerinsights/public-rate-mdtp/performance,/aws/fluentbit/docker-partial-logs,/aws/fluentbit/ingress-gateway-envoy-protected,/aws/fluentbit/ingress-gateway-envoy-protected-rate,/aws/fluentbit/ingress-gateway-envoy-public,/aws/fluentbit/ingress-gateway-envoy-public-monolith,/aws/fluentbit/ingress-gateway-envoy-public-rate,/aws/route53/resolver/deskpro_vpc,/aws/route53/resolver/hmrc_core_connectivity-v2_vpc,/aws/route53/resolver/hmrc_core_connectivity_vpc,/aws/route53/resolver/isc_vpc,/aws/route53/resolver/mdtp_vpc,/aws/route53/resolver/perftest_vpc,/aws/route53/resolver/psn_vpc,/vpc/platsec_central_flow_log,CloudTrail/DefaultLogGroup,deskpro-flow-logs,hmrc_core_connectivity-flow-logs,isc-flow-logs,mdtp-flow-logs,perftest-flow-logs,psn-flow-logs'

export DRY_RUN=true
```