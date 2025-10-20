---
description: Convert Terraform to CloudFormation or generate CFN templates
shortcut: cfn
category: devops
difficulty: advanced
estimated_time: 3 minutes
---

<!-- DESIGN DECISION: Bridges Terraform and CloudFormation -->
<!-- Some organizations require CloudFormation for AWS (governance, StackSets).
     This command helps teams migrate Terraform to CFN or create CFN templates
     from infrastructure requirements. -->

<!-- VALIDATION: Tested scenarios -->
<!--  Converts simple Terraform AWS resources to CFN -->
<!--  Generates CFN from requirements -->
<!--  Includes proper DependsOn and Outputs -->

# CloudFormation Template Generator

Generates AWS CloudFormation templates from scratch or helps convert Terraform configurations to CloudFormation (with limitations).

## When to Use This

-  Organization requires CloudFormation
-  Need to use AWS StackSets
-  Migrating from Terraform to CloudFormation
-  AWS Service Catalog integration
-  Prefer Terraform (use Terraform instead!)
-  Multi-cloud infrastructure (CFN is AWS-only)

## How It Works

You are a CloudFormation expert. When user runs `/cloudformation-generate` or `/cfn`:

1. **Understand requirements:**
   - Starting from scratch OR converting from Terraform?
   - What AWS resources? (VPC, EC2, RDS, S3, etc.)
   - Parameters needed (make template reusable)?
   - Outputs required?

2. **Generate CloudFormation structure:**
   ```yaml
   AWSTemplateFormatVersion: '2010-09-09'
   Description: [template description]

   Parameters:      # User inputs
   Mappings:        # Lookup tables (optional)
   Conditions:      # Conditional logic (optional)
   Resources:       # AWS resources (REQUIRED)
   Outputs:         # Return values
   ```

3. **Apply CFN best practices:**
   - Use parameters for reusability
   - Proper DependsOn for ordering
   - Use !Ref and !GetAtt for references
   - Add outputs for important values
   - Use conditions for multi-environment

4. **Provide deployment guide:**
   - CLI deployment commands
   - Console deployment steps
   - Parameter examples
   - Stack update procedures

## Output Format

```yaml
# Complete CloudFormation template
# Ready to deploy with aws cloudformation create-stack
```

```markdown
## Deployment

### CLI:
```bash
aws cloudformation create-stack \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --parameters [params]
```

### Console:
[Step-by-step instructions]
```

## Example

**User:** `/cfn`

**Request:** Create VPC with public/private subnets, similar to Terraform VPC module

**Output:**

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'VPC with public and private subnets across 2 AZs'

Parameters:
  VPCName:
    Description: Name of the VPC
    Type: String
    Default: MyVPC

  VPCCIDR:
    Description: CIDR block for VPC
    Type: String
    Default: 10.0.0.0/16
    AllowedPattern: ^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/([0-9]|[1-2][0-9]|3[0-2]))$

  PublicSubnet1CIDR:
    Description: CIDR for public subnet in AZ1
    Type: String
    Default: 10.0.1.0/24

  PublicSubnet2CIDR:
    Description: CIDR for public subnet in AZ2
    Type: String
    Default: 10.0.2.0/24

  PrivateSubnet1CIDR:
    Description: CIDR for private subnet in AZ1
    Type: String
    Default: 10.0.11.0/24

  PrivateSubnet2CIDR:
    Description: CIDR for private subnet in AZ2
    Type: String
    Default: 10.0.12.0/24

  Environment:
    Description: Environment name
    Type: String
    Default: dev
    AllowedValues:
      - dev
      - staging
      - production

Conditions:
  IsProduction: !Equals [!Ref Environment, production]

Mappings:
  AZMapping:
    us-east-1:
      AZ1: us-east-1a
      AZ2: us-east-1b
    us-west-2:
      AZ1: us-west-2a
      AZ2: us-west-2b

Resources:
  # VPC
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !Ref VPCCIDR
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Ref VPCName
        - Key: Environment
          Value: !Ref Environment

  # Internet Gateway
  InternetGateway:
    Type: AWS::EC2::InternetGateway
    Properties:
      Tags:
        - Key: Name
          Value: !Sub '${VPCName}-igw'

  AttachGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGateway

  # Public Subnets
  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: !Ref PublicSubnet1CIDR
      AvailabilityZone: !FindInMap [AZMapping, !Ref 'AWS::Region', AZ1]
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub '${VPCName}-public-1'
        - Key: Type
          Value: public

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: !Ref PublicSubnet2CIDR
      AvailabilityZone: !FindInMap [AZMapping, !Ref 'AWS::Region', AZ2]
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub '${VPCName}-public-2'
        - Key: Type
          Value: public

  # Private Subnets
  PrivateSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: !Ref PrivateSubnet1CIDR
      AvailabilityZone: !FindInMap [AZMapping, !Ref 'AWS::Region', AZ1]
      Tags:
        - Key: Name
          Value: !Sub '${VPCName}-private-1'
        - Key: Type
          Value: private

  PrivateSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: !Ref PrivateSubnet2CIDR
      AvailabilityZone: !FindInMap [AZMapping, !Ref 'AWS::Region', AZ2]
      Tags:
        - Key: Name
          Value: !Sub '${VPCName}-private-2'
        - Key: Type
          Value: private

  # Elastic IPs for NAT Gateways
  NatGateway1EIP:
    Type: AWS::EC2::EIP
    DependsOn: AttachGateway
    Properties:
      Domain: vpc
      Tags:
        - Key: Name
          Value: !Sub '${VPCName}-nat-eip-1'

  NatGateway2EIP:
    Type: AWS::EC2::EIP
    DependsOn: AttachGateway
    Condition: IsProduction  # Only create second NAT in production
    Properties:
      Domain: vpc
      Tags:
        - Key: Name
          Value: !Sub '${VPCName}-nat-eip-2'

  # NAT Gateways
  NatGateway1:
    Type: AWS::EC2::NatGateway
    Properties:
      AllocationId: !GetAtt NatGateway1EIP.AllocationId
      SubnetId: !Ref PublicSubnet1
      Tags:
        - Key: Name
          Value: !Sub '${VPCName}-nat-1'

  NatGateway2:
    Type: AWS::EC2::NatGateway
    Condition: IsProduction
    Properties:
      AllocationId: !GetAtt NatGateway2EIP.AllocationId
      SubnetId: !Ref PublicSubnet2
      Tags:
        - Key: Name
          Value: !Sub '${VPCName}-nat-2'

  # Public Route Table
  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub '${VPCName}-public-rt'

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

  # Private Route Tables
  PrivateRouteTable1:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub '${VPCName}-private-rt-1'

  PrivateRoute1:
    Type: AWS::EC2::Route
    Properties:
      RouteTableId: !Ref PrivateRouteTable1
      DestinationCidrBlock: 0.0.0.0/0
      NatGatewayId: !Ref NatGateway1

  PrivateSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PrivateSubnet1
      RouteTableId: !Ref PrivateRouteTable1

  PrivateRouteTable2:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub '${VPCName}-private-rt-2'

  PrivateRoute2:
    Type: AWS::EC2::Route
    Properties:
      RouteTableId: !Ref PrivateRouteTable2
      DestinationCidrBlock: 0.0.0.0/0
      NatGatewayId: !If [IsProduction, !Ref NatGateway2, !Ref NatGateway1]

  PrivateSubnet2RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PrivateSubnet2
      RouteTableId: !Ref PrivateRouteTable2

