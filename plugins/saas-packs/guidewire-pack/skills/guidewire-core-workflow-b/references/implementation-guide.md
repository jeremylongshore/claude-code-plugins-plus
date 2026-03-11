# Guidewire Core Workflow B: Claims Processing — Implementation Guide

## TypeScript: Create FNOL

```typescript
interface FNOLRequest {
  data: {
    attributes: {
      lossDate: string;
      lossTime?: string;
      reportedDate: string;
      lossType: { code: string };
      lossCause: { code: string };
      description: string;
      policyNumber: string;
      lossLocation?: {
        addressLine1: string;
        city: string;
        state: { code: string };
        postalCode: string;
      };
      reporter?: {
        firstName: string;
        lastName: string;
        primaryPhone: string;
        relationship: { code: string };
      };
    };
  };
}

async function createFNOL(fnolData: FNOLData): Promise<Claim> {
  const request: FNOLRequest = {
    data: {
      attributes: {
        lossDate: fnolData.lossDate,
        lossTime: fnolData.lossTime,
        reportedDate: new Date().toISOString().split('T')[0],
        lossType: { code: fnolData.lossType },
        lossCause: { code: fnolData.lossCause },
        description: fnolData.description,
        policyNumber: fnolData.policyNumber,
        lossLocation: {
          addressLine1: fnolData.location.address,
          city: fnolData.location.city,
          state: { code: fnolData.location.state },
          postalCode: fnolData.location.zip
        },
        reporter: {
          firstName: fnolData.reporter.firstName,
          lastName: fnolData.reporter.lastName,
          primaryPhone: fnolData.reporter.phone,
          relationship: { code: 'insured' }
        }
      }
    }
  };

  const response = await claimCenterClient.request<{ data: Claim }>(
    'POST', '/fnol/v1/fnol', request
  );
  console.log(`Created claim: ${response.data.claimNumber}`);
  return response.data;
}
```

## TypeScript: Add Exposures

```typescript
interface ExposureRequest {
  data: {
    attributes: {
      exposureType: { code: string };
      lossParty: { code: string };
      primaryCoverage: { code: string };
      claimant?: { id: string };
      incident?: { id: string };
    };
  };
}

async function addExposure(claimId: string, exposureData: ExposureData): Promise<Exposure> {
  const request: ExposureRequest = {
    data: {
      attributes: {
        exposureType: { code: exposureData.type },
        lossParty: { code: exposureData.lossParty },
        primaryCoverage: { code: exposureData.coverageCode },
        claimant: exposureData.claimantId ? { id: exposureData.claimantId } : undefined
      }
    }
  };

  const response = await claimCenterClient.request<{ data: Exposure }>(
    'POST', `/claim/v1/claims/${claimId}/exposures`, request
  );
  return response.data;
}
```

## TypeScript: Add Vehicle Incident

```typescript
interface VehicleIncidentRequest {
  data: {
    attributes: {
      severity: { code: string };
      description: string;
      vehicle: {
        vin?: string;
        year: number;
        make: string;
        model: string;
        color?: string;
        licensePlate?: string;
      };
      damageDescription: string;
      airbagDeployed?: boolean;
      vehicleOperable?: boolean;
    };
  };
}

async function addVehicleIncident(
  claimId: string, vehicleData: VehicleIncidentData
): Promise<VehicleIncident> {
  const request: VehicleIncidentRequest = {
    data: {
      attributes: {
        severity: { code: vehicleData.severity },
        description: vehicleData.description,
        vehicle: {
          vin: vehicleData.vin,
          year: vehicleData.year,
          make: vehicleData.make,
          model: vehicleData.model,
          licensePlate: vehicleData.licensePlate
        },
        damageDescription: vehicleData.damageDescription,
        airbagDeployed: vehicleData.airbagDeployed,
        vehicleOperable: vehicleData.vehicleOperable
      }
    }
  };

  const response = await claimCenterClient.request<{ data: VehicleIncident }>(
    'POST', `/claim/v1/claims/${claimId}/vehicle-incidents`, request
  );
  return response.data;
}
```

## TypeScript: Set Reserves and Create Payments

```typescript
async function setReserve(
  claimId: string, exposureId: string, reserveData: ReserveData
): Promise<Reserve> {
  const request = {
    data: {
      attributes: {
        reserveLine: { code: reserveData.reserveLine },
        costType: { code: reserveData.costType },
        costCategory: { code: reserveData.costCategory },
        newAmount: { amount: reserveData.amount, currency: 'usd' },
        comments: reserveData.comments
      }
    }
  };

  const response = await claimCenterClient.request<{ data: Reserve }>(
    'POST', `/claim/v1/claims/${claimId}/exposures/${exposureId}/reserves`, request
  );
  console.log(`Set reserve: $${reserveData.amount} on exposure ${exposureId}`);
  return response.data;
}

async function createPayment(
  claimId: string, paymentData: PaymentData
): Promise<Payment> {
  const request = {
    data: {
      attributes: {
        paymentType: { code: paymentData.paymentType },
        exposure: { id: paymentData.exposureId },
        payee: {
          payeeType: { code: paymentData.payeeType },
          claimContact: paymentData.claimContactId
            ? { id: paymentData.claimContactId } : undefined
        },
        reserveLine: { code: 'indemnity' },
        costType: { code: paymentData.costType },
        costCategory: { code: paymentData.costCategory },
        amount: { amount: paymentData.amount, currency: 'usd' },
        comments: paymentData.comments,
        paymentMethod: { code: paymentData.method || 'check' }
      }
    }
  };

  const response = await claimCenterClient.request<{ data: Payment }>(
    'POST', `/claim/v1/claims/${claimId}/payments`, request
  );
  console.log(`Created payment: $${paymentData.amount} - Check #${response.data.checkNumber}`);
  return response.data;
}
```

## TypeScript: Close Exposure and Claim

```typescript
async function closeExposure(
  claimId: string, exposureId: string, outcome: string
): Promise<Exposure> {
  const response = await claimCenterClient.request<{ data: Exposure }>(
    'POST', `/claim/v1/claims/${claimId}/exposures/${exposureId}/close`,
    { data: { attributes: { closedOutcome: { code: outcome } } } }
  );
  return response.data;
}

