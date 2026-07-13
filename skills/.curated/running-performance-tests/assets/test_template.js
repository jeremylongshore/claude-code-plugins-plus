// test_template.js - Template for K6 performance tests

// Import necessary modules from K6
import http from 'k6/http';
import { check, sleep } from 'k6';

// Configuration options
export const options = {
  // Stages define the load pattern
  stages: [
    // Example: Ramp-up to 10 virtual users (VUs) over 10 seconds
    { duration: '10s', target: 10 },

    // Example: Maintain 10 VUs for 30 seconds
    { duration: '30s', target: 10 },

    // Example: Ramp-down to 0 VUs over 10 seconds
    { duration: '10s', target: 0 },
  ],

  // Thresholds define pass/fail criteria
  thresholds: {
    // Example: 95th percentile response time should be below 200ms
    http_req_duration: ['p95<200'],

    // Example: 99% of requests should be successful
    http_req_failed: ['rate<0.01'], // <1% failure rate
  },
};

// Define the virtual user (VU) function
export default function () {
  // Replace with your target URL
  const url = 'YOUR_TARGET_URL_HERE';

  // Replace with your request parameters (optional)
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  // Replace with your request body (optional)
  const payload = JSON.stringify({
    key1: 'value1',
    key2: 'value2',
  });

  // Make an HTTP request
  const res = http.get(url, params); // or use http.post, http.put, http.delete, etc.

  // Check the response status code
  check(res, {
    'status is 200': (r) => r.status === 200,
  });

  // Add more checks as needed
  // Example: check(res, { 'response time < 500ms': (r) => r.timings.duration < 500 });

  // Introduce a delay between requests (optional)
  sleep(1); // Sleep for 1 second

  // Log response data for debugging (optional - REMOVE IN PRODUCTION!)
  // console.log(res.body);
}