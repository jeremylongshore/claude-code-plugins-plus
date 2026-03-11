# Guidewire CI Integration — Implementation Guide

## GitHub Actions Workflow

```yaml
# .github/workflows/guidewire-ci.yml
name: Guidewire CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  JAVA_VERSION: '17'
  GRADLE_VERSION: '8.5'
  GW_TENANT_ID: ${{ secrets.GW_TENANT_ID }}

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          java-version: ${{ env.JAVA_VERSION }}
          distribution: 'temurin'
          cache: 'gradle'
      - run: chmod +x gradlew
      - run: ./gradlew build --no-daemon
      - run: ./gradlew gosucheck --no-daemon
      - uses: actions/upload-artifact@v4
        with:
          name: build-artifacts
          path: build/libs/

  test:
    needs: build
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: pc_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports: ['5432:5432']
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          java-version: ${{ env.JAVA_VERSION }}
          distribution: 'temurin'
          cache: 'gradle'
      - uses: actions/download-artifact@v4
        with:
          name: build-artifacts
          path: build/libs/
      - run: |
          ./gradlew dbupgrade -PdbHost=localhost -PdbName=pc_test \
            -PdbUser=postgres -PdbPassword=postgres --no-daemon
      - run: ./gradlew test --no-daemon
      - run: ./gradlew integrationTest --no-daemon
        env:
          DB_HOST: localhost
          DB_NAME: pc_test
          DB_USER: postgres
          DB_PASSWORD: postgres
      - if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: build/reports/tests/
      - uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: build/reports/jacoco/

  security-scan:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/analyze@v2
        with:
          languages: java
      - run: ./gradlew dependencyCheckAnalyze --no-daemon
      - uses: actions/upload-artifact@v4
        with:
          name: security-report
          path: build/reports/dependency-check/

  deploy-sandbox:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment: sandbox
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: build-artifacts
          path: build/libs/
      - env:
          GW_CLIENT_ID: ${{ secrets.GW_SANDBOX_CLIENT_ID }}
          GW_CLIENT_SECRET: ${{ secrets.GW_SANDBOX_CLIENT_SECRET }}
        run: ./scripts/deploy-to-cloud.sh sandbox
      - run: ./gradlew smokeTest -Penv=sandbox --no-daemon

  deploy-production:
    needs: deploy-sandbox
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://your-tenant.cloud.guidewire.com
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: build-artifacts
          path: build/libs/
      - env:
          GW_CLIENT_ID: ${{ secrets.GW_PROD_CLIENT_ID }}
          GW_CLIENT_SECRET: ${{ secrets.GW_PROD_CLIENT_SECRET }}
        run: ./scripts/deploy-to-cloud.sh production
      - run: ./gradlew productionVerify -Penv=production --no-daemon
```

## Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent {
        docker {
            image 'eclipse-temurin:17-jdk'
            args '-v gradle-cache:/root/.gradle'
        }
    }

    environment {
        GRADLE_OPTS = '-Dorg.gradle.daemon=false'
        GW_TENANT_ID = credentials('gw-tenant-id')
    }

    options {
        timeout(time: 1, unit: 'HOURS')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('Checkout') { steps { checkout scm } }
        stage('Build') {
            steps {
                sh 'chmod +x gradlew'
                sh './gradlew clean build'
            }
            post {
                success { archiveArtifacts artifacts: 'build/libs/*.jar', fingerprint: true }
            }
        }
        stage('Code Quality') {
            parallel {
                stage('Gosu Check') { steps { sh './gradlew gosucheck' } }
                stage('Static Analysis') {
                    steps { sh './gradlew spotbugsMain' }
                    post {
                        always {
                            recordIssues(tools: [spotBugs(pattern: '**/build/reports/spotbugs/*.xml')])
                        }
                    }
                }
            }
        }
        stage('Test') {
            steps { sh './gradlew test integrationTest' }
            post {
                always {
                    junit '**/build/test-results/**/*.xml'
                    publishHTML([
                        reportDir: 'build/reports/tests/test',
                        reportFiles: 'index.html',
                        reportName: 'Test Report'
                    ])
                }
            }
        }
        stage('Security Scan') {
            steps { sh './gradlew dependencyCheckAnalyze' }
            post {
                always { dependencyCheckPublisher pattern: '**/dependency-check-report.xml' }
            }
        }
        stage('Deploy Sandbox') {
            when { branch 'develop' }
            environment {
                GW_CLIENT_ID = credentials('gw-sandbox-client-id')
                GW_CLIENT_SECRET = credentials('gw-sandbox-client-secret')
            }
            steps {
                sh './scripts/deploy-to-cloud.sh sandbox'
                sh './gradlew smokeTest -Penv=sandbox'
            }
        }
        stage('Deploy Production') {
            when { branch 'main' }
            environment {
                GW_CLIENT_ID = credentials('gw-prod-client-id')
                GW_CLIENT_SECRET = credentials('gw-prod-client-secret')
            }
            steps {
                input message: 'Deploy to production?', ok: 'Deploy'
                sh './scripts/deploy-to-cloud.sh production'
            }
        }
    }

    post {
        always { cleanWs() }
        failure {
            emailext(
                subject: "Build Failed: ${env.JOB_NAME} [${env.BUILD_NUMBER}]",
                body: "Check console output at ${env.BUILD_URL}",
                recipientProviders: [developers()]
            )
        }
    }
}
```

## Gradle CI Configuration

```groovy
// build.gradle - CI-optimized configuration
plugins {
    id 'com.guidewire.gradle' version '10.12.0'
    id 'org.owasp.dependencycheck' version '9.0.0'
    id 'com.github.spotbugs' version '6.0.0'
    id 'jacoco'
}