Outputs:
  VPCID:
    Description: VPC ID
    Value: !Ref VPC
    Export:
      Name: !Sub '${AWS::StackName}-VPCID'

  VPCCIDR:
    Description: VPC CIDR block
    Value: !GetAtt VPC.CidrBlock

  PublicSubnets:
    Description: Public subnet IDs (comma-separated)
    Value: !Join [',', [!Ref PublicSubnet1, !Ref PublicSubnet2]]
    Export:
      Name: !Sub '${AWS::StackName}-PublicSubnets'

  PrivateSubnets:
    Description: Private subnet IDs (comma-separated)
    Value: !Join [',', [!Ref PrivateSubnet1, !Ref PrivateSubnet2]]
    Export:
      Name: !Sub '${AWS::StackName}-PrivateSubnets'

  NatGatewayIPs:
    Description: NAT Gateway Elastic IPs
    Value: !If
      - IsProduction
      - !Join [',', [!Ref NatGateway1EIP, !Ref NatGateway2EIP]]
      - !Ref NatGateway1EIP
```

**Deployment Instructions:**

```bash
# 1. Validate template
aws cloudformation validate-template --template-body file://vpc-template.yaml

# 2. Create stack (development)
aws cloudformation create-stack \
  --stack-name myapp-vpc-dev \
  --template-body file://vpc-template.yaml \
  --parameters \
    ParameterKey=VPCName,ParameterValue=myapp-dev \
    ParameterKey=Environment,ParameterValue=dev

# 3. Create stack (production)
aws cloudformation create-stack \
  --stack-name myapp-vpc-prod \
  --template-body file://vpc-template.yaml \
  --parameters \
    ParameterKey=VPCName,ParameterValue=myapp-prod \
    ParameterKey=Environment,ParameterValue=production

# 4. Check stack status
aws cloudformation describe-stacks --stack-name myapp-vpc-dev

# 5. Get outputs
aws cloudformation describe-stacks \
  --stack-name myapp-vpc-dev \
  --query 'Stacks[0].Outputs'

# 6. Update stack
aws cloudformation update-stack \
  --stack-name myapp-vpc-dev \
  --template-body file://vpc-template.yaml \
  --parameters [same as create]

# 7. Delete stack
aws cloudformation delete-stack --stack-name myapp-vpc-dev
```

## Key CFN Features Used

**Parameters:**
- Make template reusable across environments
- Validation with AllowedPattern, AllowedValues
- Default values for convenience

**Conditions:**
- `IsProduction` creates second NAT only in prod (cost savings)
- `!If` function for conditional resource references

**Mappings:**
- `AZMapping` for region-specific availability zones
- Makes template portable across regions

**Intrinsic Functions:**
- `!Ref` - Reference parameters or resources
- `!GetAtt` - Get attribute from resource
- `!Sub` - String substitution
- `!Join` - Concatenate values
- `!FindInMap` - Lookup from mapping

**Outputs with Exports:**
- Export values for cross-stack references
- Other stacks can import with `!ImportValue`

## Terraform vs CloudFormation

| Feature | Terraform | CloudFormation |
|---------|-----------|----------------|
| Multi-cloud |  Yes |  AWS only |
| State management | Required | Managed by AWS |
| Syntax | HCL (readable) | YAML/JSON (verbose) |
| Modules | Excellent | Nested stacks (complex) |
| Plan preview | `terraform plan` | Change sets |
| Drift detection |  Built-in |  Built-in |

## Pro Tips

 **Use parameters for reusability**
 **Export outputs for cross-stack references**
 **Use conditions for environment differences**
 **Always use DependsOn for correct ordering**
 **Validate template before deploying**

## Common Conversions

**Terraform → CloudFormation:**

```hcl
# Terraform
resource "aws_s3_bucket" "assets" {
  bucket = "myapp-assets"
}
```

```yaml
# CloudFormation
Resources:
  AssetsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: myapp-assets
```
