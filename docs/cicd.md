

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