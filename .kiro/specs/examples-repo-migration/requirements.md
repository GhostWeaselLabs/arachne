# Requirements Document

## Introduction

This feature involves migrating the examples and notebooks directories from the main meridian repository into a separate public GitHub repository called "meridian-runtime-examples". This separation will improve the main repository's focus on core functionality while providing a dedicated space for examples and tutorials. The documentation will be updated to reference the new repository appropriately.

## Requirements

### Requirement 1

**User Story:** As a developer exploring Meridian, I want to access examples and notebooks in a dedicated repository, so that I can easily find and contribute example code without cluttering the main codebase.

#### Acceptance Criteria

1. WHEN the migration is complete THEN the system SHALL have a new public GitHub repository named "meridian-runtime-examples"
2. WHEN accessing the new repository THEN it SHALL contain all current examples from the examples/ directory
3. WHEN accessing the new repository THEN it SHALL contain all current notebooks from the notebooks/ directory
4. WHEN viewing the new repository THEN it SHALL have appropriate README documentation explaining the examples structure
5. WHEN the migration is complete THEN the original examples/ and notebooks/ directories SHALL be removed from the main repository

### Requirement 2

**User Story:** As a user reading Meridian documentation, I want updated links and references to examples, so that I can easily navigate to the correct example code location.

#### Acceptance Criteria

1. WHEN viewing documentation THEN all references to examples SHALL point to the new meridian-runtime-examples repository
2. WHEN clicking example links in documentation THEN they SHALL successfully navigate to the correct files in the new repository
3. WHEN viewing the main README THEN it SHALL include a clear reference to the examples repository
4. WHEN accessing documentation examples THEN the links SHALL use stable GitHub URLs that won't break with repository updates

### Requirement 3

**User Story:** As a maintainer, I want the repository migration to preserve git history and maintain proper attribution, so that contributor history is not lost.

#### Acceptance Criteria

1. WHEN the new repository is created THEN it SHALL preserve the git history of moved files where technically feasible
2. WHEN viewing file history in the new repository THEN original author attribution SHALL be maintained
3. WHEN the migration is complete THEN a migration record SHALL be documented in both repositories
4. WHEN contributors check their contribution history THEN their work on examples SHALL remain visible

### Requirement 4

**User Story:** As a developer, I want the examples repository to have proper development setup and CI/CD, so that examples remain functional and tested.

#### Acceptance Criteria

1. WHEN the new repository is created THEN it SHALL include appropriate development setup instructions
2. WHEN code is pushed to the examples repository THEN automated testing SHALL verify examples still work
3. WHEN dependencies change in the main repository THEN the examples repository SHALL have a process to stay synchronized
4. WHEN viewing the examples repository THEN it SHALL include contribution guidelines specific to examples

### Requirement 5

**User Story:** As a user, I want seamless transition during the migration, so that I can continue accessing examples without disruption.

#### Acceptance Criteria

1. WHEN the migration occurs THEN existing bookmarks to examples SHALL redirect appropriately or show clear migration notices
2. WHEN the migration is announced THEN users SHALL receive adequate notice through appropriate channels
3. WHEN accessing old example links THEN they SHALL provide clear guidance on finding the new location
4. WHEN the migration is complete THEN the main repository SHALL include a migration notice in the changelog

### Requirement 6

**User Story:** As an engineer executing the migration, I want clear, real-time progress and status output, so that I can see where it is stuck, resume safely, and report accurate progress.

#### Acceptance Criteria

1. WHEN running the migration with default settings THEN the system SHALL print phase banners (prepare, migrate, integrate) and step-level messages with timestamps and elapsed time.
2. WHEN running with `--verbose` (and `-vv`) THEN the system SHALL include underlying git commands executed, per-repo status, and counts of files/commits processed.
3. WHEN running with `--debug` THEN the system SHALL include stack traces and environment details sufficient to triage failures.
4. WHEN running with `--json` THEN the system SHALL emit NDJSON events with fields: `timestamp`, `level`, `phase`, `step`, `repo`, `message`, `progress {current,total,pct}`, `duration_ms`, and optional `commit`.
5. WHEN provided `--status-file <path>` THEN the system SHALL persist a resumable checkpoint after each step and SHALL support `--resume` to continue from the last checkpoint without repeating completed steps.
6. WHEN running with `--dry-run` THEN the system SHALL simulate all steps and produce a clear "would perform" output without making changes.
7. WHEN no visible activity occurs for over 30 seconds THEN the system SHALL emit a heartbeat line indicating the last activity and current phase/step.
8. WHEN any step fails THEN the system SHALL exit non-zero and print a compact error summary including failed step, repo/context, last successful checkpoint, and remediation hint.
9. WHEN the migration completes THEN the system SHALL print a final summary table with steps, counts, durations, and success/fail; if `--json` is enabled it SHALL also write a summary event.