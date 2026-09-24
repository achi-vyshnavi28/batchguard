# PRD 1.1: Equipment cleaning log and batch rejection

**Author:** Product · **Status:** Draft for review · **Target release:** BatchGuard 1.1

## Problem
Operators record equipment cleaning on paper; QA cannot see whether the blender was cleaned before a batch started.
When a batch fails, there is no way to reject it in the system: it stays "in review" forever.

## User stories

### US-101 Record equipment cleaning
As an operator, I want to record that I cleaned a piece of equipment, so QA can confirm it was clean before use.
- The operator selects the equipment, the cleaning type (minor/major) and confirms with an e-signature.
- The cleaning record shows who cleaned it and when.
- A supervisor verifies major cleanings.

### US-102 Block batch start on dirty equipment
As QA, I want batches not to start on equipment that isn't clean, so we avoid cross-contamination.
- A batch cannot be created if its equipment has not been cleaned since its last use.
- Cleaning is valid for 72 hours.

### US-103 Reject a batch
As QA, I want to reject a failed batch so it is clearly not released.
- QA can reject a batch that is in review.
- Rejection requires a reason and an e-signature.
- The system should handle rejection quickly and be user-friendly.

### US-104 Override
As QA, I want to override the cleaning check when needed.
- QA can override as needed.

### US-105 Cleaning report
As a QA manager, I want a report of cleanings.
- The report shows cleanings. TBD which filters.
