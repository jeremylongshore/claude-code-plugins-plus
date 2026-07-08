## CKAN API client - JavaScript

Among other JS clients publicly available, the objectives of this one are:

- **To be completely flexible in terms of which CKAN actions are supported**, so users specify which action should be called by its name rather than my importing and calling a method implemented specifically for the given action. This ensure that all core and custom actions are supported, including all possible parameters.
- **To reduce repetition when calling CKAN actions**, by reading global configurations on environemnt variables (such as the CKAN URL) and having common configurations by default (e.g. all requests by default will have the "content-type" header set to "application/json", avoiding that requests are sent without it and avoing that this has to be repeated everywhere).
- **To properly handle errors**, by properly detecting when an error happened and throwing an error with a useful message that can be shown to the final users.
- **To expose the underlying request properties**, so that anything can be customized e.g. headers

_**NOTE:**_ developed mainly to be used on Next.js projects.

## Usage

Install the package on the project with (or `npm link` for local development):

```
npm i @portaljs/ckan-api-client-js
```

Set the following environment variables on your project:

```bash
NEXT_PUBLIC_CKAN_URL=http://ckan.com # <= This should be updated
```

Import the client with:

```javascript
import CkanRequest from "ckan-api-client-js";
```

### Methods

`CkanRequest` exports 2 main methods:

- `CkanRequest.get("action_name", options)`
- `CkanRequest.post("action_name", options)`

`options` may have the following properties:

- `apiKey` - CKAN API key for authorization
- `headers` - Request headers. E.g. `{ "Authorization": "api_token" }`
- `json` - JSON body for POST requests. E.g. `{ "id": "123" }`
- `formData` - formData for POST requests

### Examples

#### `package_show`

```javascript
const dataset = await CkanRequest.get(
    "package_show?id=123",
    {
        apiKey: "my-token"
    }
);
```

#### `package_patch`

```javascript
const dataset = await CkanRequest.post(
    "package_patch",
    {
        headers: {
            Authorization: "apikey",
        },
        json: { "id": "123", "title": "My new title" },
    }
);
```

#### Error handling

If an exception happens, simply catch that and show its message to the user. Example:

```javascript
try {
    const dataset = CkanRequest.get("package_show?id=123")
} catch (e) {
    alert(e.message) // E.g. "Dataset not found"
}

```

## Development

Currently, `npm link` is being used for development purposes.

To do so, simply build (`npm run build`) the project and then link it (`npm link ...`) on another project to test changes.

