# Error Handling Reference

**API Not Enabled**

- Error: "Vertex AI API has not been used in project"
- Solution: Enable with `gcloud services enable aiplatform.googleapis.com`

**Model Not Found**

- Error: "Model publishers/google/models/... not found"
- Solution: Verify model ID and region availability

**Quota Exceeded**

- Error: "Quota exceeded for resource"
- Solution: Request quota increase or reduce replica count

**KMS Key Access Denied**

- Error: "Permission denied on KMS key"
- Solution: Grant cloudkms.cryptoKeyEncrypterDecrypter role to Vertex AI service account

**Vector Search Build Failed**

- Error: "Index build failed"
- Solution: Check GCS bucket permissions and embedding format

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
