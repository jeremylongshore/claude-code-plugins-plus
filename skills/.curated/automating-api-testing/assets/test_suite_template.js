/**
 * test_suite_template.js
 *
 * Template for generating API test suites.  This template provides a structure
 * for creating comprehensive test cases for various API endpoints.
 *
 * @example
 * // Example usage (after replacing placeholders):
 * const testSuite = require('./test_suite_template');
 *
 * const config = {
 *   baseURL: 'https://api.example.com',
 *   endpoint: '/users',
 *   method: 'GET',
 *   description: 'Retrieve all users'
 * };
 *
 * const testCase = testSuite(config);
 *
 * describe(config.description, () => {
 *   it('should return a 200 OK status', async () => {
 *     const response = await testCase.request();
 *     expect(response.status).toBe(200);
 *   });
 *   // Add more test cases here...
 * });
 */

/**
 * Generates a test suite based on the provided configuration.
 *
 * @param {object} config - Configuration object for the test suite.
 * @param {string} config.baseURL - The base URL of the API.
 * @param {string} config.endpoint - The API endpoint to test.
 * @param {string} config.method - The HTTP method to use (GET, POST, PUT, DELETE, etc.).
 * @param {string} config.description - A description of the test case.
 * @param {object} [config.headers] - Optional headers to include in the request.
 * @param {object} [config.body] - Optional request body.
 * @param {string} [config.authenticationType] - Optional authentication type (e.g., 'Bearer', 'OAuth', 'API Key').
 * @param {string} [config.authenticationToken] - Optional authentication token or API key.
 * @returns {object} An object containing the request function.
 */
module.exports = (config) => {
  const axios = require('axios'); // Consider making axios a configurable dependency if needed

  /**
   * Executes the API request based on the configuration.
   *
   * @async
   * @function request
   * @returns {Promise<object>} A promise that resolves to the API response.
   * @throws {Error} If the request fails.
   */
  async function request() {
    try {
      const requestConfig = {
        method: config.method,
        url: config.baseURL + config.endpoint,
        headers: config.headers || {},
        data: config.body || null, // Use data for POST/PUT requests, params for GET
        // params: config.method === 'GET' ? config.body : null // Alternate: use params for GET requests
      };

      // Authentication handling
      if (config.authenticationType === 'Bearer' && config.authenticationToken) {
        requestConfig.headers.Authorization = `Bearer ${config.authenticationToken}`;
      } else if (config.authenticationType === 'API Key' && config.authenticationToken) {
        // Example API Key header - adjust based on API requirements
        requestConfig.headers['X-API-Key'] = config.authenticationToken;
      } // Add more authentication types as needed

      const response = await axios(requestConfig);
      return response;
    } catch (error) {
      // Handle errors appropriately (e.g., log, re-throw, or return a custom error object)
      console.error(`Request failed for ${config.description}:`, error.message);
      throw error; // Re-throw the error for the test to handle
    }
  }

  return {
    request,

    // Add more helper functions here if needed (e.g., for data validation)
    validateResponseSchema: (response, schema) => {
      // Placeholder: Implement schema validation logic using a library like Joi or Ajv
      // Example:
      // const validationResult = schema.validate(response.data);
      // if (validationResult.error) {
      //   throw new Error(`Schema validation failed: ${validationResult.error.message}`);
      // }
    },
    extractDataFromResponse: (response, path) => {
        // Placeholder: Implement logic to extract data from the response using a library like lodash.get
        // Example:
        // return _.get(response.data, path);
    }
  };
};