# Deprecation Notice Template

This template provides a structure for creating clear and informative deprecation notices for your API endpoints. Use this template to communicate upcoming changes to your users and guide them through the migration process.

## 1. Endpoint Identification

Clearly identify the API endpoint being deprecated. Provide the full URL, the HTTP method, and a brief description.

**Example:**

*   **Endpoint:** `GET /users/{user_id}`
*   **Description:** Retrieves user information by ID.

## 2. Deprecation Date

Specify the exact date when the endpoint will be officially deprecated. This date should be clearly visible and easily understandable.

**Example:**

*   **Deprecation Date:** 2024-12-31

## 3. Sunset Date (Removal Date)

State the date when the deprecated endpoint will be completely removed and no longer functional. This is crucial for users to plan their migration.

**Example:**

*   **Sunset Date:** 2025-06-30

## 4. Reason for Deprecation

Explain the reason behind the deprecation. Be transparent and provide context. This helps users understand the need for the change.

**Examples:**

*   "This endpoint is being deprecated in favor of the new `GET /v2/users/{user_id}` endpoint, which offers improved performance and security."
*   "This endpoint relies on outdated technology and is being replaced with a more modern and scalable solution."
*   "This endpoint is being deprecated due to low usage and maintenance costs."

## 5. Recommended Alternative

Provide a clear and specific alternative to the deprecated endpoint. Include the full URL, HTTP method, and a description of its functionality.

**Example:**

*   **Alternative Endpoint:** `GET /v2/users/{user_id}`
*   **Description:** Retrieves user information by ID using a more efficient data structure.

## 6. Migration Guide

Provide detailed instructions on how to migrate from the deprecated endpoint to the recommended alternative. This should include code examples, data mapping information, and any other relevant details.

**Example:**

To migrate to the new endpoint, please follow these steps:

1.  Replace all instances of `GET /users/{user_id}` with `GET /v2/users/{user_id}`.
2.  The response format for the new endpoint is slightly different.  The `name` field has been split into `firstName` and `lastName` fields.  Update your code accordingly.
    *   **Old:** `{"id": 123, "name": "John Doe"}`
    *   **New:** `{"id": 123, "firstName": "John", "lastName": "Doe"}`
3.  Ensure you are handling any potential errors returned by the new endpoint.

## 7. Impact of Deprecation

Explain the potential impact of the deprecation on users who continue to use the deprecated endpoint after the deprecation date.

**Examples:**

*   "After the deprecation date, this endpoint will continue to function but will no longer receive updates or bug fixes."
*   "After the sunset date, this endpoint will return a `410 Gone` error."

## 8. Support and Contact Information

Provide contact information for users who have questions or need assistance with the migration process.

**Example:**

If you have any questions or require assistance with the migration, please contact our support team at [support@example.com](mailto:support@example.com) or visit our documentation at [https://example.com/docs/api-migration](https://example.com/docs/api-migration).

## 9. Versioning Information (Optional)

If your API uses versioning, include information about the API version being deprecated.

**Example:**

*   **Affected API Version(s):** v1

## Example Complete Notice

---

**Endpoint:** `POST /orders`
**Description:** Creates a new order.
**Deprecation Date:** 2024-11-15
**Sunset Date:** 2025-05-15
**Reason for Deprecation:**  This endpoint is being deprecated due to security vulnerabilities.
**Recommended Alternative:** `POST /v2/orders`
**Description:** Creates a new order using a more secure authentication method.
**Migration Guide:**  Please update your code to use the `POST /v2/orders` endpoint. The request body format is the same.  You will need to update your authentication headers to use the new API key provided in your account settings.
**Impact of Deprecation:** After 2025-05-15, `POST /orders` will return a `403 Forbidden` error.
**Support and Contact Information:** Contact support@example.com for assistance.

---

**Remember to replace the placeholder information with your specific details.**