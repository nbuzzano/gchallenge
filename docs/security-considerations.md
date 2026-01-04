

## Security Considerations

### 1. Secrets Management

Store sensitive data in AWS Secrets Manager:

```bash
# Store database password
aws secretsmanager create-secret \
  --name db-password \
  --secret-string '{"password":"<your-secure-password>"}'

# Store API keys
aws secretsmanager create-secret \
  --name api-keys \
  --secret-string '{"key1":"value1","key2":"value2"}'
```

### 2. Database Security

- **Encryption at rest**: Enable RDS encryption
- **Encryption in transit**: Use SSL/TLS for connections
- **IAM authentication**: Use RDS IAM database authentication
- **Network isolation**: Place RDS in private subnets
- **Backup encryption**: Enable automated encrypted backups

### 3. Container Security

- **Image scanning**: Enable ECR image scanning for vulnerabilities
- **Least privilege**: Run containers as non-root user
- **Resource limits**: Set CPU and memory limits
- **Network policies**: Restrict pod-to-pod communication

### 4. API Security

- **Rate limiting**: Implement request throttling
- **Input validation**: Validate all user inputs
- **CORS**: Configure Cross-Origin Resource Sharing properly
- **HTTPS/TLS**: Enable SSL/TLS termination at ALB
- **Authentication**: Add API key or OAuth2 authentication

### 5. Infrastructure Security

- **VPC**: Isolate resources in private subnets
- **Security groups**: Restrict network traffic
- **IAM policies**: Apply least privilege principle
- **Audit logging**: Enable CloudTrail for API calls
- **Backup strategy**: Regular automated backups with encryption

---

## Monitoring & Logging

### CloudWatch Dashboard

Create `infrastructure/monitoring/dashboard.json`:

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "AWS/ECS", "CPUUtilization", { "stat": "Average" } ],
          [ ".", "MemoryUtilization", { "stat": "Average" } ],
          [ "AWS/ApplicationELB", "TargetResponseTime", { "stat": "Average" } ],
          [ ".", "RequestCount", { "stat": "Sum" } ],
          [ ".", "HTTPCode_Target_5XX_Count", { "stat": "Sum" } ]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "API Performance Metrics"
      }
    },
    {
      "type": "log",
      "properties": {
        "query": "fields @timestamp, @message | stats count() by bin(5m)",
        "region": "us-east-1",
        "title": "Error Rate (5min bins)"
      }
    }
  ]
}
```

### CloudWatch Alarms

```bash
# High CPU utilization
aws cloudwatch put-metric-alarm \
  --alarm-name migration-api-high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:alerting-topic

# High error rate
aws cloudwatch put-metric-alarm \
  --alarm-name migration-api-high-errors \
  --alarm-description "Alert when 5XX errors exceed 10 per minute" \
  --metric-name HTTPCode_Target_5XX_Count \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 60 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:alerting-topic
```

---