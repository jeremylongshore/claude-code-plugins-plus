# Guidewire Local Dev Loop — Implementation Guide

## Project Structure

```bash
project-root/
├── build.gradle                 # Main build configuration
├── settings.gradle              # Multi-project settings
├── gradle.properties            # Gradle properties
├── modules/
│   ├── configuration/           # Gosu configuration code
│   │   ├── gsrc/               # Gosu source files
│   │   └── config/             # XML configuration
│   └── integration/             # Integration code
├── database/
│   └── upgrade/                 # Database upgrade scripts
└── build/
    └── idea/                    # IDE-specific files
```

## Gradle Local Server Configuration

```groovy
// build.gradle - Local server configuration
plugins {
    id 'com.guidewire.gradle' version '10.12.0'
}

guidewire {
    server {
        port = 8080
        debugPort = 5005
        jvmArgs = [
            '-Xmx4g',
            '-XX:+UseG1GC',
            '-Dgw.server.mode=dev'
        ]
    }

    database {
        server = 'localhost'
        port = 5432
        name = 'pc_dev'
        username = 'postgres'
        password = System.getenv('DB_PASSWORD') ?: 'password'
    }
}

// Hot reload configuration
tasks.register('devServer') {
    dependsOn 'classes'
    doLast {
        exec {
            commandLine 'java', '-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:5005',
                '-jar', 'build/libs/server.jar'
        }
    }
}
```

## Hot Reload Configuration

```gosu
// Enable Gosu hot swap in development
// config/dev-config.xml
<config>
  <development>
    <hot-swap enabled="true"/>
    <gosu-reload enabled="true"/>
    <pcf-reload enabled="true"/>
  </development>
</config>
```

**IDE Configuration for Hot Reload:**
1. Run > Edit Configurations > Remote JVM Debug
2. Set port to 5005
3. Start debug session after server is running

## Gosu Service Example

```gosu
// gsrc/gw/custom/MyService.gs
package gw.custom

uses gw.api.database.Query
uses gw.api.util.Logger

class MyService {
  private static final var LOG = Logger.forCategory("MyService")

  static function processPolicy(policyNumber : String) : Policy {
    LOG.info("Processing policy: ${policyNumber}")

    var policy = Query.make(Policy)
      .compare(Policy#PolicyNumber, Equals, policyNumber)
      .select()
      .AtMostOneRow

    if (policy == null) {
      throw new IllegalArgumentException("Policy not found: ${policyNumber}")
    }

    // Business logic here
    return policy
  }
}
```

## Unit Testing

```gosu
// test/gsrc/gw/custom/MyServiceTest.gs
package gw.custom

uses gw.testharness.v3.PLTestCase
uses gw.testharness.v3.PLAssert

class MyServiceTest extends PLTestCase {

  function testProcessPolicy() {
    // Setup test data
    var account = createTestAccount()
    var policy = createTestPolicy(account)

    // Execute
    var result = MyService.processPolicy(policy.PolicyNumber)

    // Assert
    PLAssert.assertNotNull(result)
    PLAssert.assertEquals(policy.PolicyNumber, result.PolicyNumber)
  }

  private function createTestAccount() : Account {
    var account = new Account()
    account.AccountNumber = "TEST-" + System.currentTimeMillis()
    account.Bundle.commit()
    return account
  }
}
```

## PCF Development

```xml
<!-- pcf/AccountDetailScreen.pcf -->
<?xml version="1.0"?>
<PCF
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:noNamespaceSchemaLocation="pcf.xsd">
  <Screen
    id="AccountDetailScreen"
    editable="true">
    <Require var="account" type="Account"/>

    <Toolbar>
      <ToolbarButton
        action="saveAccount()"
        id="SaveButton"
        label="Save"/>
    </Toolbar>

    <DetailViewPanel>
      <InputColumn>
        <TextInput
          editable="true"
          id="AccountNumber"
          label="Account Number"
          value="account.AccountNumber"/>
        <TextInput
          editable="true"
          id="AccountName"
          label="Account Name"
          value="account.AccountHolderContact.DisplayName"/>
      </InputColumn>
    </DetailViewPanel>

    <Code>
      <![CDATA[
      function saveAccount() {
        account.Bundle.commit()
        util.LocationUtil.addRequestScopedInfoMessage("Account saved")
      }
      ]]>
    </Code>
  </Screen>
</PCF>
```

## Development Commands Cheatsheet

```bash
# Build
./gradlew clean build

# Run server
./gradlew runServer

# Database operations
./gradlew dbUpgrade
./gradlew dbReset
./gradlew loadSampleData

# Testing
./gradlew test
./gradlew test --tests "ClassName.methodName"
./gradlew test --continuous

# Code quality
./gradlew gosucheck
./gradlew spotlessApply

# Generate API documentation
./gradlew apiDoc
```

## IDE Keyboard Shortcuts

| Action | IntelliJ Shortcut |
|--------|-------------------|
| Hot swap code | Ctrl+Shift+F9 |
| Run to cursor | Alt+F9 |
| Evaluate expression | Alt+F8 |
| Find usages | Alt+F7 |
| Go to declaration | Ctrl+B |
| Refactor rename | Shift+F6 |
