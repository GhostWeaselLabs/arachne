# Design Document

## Overview

This design outlines the migration of the `examples/` and `notebooks/` directories from the main meridian-runtime repository to a new dedicated public repository called `meridian-runtime-examples`. The migration will preserve git history where possible, maintain proper attribution, and ensure seamless transition for users accessing examples and documentation.

The new repository will serve as a dedicated space for examples, tutorials, and interactive notebooks, allowing the main repository to focus on core runtime functionality while providing a collaborative environment for community-contributed examples.

## Architecture

### Repository Structure

The new `meridian-runtime-examples` repository will have the following structure:

```
meridian-runtime-examples/
├── README.md                    # Main repository documentation
├── CONTRIBUTING.md              # Example-specific contribution guidelines
├── requirements.txt             # Common dependencies for examples
├── pyproject.toml              # Project configuration and dependencies
├── .github/
│   ├── workflows/
│   │   ├── ci.yml              # CI pipeline for testing examples
│   │   └── sync-deps.yml       # Workflow to sync with main repo dependencies
│   └── ISSUE_TEMPLATE/         # Issue templates for example requests
├── examples/                   # Migrated from main repo
│   ├── __init__.py
│   ├── minimal_hello/
│   ├── hello_graph/
│   ├── sentiment/
│   ├── streaming_coalesce/
│   ├── pipeline_demo/
│   └── [other examples...]
├── notebooks/                  # Migrated from main repo
│   ├── README.md
│   ├── requirements.txt
│   ├── tutorials/
│   ├── examples/
│   └── research/
└── scripts/
    ├── test_all_examples.py    # Script to test all examples
    ├── sync_dependencies.py    # Script to sync with main repo
    └── validate_examples.py    # Validation utilities
```

### Migration Strategy

The migration will use a three-phase approach:

1. **Preparation Phase**: Create the new repository with proper structure and CI/CD
2. **Migration Phase**: Transfer files with history preservation using git subtree/filter-branch
3. **Integration Phase**: Update documentation and establish synchronization processes

### Git History Preservation

To preserve git history during migration, we will use `git subtree` or `git filter-branch` approach:

```bash
# Extract examples directory with history
git subtree push --prefix=examples origin examples-history

# Extract notebooks directory with history  
git subtree push --prefix=notebooks origin notebooks-history
```

This approach maintains commit history and author attribution for the migrated files.

## Components and Interfaces

### New Repository Components

#### 1. Repository Configuration
- **pyproject.toml**: Project metadata, dependencies, and tool configurations
- **requirements.txt**: Runtime dependencies for examples
- **README.md**: Comprehensive documentation for the examples repository

#### 2. CI/CD Pipeline
- **GitHub Actions Workflows**: 
  - Test all examples against multiple Python versions
  - Validate notebook execution
  - Dependency synchronization with main repository
  - Automated testing on pull requests

#### 3. Dependency Management
- **Sync Script**: Automated process to keep example dependencies aligned with main repository
- **Version Pinning**: Strategy for managing meridian-runtime version compatibility
- **Testing Matrix**: Support for testing against multiple meridian-runtime versions

#### 4. Documentation Integration
- **Cross-repository Links**: Stable URLs for linking from main repository documentation
- **Example Metadata**: Structured information about each example (difficulty, concepts, runtime)

### Main Repository Updates

#### 1. Documentation Updates
All documentation files will be updated to reference the new repository:

- `README.md`: Update quick start examples and references
- `docs/examples/*.md`: Update all example file paths and run commands
- `docs/index.md`: Update example commands and references
- `mkdocs.yml`: Update navigation and links

#### 2. Repository Cleanup
- Remove `examples/` directory after migration
- Remove `notebooks/` directory after migration  
- Update `.gitignore` if needed
- Update CI/CD workflows to remove example testing

#### 3. Migration Documentation
- Add migration notice to CHANGELOG.md
- Create migration guide for users
- Update contribution guidelines

## Data Models

### Example Metadata Schema

Each example will include metadata for better discoverability:

```yaml
# example-metadata.yml
name: "sentiment-analysis"
description: "Real-time text processing with control-plane preemption"
difficulty: "intermediate"
concepts:
  - "control-plane"
  - "backpressure"
  - "priorities"
runtime_minutes: 2
python_version: ">=3.11"
meridian_version: ">=1.0.0"
dependencies:
  - "textblob"
  - "numpy"
```

### Repository Synchronization Model

```python
# Synchronization configuration
class SyncConfig:
    main_repo: str = "GhostWeaselLabs/meridian-runtime"
    examples_repo: str = "GhostWeaselLabs/meridian-runtime-examples"
    sync_schedule: str = "daily"
    version_compatibility: Dict[str, str] = {
        "main": "latest",
        "v1.x": ">=1.0.0,<2.0.0"
    }
```

