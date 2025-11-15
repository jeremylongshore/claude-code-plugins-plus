// k6 load test script template

import http from 'k6/http';
import { check, sleep } from 'k6';

// Configuration options
export const options = {
  stages: [
    { duration: '10s', target: 10 }, // Ramp up to 10 virtual users (VUs) over 10 seconds
    { duration: '30s', target: 10 }, // Stay at 10 VUs for 30 seconds
    { duration: '10s', target: 0 },  // Ramp down to 0 VUs over 10 seconds
  ],
  thresholds: {
    http_req_duration: ['p95<500'], // 95% of requests must complete below 500ms
    http_req_failed: ['rate<0.01'],   // Error rate must be less than 1%
  },
};

// Virtual User (VU) function
export default function () {
  // Replace with your API endpoint
  const url = 'YOUR_API_ENDPOINT';

  // Replace with your request body (if needed)
  const payload = JSON.stringify({
    key1: 'value1',
    key2: 'value2',
  });

  // Replace with your request headers (if needed)
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  // Make the HTTP request
  const res = http.post(url, payload, params);

  // Check the response status code
  check(res, {
    'is status 200': (r) => r.status === 200,
  });

  // Add more checks as needed (e.g., response body validation)
  // check(res, {
  //   'verify response': (r) => r.body.includes('expected_value'),
  // });

  // Sleep for a short duration between requests (adjust as needed)
  sleep(1);
}