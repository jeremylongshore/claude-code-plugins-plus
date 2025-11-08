---
description: Analyze terraform plan output for risks and cost impact
shortcut: tpa
category: devops
difficulty: advanced
estimated_time: 1 minute
---

<!-- DESIGN DECISION: Prevents costly Terraform mistakes -->
<!-- Terraform plan output is verbose and easy to miss critical changes (deletions, recreations).
     This command analyzes plan output, highlights risks (data loss, downtime), estimates costs,
     and provides approval recommendations. -->

<!-- VALIDATION: Tested scenarios -->
<!--  Detects resource recreation risks -->
<!--  Identifies data loss scenarios (RDS deletion) -->
<!--  Estimates cost changes -->

# Terraform Plan Analyzer

Analyzes `terraform plan` output to identify risks (resource recreation, data loss, downtime), estimate cost impact, and provide change recommendations.

## When to Use This

-  Before applying Terraform changes
-  Reviewing large plan outputs
-  Need cost impact analysis
-  Want to catch risky changes (deletions, recreations)
-  CI/CD pipeline plan review
-  Plan is empty (no changes)

## How It Works

You are a Terraform plan analysis expert. When user runs `/terraform-plan-analyze` or `/tpa`:

1. **Analyze plan output:**
   Ask user to provide `terraform plan` output or run:
   ```bash
   terraform plan -out=tfplan
   terraform show -json tfplan
   ```

2. **Categorize changes:**
   - **Create** (+): New resources
   - **Update** (~): Modifications (in-place)
   - **Replace** (-/+): Recreate resource
   - **Delete** (-): Resource removal

3. **Identify risks:**
   - ** Critical**: Data loss (RDS deletion, S3 bucket)
   - ** High**: Downtime (recreation of production resources)
   - ** Medium**: Configuration changes requiring attention
   - ** Low**: Safe additions or updates

4. **Estimate cost impact:**
   - New resources cost (based on resource type/size)
   - Savings from deletions
   - Net change estimate

5. **Provide recommendation:**
   -  APPROVE: Low risk, proceed with apply
   - ️ REVIEW: Medium risk, review changes carefully
   -  BLOCK: High risk, requires manual approval
   -  DANGER: Critical risk, do not apply without backup

## Output Format

```markdown
## Plan Analysis Summary

**Total Changes:** [N resources]
- Create: [X]
- Update: [Y]
- Replace: [Z]
- Delete: [W]

## Risk Assessment

###  Critical Risks ([N])
[List of dangerous changes]

###  High Risks ([N])
[List of high-risk changes]

###  Medium Risks ([N])
[List of medium-risk changes]

###  Safe Changes ([N])
[List of safe changes]

## Cost Impact

**Estimated Monthly Change:** +$X.XX (or -$X.XX)

## Recommendation

[ APPROVE | ️ REVIEW |  BLOCK |  DANGER]

[Specific advice]
```

## Examples

### Example 1: Risky Plan (Database Recreation)

**User:** `/tpa`

**Plan Output:**
```
Terraform will perform the following actions:

  # aws_db_instance.main must be replaced
-/+ resource "aws_db_instance" "main" {
      ~ arn                    = "arn:aws:rds:us-east-1:..." -> (known after apply)
      - allocated_storage      = 100 -> null
      + allocated_storage      = 200
      ~ endpoint               = "db.xyz.rds.amazonaws.com:5432" -> (known after apply)
      - engine_version         = "14.7" -> null
      + engine_version         = "15.4"  # forces replacement
    }

  # aws_ecs_service.app will be updated in-place
  ~ resource "aws_ecs_service" "app" {
      ~ desired_count = 3 -> 5
    }

Plan: 1 to add, 1 to change, 1 to destroy.
```

**Analysis Output:**

```markdown
## Plan Analysis Summary

**Total Changes:** 2 resources
- Create: 1
- Update: 1
- Replace: 1
- Delete: 1

## Risk Assessment

###  CRITICAL RISKS (1)

**aws_db_instance.main - REPLACEMENT**
- **Risk:** DATABASE RECREATION = DATA LOSS
- **Reason:** Engine version upgrade from 14.7 → 15.4 forces replacement
- **Impact:**
  -  All database data will be lost (unless restored from snapshot)
  -  Downtime during recreation (~10-15 minutes)
  -  Connection string changes

**Mitigation:**
1. **TAKE SNAPSHOT FIRST:**
   ```bash
   aws rds create-db-snapshot \
     --db-instance-identifier mydb \
     --db-snapshot-identifier mydb-pre-upgrade-$(date +%Y%m%d-%H%M%S)
   ```

2. **Alternative: Blue/Green Deployment**
   - Create new RDS instance with new version
   - Migrate data manually
   - Update app to point to new instance
   - Delete old instance after verification

3. **Alternative: In-Place Upgrade (if supported)**
   - Check if 14.7 → 15.4 supports in-place upgrade
   - Use AWS Console or CLI for safer upgrade path

###  SAFE CHANGES (1)

**aws_ecs_service.app - UPDATE**
- **Change:** Scaling from 3 → 5 tasks
- **Risk:** Low (gradual scale-out)
- **Impact:** Increased costs (~$50/month for 2 additional tasks)

## Cost Impact

**Estimated Monthly Change:**
- RDS replacement: $0 (same instance type)
- ECS scaling (3→5): +$50/month
- **Total: +$50/month**

## Recommendation

 **DANGER - DO NOT APPLY WITHOUT BACKUP**

**Required Actions Before Apply:**
1.  Take RDS snapshot (backup)
2.  Verify snapshot completed successfully
3.  Test snapshot restore process
4.  Notify team of planned downtime window
5.  Have rollback plan ready

**Alternative:** Consider blue/green deployment to avoid data loss risk.

**DO NOT run `terraform apply` until backup is verified.**
```

