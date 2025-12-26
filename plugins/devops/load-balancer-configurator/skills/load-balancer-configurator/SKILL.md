---
name: configuring-load-balancers
description: |
  Use when configuring load balancers including ALB, NLB, Nginx, and HAProxy. Trigger with phrases like "configure load balancer", "create ALB", "setup nginx load balancing", or "haproxy configuration". Generates production-ready configurations with health checks, SSL termination, sticky sessions, and traffic distribution rules.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(aws:*), Bash(gcloud:*), Bash(nginx:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
## Prerequisites

Before using this skill, ensure:
- Backend servers are identified with IPs or DNS names
- Load balancer type is determined (ALB, NLB, Nginx, HAProxy)
- SSL certificates are available if using HTTPS
- Health check endpoints are defined
- Understanding of traffic distribution requirements (round-robin, least-connections)
- Cloud provider CLI installed (if using cloud load balancers)

## Instructions

1. **Select Load Balancer Type**: Choose based on requirements (L4 vs L7, cloud vs on-prem)
2. **Define Backend Pool**: List backend servers with ports and weights
3. **Configure Health Checks**: Set check interval, timeout, and healthy threshold
4. **Set Up SSL/TLS**: Configure certificates and cipher suites
5. **Define Routing Rules**: Create path-based or host-based routing
6. **Enable Session Persistence**: Configure sticky sessions if needed
7. **Add Monitoring**: Set up logging and metrics collection
8. **Test Configuration**: Validate syntax and test traffic distribution

## Output

**Nginx Configuration:**
```nginx
# {baseDir}/nginx/load-balancer.conf


## Overview

This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.
upstream backend_servers {
    least_conn;
    server 10.0.1.10:8080 weight=3;
    server 10.0.1.11:8080 weight=2;
    server 10.0.1.12:8080 backup;
}

server {
    listen 80;
    server_name app.example.com;

    location / {
        proxy_pass http://backend_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /health {
        access_log off;
        return 200 "healthy\n";
    }
}
```

**AWS ALB (Terraform):**
```hcl
# {baseDir}/terraform/alb.tf
resource "aws_lb" "app_alb" {
  name               = "app-load-balancer"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = aws_subnet.public[*].id
}

resource "aws_lb_target_group" "app_tg" {
  name     = "app-target-group"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    path                = "/health"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

resource "aws_lb_listener" "app_listener" {
  load_balancer_arn = aws_lb.app_alb.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.cert.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_tg.arn
  }
}
```

## Error Handling

**Backend Server Unreachable**
- Error: "502 Bad Gateway" or connection refused
- Solution: Verify backend server IPs, ports, and firewall rules

**SSL Certificate Error**
- Error: "certificate verify failed"
- Solution: Check certificate validity, chain, and private key match

**Health Check Failures**
- Error: "Target is unhealthy"
- Solution: Verify health check path returns 200 status and backends are running

**Configuration Syntax Error**
- Error: "nginx: configuration file test failed"
- Solution: Run `nginx -t` to validate syntax and fix errors

**Session Persistence Not Working**
- Issue: Users losing session on subsequent requests
- Solution: Enable sticky sessions using cookie-based or IP-based persistence

## Resources

- Nginx documentation: https://nginx.org/en/docs/
- HAProxy configuration guide: https://www.haproxy.org/
- AWS ALB documentation: https://docs.aws.amazon.com/elasticloadbalancing/
- GCP Load Balancing: https://cloud.google.com/load-balancing/docs
- Example configurations in {baseDir}/lb-examples/