## Error Handling

### Migration Error Scenarios

1. **Git History Loss**: If subtree migration fails, fallback to manual copy with attribution documentation
2. **Broken Links**: Implement redirect strategy and comprehensive link validation
3. **Dependency Conflicts**: Version pinning strategy with compatibility matrix
4. **CI/CD Failures**: Graceful degradation with manual testing procedures

### Runtime Error Handling

1. **Example Failures**: Each example includes error handling and clear failure messages
2. **Dependency Issues**: Clear installation instructions and troubleshooting guides
3. **Version Incompatibility**: Automated testing against multiple meridian-runtime versions

## Testing Strategy

### Pre-Migration Testing

1. **Link Validation**: Automated testing of all documentation links
2. **Example Execution**: Verify all examples run successfully before migration
3. **Dependency Analysis**: Catalog all example dependencies

### Post-Migration Testing

1. **Automated CI/CD**: 
   - Test all examples on multiple Python versions (3.11, 3.12, 3.13)
   - Test against multiple meridian-runtime versions
   - Validate notebook execution
   - Link checking for documentation

2. **Integration Testing**:
   - Verify documentation links work correctly
   - Test example installation and execution flow
   - Validate cross-repository references

3. **User Acceptance Testing**:
   - Community feedback on migration
   - Documentation clarity and completeness
   - Example discoverability and usability

### Continuous Testing

1. **Scheduled Testing**: Daily runs against latest meridian-runtime
2. **Dependency Monitoring**: Automated alerts for dependency conflicts
3. **Performance Monitoring**: Track example execution times and resource usage

## Implementation Phases

### Phase 1: Repository Setup (Week 1)
- Create new GitHub repository `meridian-runtime-examples`
- Set up basic structure and CI/CD pipeline
- Configure repository settings and permissions
- Create initial documentation

### Phase 2: Content Migration (Week 2)
- Migrate examples/ directory with git history
- Migrate notebooks/ directory with git history
- Update example dependencies and configurations
- Test all examples in new repository

### Phase 3: Documentation Update (Week 3)
- Update all documentation references in main repository
- Create migration guides and announcements
- Update README and contribution guidelines
- Implement redirect strategies for old links

### Phase 4: Integration and Testing (Week 4)
- Set up dependency synchronization
- Comprehensive testing of all examples
- Community announcement and feedback collection
- Monitor and fix any issues

## Observability and Status Reporting

### CLI Interface
- Flags:
  - `--verbose` / `-v`, `-vv` for increasingly detailed logs
  - `--debug` for stack traces and environment details
  - `--json` to emit NDJSON events for each step
  - `--status-file <path>` to persist checkpoints; `--resume` to continue
  - `--dry-run` to simulate without changes

### Status Reporter
- Phases: `prepare`, `migrate`, `integrate`
- Events include: `timestamp`, `level`, `phase`, `step`, `message`, `repo`, `duration_ms`, `progress {current,total,pct}`, optional `commit`
- Heartbeat: emit every 30s without visible activity
- Final summary: table of steps, durations, counts, failures

### Checkpointing
- After each step, write checkpoint to status file with: phase, step, parameters, successful artifacts (e.g., branch names), and timestamps
- On `--resume`, skip completed steps and continue idempotently

### Error Handling Enhancements
- Compact error summary with failed step, hint, and last checkpoint reference
- Suggest `--debug` for details; include remediation link in docs

### Integration Points
- JSON events consumable by CI; log lines suitable for human operators
- Optional GitHub PR/issue comment hook (future task) to post summaries

## Synchronization Strategy

### Dependency Synchronization

The examples repository will maintain compatibility with the main repository through:

1. **Automated Dependency Updates**: Daily checks for meridian-runtime version updates
2. **Version Compatibility Matrix**: Support for multiple meridian-runtime versions
3. **Breaking Change Notifications**: Automated alerts when main repository has breaking changes

### Content Synchronization

1. **One-way Sync**: Examples repository is the source of truth for examples
2. **Contribution Flow**: New examples contributed to examples repository
3. **Documentation Updates**: Main repository documentation updated to reference examples repository

## Migration Communication Plan

### Pre-Migration (1 week before)
- Announcement in main repository README
- GitHub issue for community feedback
- Documentation of migration timeline

### During Migration (Migration week)
- Status updates on migration progress
- Temporary notices on affected documentation
- Support for users experiencing issues

### Post-Migration (1 week after)
- Migration completion announcement
- Updated documentation and guides
- Community feedback collection and response