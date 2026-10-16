terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.95"
    }
  }

  # local state is fine for a single-person project. For a team, move it to S3:
  # backend "s3" {
  #   bucket = "careslot-tfstate-<account-id>"
  #   key    = "eks/terraform.tfstate"
  #   region = "ap-south-1"
  # }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project   = "careslot"
      ManagedBy = "terraform"
      Owner     = var.owner
    }
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}
