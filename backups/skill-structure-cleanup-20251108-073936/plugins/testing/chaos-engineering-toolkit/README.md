# Chaos Engineering Toolkit

Chaos testing for resilience with failure injection, latency simulation, and system resilience validation.

## Installation

```bash
/plugin install chaos-engineering-toolkit@claude-code-plugins-plus
```

## Usage

The chaos engineering agent activates automatically when discussing:
- System resilience testing
- Failure injection strategies
- Chaos experiments (GameDays)
- Recovery mechanism validation

Or invoke directly in conversation:
```
"Help me design a chaos experiment to test our payment service resilience"
```

## Features

- **Failure Injection**: Controlled failure scenarios
- **Latency Simulation**: Network delays and timeouts
- **Resource Exhaustion**: CPU, memory, disk limits
- **Resilience Validation**: Circuit breaker and retry testing
- **Chaos Experiments**: Scientific method-based GameDays
- **Multi-Tool Support**: Chaos Mesh, Gremlin, Toxiproxy, AWS FIS

## Example Scenarios

```bash
# Design database failover test
"Design a chaos experiment for database failover"

# Test API resilience under latency
"Create latency injection test for our API gateway"

# Validate circuit breaker behavior
"Test if our circuit breakers work during dependency failures"
```

## Supported Tools

- Chaos Mesh (Kubernetes)
- Gremlin (Enterprise)
- AWS Fault Injection Simulator
- Toxiproxy (Network simulation)
- Chaos Monkey (Netflix)
- Pumba (Docker chaos)

## Files

- `agents/chaos-engineer.md` - Chaos engineering specialist agent

## License

MIT
