# Examples

**Example: Debug Failed Command**
Request: "npm install failed with ENOENT error"
Result: Analysis shows missing directory, suggests mkdir or path fix

**Example: Generate Complex Command**
Request: "Find all files modified in last 24 hours over 1MB"
Result: `find . -type f -mtime -1 -size +1M -exec ls -lh {} \;`

**Example: Script Generation**
Request: "Create script to backup database and upload to S3"
Result: Shell script with pg_dump, compression, aws s3 cp with error handling

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
