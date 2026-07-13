# Error Handling Reference

**Terraform State Lock**

- Error: "Error acquiring the state lock"
- Solution: Use `terraform force-unlock <lock-id>` or wait for lock expiry

**API Not Enabled**

- Error: "Vertex AI API has not been used"
- Solution: Enable with `gcloud services enable aiplatform.googleapis.com`

**VPC-SC Configuration**

- Error: "Access denied by VPC Service Controls"
- Solution: Add project to service perimeter or adjust ingress/egress policies

**IAM Permission Denied**

- Error: "does not have required permission"
- Solution: Grant roles/owner temporarily to service account running Terraform

**Resource Already Exists**

- Error: "Resource already exists"
- Solution: Import existing resource or use data source instead

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