java {
    toolchain { languageVersion = JavaLanguageVersion.of(17) }
}

tasks.named('gosucheck') {
    reports {
        xml.required = true
        html.required = true
    }
}

test {
    useJUnitPlatform()
    maxParallelForks = Runtime.runtime.availableProcessors().intdiv(2) ?: 1
    testLogging {
        events 'passed', 'skipped', 'failed'
        showStandardStreams = false
        exceptionFormat = 'full'
    }
    finalizedBy jacocoTestReport
}

tasks.register('integrationTest', Test) {
    description = 'Runs integration tests'
    group = 'verification'
    testClassesDirs = sourceSets.integrationTest.output.classesDirs
    classpath = sourceSets.integrationTest.runtimeClasspath
    shouldRunAfter test
}

jacocoTestReport {
    dependsOn test
    reports {
        xml.required = true
        html.required = true
    }
}

jacocoTestCoverageVerification {
    violationRules {
        rule {
            limit { minimum = 0.7 }
        }
    }
}

dependencyCheck {
    formats = ['HTML', 'XML', 'JSON']
    failBuildOnCVSS = 7.0
    suppressionFile = 'config/dependency-check-suppressions.xml'
}

spotbugs {
    effort = 'max'
    reportLevel = 'medium'
    excludeFilter = file('config/spotbugs-exclude.xml')
}

tasks.register('ci') {
    description = 'Runs all CI checks'
    group = 'verification'
    dependsOn 'build', 'gosucheck', 'test', 'integrationTest',
              'jacocoTestCoverageVerification', 'dependencyCheckAnalyze'
}
```

## CI Test Utilities (Gosu)

```gosu
package gw.test.ci

uses gw.testharness.v3.PLTestCase
uses gw.api.database.Query

class CITestBase extends PLTestCase {

  static property get SkipSlowTests() : boolean {
    return System.getenv("CI") == "true" &&
           System.getenv("RUN_SLOW_TESTS") != "true"
  }

  static function verifyDatabaseConnection() : boolean {
    try {
      var count = Query.make(Account).select().Count
      return true
    } catch (e : Exception) {
      return false
    }
  }

  override function beforeClass() {
    super.beforeClass()
    cleanupTestData()
  }

  protected function cleanupTestData() {
    Query.make(Account)
      .compare(Account#AccountNumber, StartsWith, "TEST-")
      .select()
      .each(\account -> {
        gw.transaction.Transaction.runWithNewBundle(\bundle -> {
          bundle.delete(bundle.add(account))
        })
      })
  }
}
```

## Deployment Script

```bash
#!/bin/bash
# scripts/deploy-to-cloud.sh

set -e

ENV=${1:-sandbox}

echo "=== Deploying to Guidewire Cloud ($ENV) ==="

if [[ "$ENV" != "sandbox" && "$ENV" != "production" ]]; then
    echo "Invalid environment: $ENV"
    exit 1
fi

# Get access token
TOKEN=$(curl -s -X POST "${GW_HUB_URL}/oauth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=client_credentials&client_id=${GW_CLIENT_ID}&client_secret=${GW_CLIENT_SECRET}" \
    | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
    echo "Failed to obtain access token"
    exit 1
fi

# Deploy configuration package
echo "Deploying configuration package..."
DEPLOYMENT_RESPONSE=$(curl -s -X POST "${GW_API_URL}/deployment/v1/packages" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/zip" \
    --data-binary @build/libs/configuration-package.zip)

DEPLOYMENT_ID=$(echo $DEPLOYMENT_RESPONSE | jq -r '.deploymentId')
echo "Deployment ID: $DEPLOYMENT_ID"

# Wait for deployment to complete
echo "Waiting for deployment to complete..."
while true; do
    STATUS=$(curl -s "${GW_API_URL}/deployment/v1/packages/${DEPLOYMENT_ID}" \
        -H "Authorization: Bearer ${TOKEN}" \
        | jq -r '.status')

    echo "Status: $STATUS"

    if [ "$STATUS" == "COMPLETED" ]; then
        echo "Deployment completed successfully"
        break
    elif [ "$STATUS" == "FAILED" ]; then
        echo "Deployment failed"
        exit 1
    fi

    sleep 30
done

echo "=== Deployment Complete ==="
```
