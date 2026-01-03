# AWS Cloud Deployment Strategy

This document outlines the strategic approach for deploying the DB Migration REST API to AWS cloud infrastructure. It provides architectural recommendations, service selection criteria, and operational considerations without implementation-specific code.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [AWS Services Selection](#aws-services-selection)
3. [Infrastructure as Code Approach](#infrastructure-as-code-approach)
4. [GitOps & Automation Strategy](#gitops--automation-strategy)
5. [Security & Compliance](#security--compliance)
6. [Monitoring & Observability](#monitoring--observability)
7. [Disaster Recovery Planning](#disaster-recovery-planning)
8. [Cost Management](#cost-management)

---

## Architecture Overview

### Recommended Architecture: Containerized Microservices on AWS

The recommended approach for this REST API deployment follows a modern cloud-native architecture:

**Core Components:**
- **Compute Layer**: Containerized application running on managed container orchestration
- **Database Layer**: Managed relational database with automatic backups and high availability
- **Load Balancing**: Distribute traffic across multiple application instances
- **Storage Layer**: Secure object storage for CSV file uploads
- **Observability**: Centralized logging, metrics, and monitoring

**High-Level Flow:**
1. User uploads CSV file via REST API endpoint
2. API validates and processes the CSV data
3. Data is stored in managed SQL database
4. Application scales automatically based on demand
5. All operations logged and monitored centrally
6. Backups happen automatically with point-in-time recovery

**Multi-Availability Zone Design:**
- Deploy across 2+ availability zones for high availability
- Automatic failover if one AZ becomes unavailable
- Load balancer distributes traffic across zones
- Database with synchronous replication to standby

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Route 53 (DNS)                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│         Load Balancer (SSL/TLS Termination)                  │
│              Port 80/443 → 8000                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┴──────────────┐
         │                            │
    ┌────▼────────┐          ┌───────▼────────┐
    │   AZ-1      │          │    AZ-2        │
    │ ┌────────┐  │          │ ┌───────────┐  │
    │ │App Pod │  │          │ │ App Pod   │  │
    │ │Replica │  │          │ │ Replica   │  │
    │ └────────┘  │          │ └───────────┘  │
    └─────┬───────┘          └────────┬───────┘
          │                            │
          └─────────────┬──────────────┘
                        │
            ┌───────────▼──────────────┐
            │  Managed SQL Database    │
            │  (Primary + Standby)     │
            │  Multi-AZ Deployment     │
            └───────────┬──────────────┘
                        │
            ┌───────────▼──────────────┐
            │   Object Storage (S3)    │
            │   CSV File Uploads       │
            └──────────────────────────┘
```

---

## AWS Services Selection

### Compute & Application Hosting Options

**Option 1: Amazon ECS with Fargate (Recommended)**
- **Pros**: Serverless container management, no EC2 instance management, pay per container
- **Cons**: Slightly higher cost than EC2, not suitable for very long-running tasks
- **Best for**: Stateless APIs with variable load, our use case

**Option 2: Amazon EKS (Kubernetes)**
- **Pros**: Industry standard, highly portable, rich ecosystem
- **Cons**: More complex, higher operational overhead
- **Best for**: Large microservices architectures, multi-cloud strategies

**Option 3: EC2 with Auto Scaling**
- **Pros**: Cost-effective for baseline load, familiar approach
- **Cons**: More operational overhead, instance management required
- **Best for**: Predictable, consistent load

**Recommendation**: ECS Fargate offers the best balance of simplicity, cost, and scalability for this API.

### Database Options

**Option 1: Amazon RDS Aurora PostgreSQL (Recommended)**
- **Pros**: AWS-native, automatic failover, point-in-time recovery, 35-day backups
- **Cons**: Higher cost than self-managed, vendor lock-in
- **Best for**: Production APIs requiring reliability

**Option 2: RDS Standard PostgreSQL**
- **Pros**: Lower cost than Aurora
- **Cons**: Less redundancy, manual failover
- **Best for**: Non-critical environments

**Option 3: DynamoDB**
- **Pros**: Fully serverless, automatic scaling
- **Cons**: NoSQL (not suitable for relational data), different paradigm
- **Best for**: Different data models

**Recommendation**: RDS Aurora PostgreSQL Multi-AZ for production reliability and automatic backup/recovery.

### Load Balancing & DNS

**Application Load Balancer (ALB)**
- Layer 7 (Application) load balancing
- Understands HTTP/HTTPS
- Path-based and hostname-based routing
- Suitable for REST APIs

**Route 53**
- AWS managed DNS service
- Health checks and failover
- Global load balancing for disaster recovery

### Storage for CSV Files

**Amazon S3**
- Object storage for CSV uploads
- Versioning for audit trails
- Server-side encryption at rest
- Lifecycle policies to archive old files
- Integration with other AWS services

### Monitoring & Logging

**CloudWatch**
- Centralized logs from all containers
- Custom metrics and dashboards
- Alarms for operational alerts
- Log retention policies

**Optional: AWS X-Ray**
- Distributed tracing
- Performance analysis
- Dependency mapping

---

## Infrastructure as Code Approach

Rather than manually creating resources through AWS console, infrastructure should be defined as code. This enables:
- **Reproducibility**: Consistent deployments across environments
- **Version Control**: Track infrastructure changes in Git
- **Automation**: Automated creation and updates
- **Documentation**: Infrastructure is self-documenting
- **Disaster Recovery**: Quick redeployment if needed

### Tool Selection

**Option 1: AWS CloudFormation**
- AWS-native Infrastructure as Code
- JSON or YAML format
- Deep AWS service integration
- Learning curve for complex stacks

**Option 2: Terraform**
- Multi-cloud capable
- HCL language (more intuitive)
- Large community and modules
- Excellent for complex architectures

**Option 3: AWS CDK**
- Define infrastructure using Python/TypeScript
- Familiar programming paradigm
- Good for developers comfortable with code
- Compiles to CloudFormation

**Recommendation**: Terraform for multi-cloud flexibility, or CloudFormation for AWS-only simplicity.

### IaC Template Structure

Infrastructure code should define:
1. **VPC & Networking**: VPC, subnets, security groups, route tables
2. **Database**: RDS cluster, parameter groups, backup settings
3. **Application**: Container definitions, task definitions, service configuration
4. **Load Balancing**: ALB, target groups, listeners
5. **Monitoring**: CloudWatch log groups, alarms, dashboards
6. **Storage**: S3 buckets, versioning, encryption, lifecycle policies
7. **IAM**: Roles, policies, service principals

---

## GitOps & Automation Strategy

GitOps is a modern operational paradigm where:
- **Git is the single source of truth** for infrastructure and application state
- **Declarative**: Desired state is declared in files
- **Automated**: Tools automatically reconcile actual state with desired state
- **Observable**: Changes are traceable and auditable
- **Continuous**: Continuous reconciliation ensures drift correction

### GitOps Workflow for This Project

```
Developer commits code to Git
           ↓
Automated tests run (unit, integration)
           ↓
Code review & approval
           ↓
Merge to main branch
           ↓
Infrastructure deployment triggered
           ↓
Application container built & pushed
           ↓
ECS service updated with new image
           ↓
Health checks verify deployment
           ↓
Monitoring tracks application health
           ↓
If issues detected: automatic rollback
```

### CI/CD Pipeline Components

**Continuous Integration (CI):**
- Automated testing on every commit
- Code quality checks
- Security scanning
- Container image building and scanning

**Continuous Deployment (CD):**
- Automatic deployment of passing changes
- Infrastructure provisioning
- Database migrations
- Health verification

### Implementation Approach

Rather than manual deployments, the recommended approach:

1. **Test Pipeline**: Every push runs automated tests
   - Unit tests for business logic
   - Integration tests with test database
   - API endpoint tests
   - Security scanning for vulnerabilities

2. **Build Pipeline**: On approval, containerize application
   - Docker image creation
   - Image scanning for vulnerabilities
   - Push to container registry (ECR)

3. **Deploy Pipeline**: Automatically deploy to staging then production
   - Infrastructure validation
   - Secrets retrieval from secure storage
   - Service deployment and health checks
   - Smoke tests post-deployment

4. **Monitoring**: Continuous observation
   - Application metrics and logs
   - Alert on anomalies
   - Automatic incident response where possible

### Tools for Implementation

**GitHub Actions** (recommended for this project):
- Native GitHub integration
- Free for public repos
- Matrix builds for testing multiple scenarios
- Secrets management

**Alternative Tools**:
- Jenkins: Self-hosted, extensive plugins
- GitLab CI: Integrated with GitLab
- CircleCI: SaaS offering
- AWS CodePipeline: AWS-native service

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'DB Migration API - ECS + RDS deployment'

Parameters:
  Environment:
    Type: String
    Default: production
    AllowedValues: [development, staging, production]
  
  ContainerImage:
    Type: String
    Description: ECR image URI

Resources:
  # VPC Configuration
  MigrationVPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true

  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref MigrationVPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      MapPublicIpOnLaunch: true

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref MigrationVPC
      CidrBlock: 10.0.2.0/24
      AvailabilityZone: !Select [1, !GetAZs '']
      MapPublicIpOnLaunch: true

  PrivateSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref MigrationVPC
      CidrBlock: 10.0.10.0/24
      AvailabilityZone: !Select [0, !GetAZs '']

  PrivateSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref MigrationVPC
      CidrBlock: 10.0.11.0/24
      AvailabilityZone: !Select [1, !GetAZs '']

  # Internet Gateway
  InternetGateway:
    Type: AWS::EC2::InternetGateway

  AttachGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref MigrationVPC
      InternetGatewayId: !Ref InternetGateway

  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref MigrationVPC

  PublicRoute:
    Type: AWS::EC2::Route
    DependsOn: AttachGateway
    Properties:
      RouteTableId: !Ref PublicRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway

  PublicSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PublicSubnet1
      RouteTableId: !Ref PublicRouteTable

  PublicSubnet2RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PublicSubnet2
      RouteTableId: !Ref PublicRouteTable

  # Security Groups
  ALBSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: ALB Security Group
      VpcId: !Ref MigrationVPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0

  ECSSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: ECS Tasks Security Group
      VpcId: !Ref MigrationVPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 8000
          ToPort: 8000
          SourceSecurityGroupId: !Ref ALBSecurityGroup

  RDSSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: RDS Security Group
      VpcId: !Ref MigrationVPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 5432
          ToPort: 5432
          SourceSecurityGroupId: !Ref ECSSecurityGroup

  # RDS Aurora PostgreSQL
  DBSubnetGroup:
    Type: AWS::RDS::DBSubnetGroup
    Properties:
      DBSubnetGroupDescription: Subnet group for RDS
      SubnetIds:
        - !Ref PrivateSubnet1
        - !Ref PrivateSubnet2

  AuroraCluster:
    Type: AWS::RDS::DBCluster
    DeletionPolicy: Snapshot
    Properties:
      Engine: aurora-postgresql
      EngineVersion: '14.6'
      MasterUsername: postgres
      MasterUserPassword: !Sub '{{resolve:secretsmanager:db-password:SecretString:password}}'
      DBSubnetGroupName: !Ref DBSubnetGroup
      VpcSecurityGroupIds:
        - !Ref RDSSecurityGroup
      BackupRetentionPeriod: 35
      PreferredBackupWindow: '03:00-04:00'
      PreferredMaintenanceWindow: 'sun:04:00-sun:05:00'
      EnableIAMDatabaseAuthentication: true
      StorageEncrypted: true
      DeletionProtection: true

  AuroraInstance1:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: migration-db-1
      DBInstanceClass: db.t3.medium
      Engine: aurora-postgresql
      DBClusterIdentifier: !Ref AuroraCluster
      PubliclyAccessible: false

  AuroraInstance2:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: migration-db-2
      DBInstanceClass: db.t3.medium
      Engine: aurora-postgresql
      DBClusterIdentifier: !Ref AuroraCluster
      PubliclyAccessible: false

  # Application Load Balancer
  ApplicationLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: migration-api-alb
      Subnets:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2
      SecurityGroups:
        - !Ref ALBSecurityGroup
      Scheme: internet-facing

  TargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: migration-api-tg
      Port: 8000
      Protocol: HTTP
      VpcId: !Ref MigrationVPC
      TargetType: ip
      HealthCheckEnabled: true
      HealthCheckPath: /
      HealthCheckProtocol: HTTP
      HealthCheckIntervalSeconds: 30
      HealthCheckTimeoutSeconds: 5
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 3

  ALBListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref TargetGroup
      LoadBalancerArn: !Ref ApplicationLoadBalancer
      Port: 80
      Protocol: HTTP

  # ECS Cluster
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: migration-api-cluster
      ClusterSettings:
        - Name: containerInsights
          Value: enabled

  # CloudWatch Log Group
  LogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: /ecs/migration-api
      RetentionInDays: 30

  # IAM Role for ECS Task Execution
  ECSTaskExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: ecs-tasks.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
      Policies:
        - PolicyName: SecretsManagerAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - secretsmanager:GetSecretValue
                Resource: !Sub 'arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:db-*'

  # IAM Role for ECS Task (Application)
  ECSTaskRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: ecs-tasks.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: S3Access
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - s3:GetObject
                  - s3:PutObject
                Resource: !Sub '${CSVBucket.Arn}/*'
        - PolicyName: CloudWatchLogs
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - logs:CreateLogStream
                  - logs:PutLogEvents
                Resource: !GetAtt LogGroup.Arn

  # ECS Task Definition
  TaskDefinition:
    Type: AWS::ECS::TaskDefinition
    Properties:
      Family: migration-api
      NetworkMode: awsvpc
      RequiresCompatibilities:
        - FARGATE
      Cpu: '256'
      Memory: '512'
      ExecutionRoleArn: !GetAtt ECSTaskExecutionRole.Arn
      TaskRoleArn: !GetAtt ECSTaskRole.Arn
      ContainerDefinitions:
        - Name: migration-api
          Image: !Ref ContainerImage
          PortMappings:
            - ContainerPort: 8000
              Protocol: tcp
          Environment:
            - Name: DATABASE_URL
              Value: !Sub 'postgresql://postgres:${DBPassword}@${AuroraCluster.Endpoint.Address}:5432/migration'
            - Name: ENVIRONMENT
              Value: !Ref Environment
          LogConfiguration:
            LogDriver: awslogs
            Options:
              awslogs-group: !Ref LogGroup
              awslogs-region: !Ref AWS::Region
              awslogs-stream-prefix: ecs

  # ECS Service
  ECSService:
    Type: AWS::ECS::Service
    DependsOn: ALBListener
    Properties:
      ServiceName: migration-api-service
      Cluster: !Ref ECSCluster
      TaskDefinition: !Ref TaskDefinition
      DesiredCount: 2
      LaunchType: FARGATE
      NetworkConfiguration:
        AwsvpcConfiguration:
          Subnets:
            - !Ref PrivateSubnet1
            - !Ref PrivateSubnet2
          SecurityGroups:
            - !Ref ECSSecurityGroup
          AssignPublicIp: DISABLED
      LoadBalancers:
        - ContainerName: migration-api
          ContainerPort: 8000
          TargetGroupArn: !Ref TargetGroup
      DeploymentConfiguration:
        MaximumPercent: 200
        MinimumHealthyPercent: 100

  # Auto Scaling
  ServiceScalingTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    Properties:
      MaxCapacity: 10
      MinCapacity: 2
      ResourceId: !Sub 'service/${ECSCluster}/migration-api-service'
      RoleARN: !Sub 'arn:aws:iam::${AWS::AccountId}:role/aws-service-role/ecs.application-autoscaling.amazonaws.com/AWSServiceRoleForApplicationAutoScaling_ECSService'
      ScalableDimension: ecs:service:DesiredCount
      ServiceNamespace: ecs

  ServiceScalingPolicy:
    Type: AWS::ApplicationAutoScaling::ScalingPolicy
    Properties:
      PolicyName: cpu-scaling-policy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ServiceScalingTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 70.0
        PredefinedMetricSpecification:
          PredefinedMetricType: ECSServiceAverageCPUUtilization
        ScaleOutCooldown: 60
        ScaleInCooldown: 300

  # S3 Bucket for CSV files
  CSVBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub 'migration-api-csv-${AWS::AccountId}'
      VersioningConfiguration:
        Status: Enabled
      ServerSideEncryptionConfiguration:
        - ServerSideEncryptionByDefault:
            SSEAlgorithm: AES256
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true

Outputs:
  LoadBalancerDNS:
    Description: DNS name of the load balancer
    Value: !GetAtt ApplicationLoadBalancer.DNSName
    Export:
      Name: !Sub '${AWS::StackName}-LoadBalancerDNS'

  RDSEndpoint:
    Description: RDS Aurora endpoint
    Value: !GetAtt AuroraCluster.Endpoint.Address
    Export:
      Name: !Sub '${AWS::StackName}-RDSEndpoint'

  ECSClusterName:
    Description: ECS Cluster Name
    Value: !Ref ECSCluster
    Export:
      Name: !Sub '${AWS::StackName}-ECSCluster'
```

### Option 2: Terraform (Recommended for larger deployments)

Create `infrastructure/terraform/main.tf`:

```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "terraform-state-bucket"
    key            = "migration-api/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  default = "us-east-1"
}

variable "environment" {
  default = "production"
}

variable "app_name" {
  default = "migration-api"
}

variable "container_image" {
  description = "ECR image URI"
}

variable "container_port" {
  default = 8000
}

variable "desired_count" {
  default = 2
}

# VPC
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.app_name}-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = false
  enable_dns_hostnames = true
  enable_dns_support = true

  tags = {
    Environment = var.environment
    Application = var.app_name
  }
}

# RDS Aurora PostgreSQL
module "rds" {
  source = "terraform-aws-modules/rds-aurora/aws"
  version = "~> 8.0"

  name           = "${var.app_name}-db"
  engine         = "aurora-postgresql"
  engine_version = "14.6"
  family         = "aurora-postgresql14"
  major_engine_version = "14"

  database_name   = "migration"
  master_username = "postgres"
  master_password = random_password.db_password.result

  instances = {
    one = {
      instance_class = "db.t3.medium"
      publicly_accessible = false
    }
    two = {
      instance_class = "db.t3.medium"
      publicly_accessible = false
    }
  }

  vpc_id               = module.vpc.vpc_id
  db_subnet_group_name = module.vpc.database_subnet_group_name
  security_group_ingress_rules = {
    ecs = {
      from_port   = 5432
      to_port     = 5432
      ip_protocol = "tcp"
      security_groups = [aws_security_group.ecs_tasks.id]
    }
  }

  backup_retention_period      = 35
  preferred_backup_window      = "03:00-04:00"
  preferred_maintenance_window = "sun:04:00-sun:05:00"
  storage_encrypted            = true
  enabled_cloudwatch_logs_exports = ["postgresql"]

  tags = {
    Environment = var.environment
  }
}

# Random password for database
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Secrets Manager for DB password
resource "aws_secretsmanager_secret" "db_password" {
  name = "${var.app_name}-db-password"
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}

# Security Groups
resource "aws_security_group" "alb" {
  name   = "${var.app_name}-alb-sg"
  vpc_id = module.vpc.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ecs_tasks" {
  name   = "${var.app_name}-ecs-tasks-sg"
  vpc_id = module.vpc.vpc_id

  ingress {
    from_port       = var.container_port
    to_port         = var.container_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ALB
resource "aws_lb" "main" {
  name               = "${var.app_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets
}

resource "aws_lb_target_group" "app" {
  name        = "${var.app_name}-tg"
  port        = var.container_port
  protocol    = "HTTP"
  vpc_id      = module.vpc.vpc_id
  target_type = "ip"

  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/"
    matcher             = "200"
  }
}

resource "aws_lb_listener" "app" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${var.app_name}"
  retention_in_days = 30
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.app_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }
}

# IAM Roles
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.app_name}-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_task_execution_role_secrets" {
  name = "${var.app_name}-ecs-task-execution-secrets"
  role = aws_iam_role.ecs_task_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Effect = "Allow"
        Resource = [
          aws_secretsmanager_secret.db_password.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role" "ecs_task_role" {
  name = "${var.app_name}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# ECS Task Definition
resource "aws_ecs_task_definition" "app" {
  family                   = var.app_name
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = var.app_name
      image     = var.container_image
      cpu       = 256
      memory    = 512
      essential = true
      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "DATABASE_URL"
          value = "postgresql://postgres@${module.rds.cluster_endpoint}:5432/migration"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

# ECS Service
resource "aws_ecs_service" "app" {
  name            = "${var.app_name}-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = module.vpc.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = var.app_name
    container_port   = var.container_port
  }

  depends_on = [aws_lb_listener.app]

  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
  }
}

# Auto Scaling
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.app.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "ecs_policy_cpu" {
  name               = "${var.app_name}-cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

# S3 Bucket for CSV files
resource "aws_s3_bucket" "csv_storage" {
  bucket = "${var.app_name}-csv-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "csv_storage" {
  bucket = aws_s3_bucket.csv_storage.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "csv_storage" {
  bucket = aws_s3_bucket.csv_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "csv_storage" {
  bucket = aws_s3_bucket.csv_storage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# Outputs
output "alb_dns_name" {
  value = aws_lb.main.dns_name
}

output "rds_endpoint" {
  value = module.rds.cluster_endpoint
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}
```

---

## GitOps Pipeline Strategy

### GitOps Principles

1. **Git as single source of truth**: All infrastructure and deployment configs live in Git
2. **Declarative infrastructure**: Desired state defined in code (CloudFormation/Terraform)
3. **Automated sync**: Tools automatically reconcile Git state with cloud state
4. **Continuous delivery**: Changes merged to main are automatically deployed

### Recommended Tool: ArgoCD

ArgoCD monitors your Git repository and automatically deploys changes to AWS.

#### Setup ArgoCD in EKS (alternative to ECS)

```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Expose ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

#### ArgoCD Application Definition

Create `argocd/application.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: migration-api
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-username/gchallenge
    targetRevision: main
    path: infrastructure/kubernetes
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

---

## CI/CD with GitHub Actions

### Docker Build & Push Pipeline

Create `.github/workflows/docker-build.yml`:

```yaml
name: Docker Build & Push

on:
  push:
    branches:
      - main
    paths:
      - 'app/**'
      - 'Dockerfile'
      - 'requirements.txt'
      - '.github/workflows/docker-build.yml'

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: migration-api

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    
    permissions:
      id-token: write
      contents: read

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build, tag, and push image to Amazon ECR
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

      - name: Update ECS task definition
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          aws ecs update-service \
            --cluster migration-api-cluster \
            --service migration-api-service \
            --force-new-deployment \
            --region ${{ env.AWS_REGION }}
```

### Testing Pipeline

Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on:
  push:
    branches:
      - main
      - develop
  pull_request:
    branches:
      - main
      - develop

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_migration
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install --with dev

      - name: Run linting
        run: |
          poetry run flake8 app tests
          poetry run black --check app tests

      - name: Run tests
        run: |
          poetry run pytest --cov=app --cov-report=xml
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_migration

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

      - name: Security scan
        run: |
          poetry run bandit -r app/
```

### Infrastructure Deployment Pipeline

Create `.github/workflows/deploy-infra.yml`:

```yaml
name: Deploy Infrastructure

on:
  push:
    branches:
      - main
    paths:
      - 'infrastructure/**'
      - '.github/workflows/deploy-infra.yml'

env:
  AWS_REGION: us-east-1

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    permissions:
      id-token: write
      contents: read

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Validate CloudFormation template
        run: |
          aws cloudformation validate-template \
            --template-body file://infrastructure/cloudformation/api-stack.yaml

      - name: Deploy CloudFormation stack
        run: |
          aws cloudformation deploy \
            --template-file infrastructure/cloudformation/api-stack.yaml \
            --stack-name migration-api-production \
            --parameter-overrides \
              Environment=production \
              ContainerImage=${{ secrets.ECR_IMAGE_URI }} \
            --capabilities CAPABILITY_NAMED_IAM \
            --region ${{ env.AWS_REGION }}

      - name: Wait for stack to complete
        run: |
          aws cloudformation wait stack-create-complete \
            --stack-name migration-api-production \
            --region ${{ env.AWS_REGION }} || \
          aws cloudformation wait stack-update-complete \
            --stack-name migration-api-production \
            --region ${{ env.AWS_REGION }}

  health-check:
    needs: deploy
    runs-on: ubuntu-latest
    
    permissions:
      id-token: write
      contents: read

    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Get ALB DNS
        id: get-dns
        run: |
          DNS=$(aws cloudformation describe-stacks \
            --stack-name migration-api-production \
            --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' \
            --output text \
            --region ${{ env.AWS_REGION }})
          echo "dns=$DNS" >> $GITHUB_OUTPUT

      - name: Health check
        run: |
          for i in {1..30}; do
            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://${{ steps.get-dns.outputs.dns }})
            if [ $HTTP_CODE -eq 200 ]; then
              echo "✓ API is healthy"
              exit 0
            fi
            echo "Attempt $i: HTTP $HTTP_CODE, retrying..."
            sleep 10
          done
          echo "✗ API health check failed"
          exit 1
```

---

## Dockerfile

Create `Dockerfile`:

```dockerfile
# Multi-stage build
FROM python:3.11-slim as builder

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-dev --no-interaction --no-ansi

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY app/ ./app/

# Set environment variable
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

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

## Disaster Recovery

### Backup Strategy

1. **RDS Automated Backups**
   - 35-day retention period
   - Daily snapshots
   - Point-in-time recovery

2. **Application Code**
   - GitHub repository (single source of truth)
   - Tags for releases
   - Release notes for each version

3. **Configuration**
   - Infrastructure as Code in Git
   - Secrets in AWS Secrets Manager
   - Feature flags in parameter store

### Recovery Procedures

#### Database Recovery

```bash
# List available snapshots
aws rds describe-db-snapshots \
  --db-cluster-identifier migration-db

# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier migration-db-restored \
  --db-snapshot-identifier <snapshot-id>

# Promote to primary
aws rds promote-read-replica \
  --db-instance-identifier migration-db-restored
```

#### Application Recovery

```bash
# Rollback to previous image
aws ecs update-service \
  --cluster migration-api-cluster \
  --service migration-api-service \
  --force-new-deployment

# Or specify previous image
aws ecs update-service \
  --cluster migration-api-cluster \
  --service migration-api-service \
  --task-definition migration-api:PREVIOUS_REVISION
```

#### Full Infrastructure Recovery

```bash
# Destroy compromised stack
aws cloudformation delete-stack \
  --stack-name migration-api-production

# Redeploy from Git
git push  # Triggers GitHub Actions
# or manually
aws cloudformation deploy \
  --template-file infrastructure/cloudformation/api-stack.yaml \
  --stack-name migration-api-production-restored
```

---

## Cost Optimization

### Recommendations

1. **Reserved Instances**: Purchase RDS reservations for 1-3 year commitment
2. **Spot Instances**: Use Fargate Spot for non-critical workloads (70% savings)
3. **S3 Lifecycle**: Move old CSV files to Glacier after 90 days
4. **Data Transfer**: Minimize cross-region data transfer
5. **Monitoring**: Use AWS Trusted Advisor for optimization recommendations

### Estimated Monthly Costs (US East 1)

| Service | Config | Estimated Cost |
|---------|--------|-----------------|
| ECS Fargate | 2-4 tasks, 256 CPU, 512 MB | $30-60 |
| RDS Aurora | db.t3.medium, Multi-AZ | $150-200 |
| ALB | 1 LB, 10GB data transfer | $20-30 |
| CloudWatch | Logs + metrics | $10-20 |
| S3 | 100GB storage | $2-5 |
| **Total** | | **$212-315/month** |

---

## Deployment Checklist

- [ ] AWS account setup with proper IAM roles
- [ ] GitHub personal access token created
- [ ] Docker image builds successfully
- [ ] CloudFormation/Terraform templates validated
- [ ] GitHub Actions secrets configured
- [ ] RDS database password stored in Secrets Manager
- [ ] S3 bucket for CSV files created
- [ ] CloudWatch log group created
- [ ] SNS topic for alerts created
- [ ] SSL certificate requested (ACM)
- [ ] Domain name configured (Route 53)
- [ ] Backup strategy tested and documented
- [ ] Monitoring dashboards created
- [ ] On-call rotation established
- [ ] Disaster recovery procedures documented and tested

---

## References

- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/welcome.html)
- [RDS Aurora Documentation](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Aurora.html)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [GitHub Actions AWS Integration](https://github.com/aws-actions)
- [Infrastructure as Code Best Practices](https://docs.aws.amazon.com/whitepapers/latest/introduction-devops-aws/)
