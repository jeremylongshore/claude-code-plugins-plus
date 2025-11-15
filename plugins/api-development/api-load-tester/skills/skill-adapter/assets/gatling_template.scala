import scala.concurrent.duration._

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import io.gatling.jdbc.Predef._

class APILoadTest extends Simulation {

  // --- Configuration ---
  // Configure the target URL and request parameters here.
  val baseURL = "${BASE_URL}" // e.g., "http://example.com"
  val endpoint = "${ENDPOINT}" // e.g., "/api/resource"
  val requestName = "Get Resource" // Descriptive name for the request
  val requestBody = """${REQUEST_BODY}""" // JSON request body (optional)

  // --- HTTP Protocol Configuration ---
  val httpProtocol = http
    .baseUrl(baseURL)
    .acceptHeader("application/json")
    .contentTypeHeader("application/json")
    // Add any other headers or configurations you need here.
    // .userAgentHeader("Gatling/3.7.0") // Example User-Agent header

  // --- Scenario Definition ---
  val scn = scenario("API Load Test Scenario")
    .exec(
      http(requestName)
        .get(endpoint) // Or .post(endpoint).body(StringBody(requestBody)) if it's a POST request
        //.headers(Map("Custom-Header" -> "value")) // Example custom header
        .check(status.is(200)) // Validate the response status
        // Add more checks as needed to validate the response data.
        // .check(jsonPath("$.someField").is("expectedValue"))
    )

  // --- Simulation Setup ---
  setUp(
    scn.inject(
      // Define your load profile here. Examples:
      // - Constant load of 10 users per second for 30 seconds
      // constantUsersPerSec(10).during(30.seconds),

      // - Ramp up from 1 to 10 users over 20 seconds
      // rampUsersPerSec(1).to(10).during(20.seconds),

      // - Constant load for a period, then a ramp-up, then another constant load
      // constantUsersPerSec(5).during(10.seconds),
      // rampUsersPerSec(5).to(15).during(10.seconds),
      // constantUsersPerSec(15).during(10.seconds)

      // Placeholders for easy adjustments.  Replace these with your desired values.
      constantUsersPerSec(${USERS_PER_SECOND}).during(${DURATION_SECONDS}.seconds)
    ).protocols(httpProtocol)
  )
  // Add global assertions if needed.  For example:
  // .assertions(
  //   global.responseTime.max.lt(1000), // Ensure maximum response time is less than 1000ms
  //   global.successfulRequests.percent.gt(95) // Ensure success rate is greater than 95%
  // )
}