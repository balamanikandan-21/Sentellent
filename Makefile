.PHONY: dev dev-up dev-down dev-logs build migrate seed

# --- Local Development ---

dev-up:
	docker compose up -d postgres redis
	@echo "Waiting for services..."
	@sleep 3
	@echo "PostgreSQL: localhost:5432 | Redis: localhost:6379"

dev-down:
	docker compose down

dev-logs:
	docker compose logs -f

dev:
	docker compose up --build

# --- Build ---

build:
	docker compose build

build-backend:
	docker build -t sentellent-backend ./backend

build-frontend:
	docker build -t sentellent-frontend ./frontend

# --- Database ---

migrate:
	cd backend && alembic upgrade head

migrate-create:
	cd backend && alembic revision --autogenerate -m "$(msg)"

# --- Infrastructure ---

tf-init:
	cd infra && terraform init

tf-plan:
	cd infra && terraform plan -out=tfplan

tf-apply:
	cd infra && terraform apply tfplan

tf-destroy:
	cd infra && terraform destroy

tf-bootstrap:
	cd infra/bootstrap && terraform init && terraform apply

# --- Deployment ---

deploy-backend:
	@echo "Building and pushing backend to ECR..."
	aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin $(shell aws sts get-caller-identity --query Account --output text).dkr.ecr.ap-south-1.amazonaws.com
	docker build -t sentellent-backend ./backend
	docker tag sentellent-backend:latest $(shell aws sts get-caller-identity --query Account --output text).dkr.ecr.ap-south-1.amazonaws.com/sentellent-production-backend:latest
	docker push $(shell aws sts get-caller-identity --query Account --output text).dkr.ecr.ap-south-1.amazonaws.com/sentellent-production-backend:latest
	aws ecs update-service --cluster sentellent-production-cluster --service sentellent-production-backend --force-new-deployment

deploy-frontend:
	@echo "Building and pushing frontend to ECR..."
	aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin $(shell aws sts get-caller-identity --query Account --output text).dkr.ecr.ap-south-1.amazonaws.com
	docker build -t sentellent-frontend ./frontend
	docker tag sentellent-frontend:latest $(shell aws sts get-caller-identity --query Account --output text).dkr.ecr.ap-south-1.amazonaws.com/sentellent-production-frontend:latest
	docker push $(shell aws sts get-caller-identity --query Account --output text).dkr.ecr.ap-south-1.amazonaws.com/sentellent-production-frontend:latest
	aws ecs update-service --cluster sentellent-production-cluster --service sentellent-production-frontend --force-new-deployment