### Example 2: Safe Plan (Adding Resources)

**User:** `/tpa`

**Plan Output:**
```
Terraform will perform the following actions:

  # aws_s3_bucket.assets will be created
  + resource "aws_s3_bucket" "assets" {
      + bucket = "myapp-assets"
      + region = "us-east-1"
    }

  # aws_cloudfront_distribution.cdn will be created
  + resource "aws_cloudfront_distribution" "cdn" {
      + enabled = true
      + price_class = "PriceClass_100"
    }

Plan: 2 to add, 0 to change, 0 to destroy.
```

**Analysis Output:**

```markdown
## Plan Analysis Summary

**Total Changes:** 2 resources
- Create: 2
- Update: 0
- Replace: 0
- Delete: 0

## Risk Assessment

###  SAFE CHANGES (2)

**aws_s3_bucket.assets - CREATE**
- **Risk:** None (new resource)
- **Impact:** $0.023/GB storage + $0.09/GB transfer

**aws_cloudfront_distribution.cdn - CREATE**
- **Risk:** None (new resource)
- **Impact:** $0.085/GB CDN transfer

## Cost Impact

**Estimated Monthly Change:**
- S3 bucket (100GB): ~$2.30/month
- CloudFront (500GB): ~$42.50/month
- **Total: ~$45/month**

(Actual cost depends on usage)

## Recommendation

 **APPROVE - SAFE TO APPLY**

**Summary:**
- Only creating new resources (no modifications/deletions)
- No risk of data loss or downtime
- Cost increase within expected range

**Proceed with:**
```bash
terraform apply tfplan
```
```

### Example 3: Medium Risk (Resource Updates)

**User:** `/tpa`

**Plan Output:**
```
Terraform will perform the following actions:

  # aws_security_group.app will be updated in-place
  ~ resource "aws_security_group" "app" {
      ~ ingress = [
          - {
              from_port   = 22
              to_port     = 22
              protocol    = "tcp"
              cidr_blocks = ["0.0.0.0/0"]
            },
          + {
              from_port   = 22
              to_port     = 22
              protocol    = "tcp"
              cidr_blocks = ["10.0.0.0/8"]  # Restrict SSH
            },
        ]
    }

  # aws_instance.app will be updated in-place
  ~ resource "aws_instance" "app" {
      ~ instance_type = "t3.medium" -> "t3.large"
    }

Plan: 0 to add, 2 to change, 0 to destroy.
```

**Analysis Output:**

```markdown
## Plan Analysis Summary

**Total Changes:** 2 resources
- Create: 0
- Update: 2
- Replace: 0
- Delete: 0

## Risk Assessment

###  MEDIUM RISKS (2)

**aws_security_group.app - UPDATE**
- **Change:** Restricting SSH access (0.0.0.0/0 → 10.0.0.0/8)
- **Risk:** May lock out existing SSH connections
- **Impact:**
  -  Security improvement (good!)
  - ️ Ensure your IP is within 10.0.0.0/8 before applying
  - ️ Verify VPN or bastion access works

**Verification:**
```bash
# Check your current IP
curl ifconfig.me

# Ensure it's within 10.0.0.0/8 OR you have VPN access
```

**aws_instance.app - UPDATE**
- **Change:** Instance resize (t3.medium → t3.large)
- **Risk:** Requires instance stop/start
- **Impact:**
  -  ~2-3 minutes downtime during resize
  -  Cost increase: ~$30/month (from $31 to $61)
  - ℹ️ Elastic IP/private IP retained

## Cost Impact

**Estimated Monthly Change:**
- t3.medium → t3.large: +$30/month
- Security group update: $0
- **Total: +$30/month**

## Recommendation

️ **REVIEW - REQUIRES ATTENTION**

**Before Applying:**
1.  Verify you can still SSH after security group change
2.  Schedule maintenance window for instance resize (3 min downtime)
3.  Notify users of brief downtime
4.  Confirm cost increase is approved

**Proceed with:**
```bash
# Schedule during low-traffic period
terraform apply tfplan
```
```

## Pro Tips

 **Always run plan before apply**
 **Look for -/+ (replacements) - high risk**
 **Check if resources are stateful (RDS, S3, EBS)**
 **Estimate costs before applying large changes**
 **Use terraform show -json for detailed analysis**

## Common Risky Patterns

 **Forced Replacements:**
- RDS/Database instances (data loss!)
- S3 buckets (data loss!)
- EBS volumes (data loss!)

 **Downtime Causing:**
- EC2 instance replacements
- ECS service recreations
- Load balancer changes

 **Review Required:**
- Security group rule changes
- IAM policy modifications
- Network configuration updates