async function closeClaim(claimId: string): Promise<Claim> {
  const response = await claimCenterClient.request<{ data: Claim }>(
    'POST', `/claim/v1/claims/${claimId}/close`,
    { data: { attributes: { closedOutcome: { code: 'completed' } } } }
  );
  console.log(`Closed claim: ${response.data.claimNumber}`);
  return response.data;
}
```

## Gosu: Complete Claims Workflow

```gosu
package gw.custom.claim

uses gw.api.util.Logger
uses gw.cc.claim.Claim
uses gw.cc.exposure.Exposure
uses gw.transaction.Transaction

class ClaimWorkflow {
  private static final var LOG = Logger.forCategory("ClaimWorkflow")

  static function createClaim(
    policyNumber : String, lossDate : Date,
    lossType : LossType, description : String
  ) : Claim {
    return Transaction.runWithNewBundle(\bundle -> {
      var policy = findPolicy(policyNumber)
      if (policy == null) {
        throw new IllegalArgumentException("Policy not found: ${policyNumber}")
      }

      var claim = new Claim(bundle)
      claim.Policy = policy
      claim.LossDate = lossDate
      claim.LossType = lossType
      claim.Description = description
      claim.ReportedDate = Date.Today
      claim.LossCause = LossCause.TC_VEHCOLLISION
      claim.open()

      LOG.info("Created claim: ${claim.ClaimNumber}")
      return claim
    })
  }

  static function addVehicleExposure(
    claim : Claim, vehicle : Vehicle, coverageCode : String
  ) : Exposure {
    return Transaction.runWithNewBundle(\bundle -> {
      var claim = bundle.add(claim)

      var incident = new VehicleIncident(bundle)
      incident.Claim = claim
      incident.Vehicle = vehicle
      incident.Description = "Vehicle damage from ${claim.LossCause.DisplayName}"

      var exposure = new Exposure(bundle)
      exposure.Claim = claim
      exposure.ExposureType = ExposureType.TC_VEHICLEDAMAGE
      exposure.LossParty = LossPartyType.TC_INSURED
      exposure.PrimaryCoverage = CoverageType.get(coverageCode)
      exposure.VehicleIncident = incident

      LOG.info("Created exposure: ${exposure.ExposureType.DisplayName}")
      return exposure
    })
  }

  static function setExposureReserve(
    exposure : Exposure, amount : java.math.BigDecimal, reserveLine : ReserveLine
  ) {
    Transaction.runWithNewBundle(\bundle -> {
      var exp = bundle.add(exposure)
      var reserve = new Reserve(bundle)
      reserve.Exposure = exp
      reserve.ReserveLine = reserveLine
      reserve.CostType = CostType.TC_CLAIMCOST
      reserve.CostCategory = CostCategory.TC_BODY
      reserve.NewAmount = new gw.api.financials.CurrencyAmount(amount, Currency.TC_USD)
      reserve.Comments = "Initial reserve set"

      LOG.info("Set reserve: ${amount} on ${exp.ExposureType.DisplayName}")
    })
  }

  static function createPayment(
    exposure : Exposure, amount : java.math.BigDecimal,
    payee : Contact, paymentType : PaymentType
  ) : Payment {
    return Transaction.runWithNewBundle(\bundle -> {
      var exp = bundle.add(exposure)
      var payment = new Payment(bundle)
      payment.Exposure = exp
      payment.Claim = exp.Claim
      payment.PaymentType = paymentType
      payment.ReserveLine = ReserveLine.TC_INDEMNITY
      payment.CostType = CostType.TC_CLAIMCOST
      payment.CostCategory = CostCategory.TC_BODY
      payment.Payee = payee
      payment.GrossAmount = new gw.api.financials.CurrencyAmount(amount, Currency.TC_USD)
      payment.submit()

      LOG.info("Created payment: ${amount} to ${payee.DisplayName}")
      return payment
    })
  }

  static function closeClaim(claim : Claim, outcome : CloseOutcome) {
    Transaction.runWithNewBundle(\bundle -> {
      var c = bundle.add(claim)
      c.Exposures
        .where(\e -> e.State == ExposureState.TC_OPEN)
        .each(\e -> e.close(outcome))
      c.close(outcome)
      LOG.info("Closed claim: ${c.ClaimNumber}")
    })
  }
}
```

## Claim Types and Loss Causes

```typescript
const lossTypes = {
  AUTO: ['vehcollision', 'vehglass', 'vehtheft', 'vehvandalism'],
  PROPERTY: ['fire', 'water', 'theft', 'weather'],
  LIABILITY: ['bodily_injury', 'property_damage', 'personal_injury'],
  WORKERS_COMP: ['injury', 'illness', 'death']
};

function getDefaultExposures(lossType: string, lossCause: string): string[] {
  if (lossType === 'AUTO' && lossCause === 'vehcollision') {
    return ['VehicleDamage', 'BodilyInjury', 'PropertyDamage'];
  }
  return [];
}
```
