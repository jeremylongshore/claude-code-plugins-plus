# Error Handling Reference

Common issues and solutions:

**Memory File Not Found**

- Error: Cannot locate project memory file
- Solution: Initialize new memory file in standard location, prompt user to set up memory persistence

**Conflicting Memories**

- Error: Multiple memories contradict each other
- Solution: Apply most recent memory, allow current request to override, suggest cleanup

**Invalid Memory Format**

- Error: Memory file corrupted or improperly formatted
- Solution: Backup existing file, recreate with valid JSON structure, restore recoverable entries

**Permission Denied**

- Error: Cannot read or write memory file
- Solution: Check file permissions, request necessary access, use alternative storage location

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
