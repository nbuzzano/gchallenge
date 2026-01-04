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