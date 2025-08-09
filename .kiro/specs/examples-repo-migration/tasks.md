# Implementation Plan

- [ ] 1. Create new repository structure and configuration
  - Set up the new GitHub repository `meridian-runtime-examples` with proper settings
  - Create initial repository structure with directories and placeholder files
  - Configure repository permissions and branch protection rules
  - _Requirements: 1.1, 1.4_

- [x] 1.1 Create repository configuration files
  - Write pyproject.toml with project metadata and dependencies
  - Create requirements.txt for common example dependencies
  - Write comprehensive README.md for the examples repository
  - Create CONTRIBUTING.md with example-specific contribution guidelines
  - _Requirements: 1.4, 4.1, 4.3_

- [x] 1.2 Set up CI/CD pipeline configuration
  - Create .github/workflows/ci.yml for testing all examples
  - Write .github/workflows/sync-deps.yml for dependency synchronization
  - Create GitHub issue templates for example requests and bug reports
  - Write scripts/test_all_examples.py for comprehensive example testing
  - _Requirements: 4.1, 4.2_

- [ ] 2. Implement git history preservation migration
  - Create migration scripts using git subtree to preserve history
  - Write backup and rollback procedures for migration safety
  - Test migration process on a fork to validate history preservation
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 2.1 Create migration automation scripts
  - Write scripts/migrate_with_history.py to automate the git subtree migration
  - Implement validation functions to verify migration completeness
  - Create rollback procedures in case migration needs to be reverted
  - Write documentation for manual migration steps as backup
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 2.2 Execute content migration with history preservation
  - Run migration scripts to move examples/ directory with git history
  - Run migration scripts to move notebooks/ directory with git history
  - Validate that all files and commit history transferred correctly
  - Test that all examples still function in the new repository
  - _Requirements: 1.2, 1.3, 3.1, 3.2_

- [x] 3. Update main repository documentation and references
  - Update README.md to reference the new examples repository
  - Modify all documentation files in docs/ to point to new repository
  - Update mkdocs.yml navigation and links
  - Create migration notice for CHANGELOG.md
  - _Requirements: 2.1, 2.2, 2.3, 5.3_

- [x] 3.1 Update documentation file references systematically
  - Replace all examples/ path references in docs/examples/*.md files
  - Update docs/index.md example commands to reference new repository
  - Modify docs/guides/migration-extension.md references
  - Update any other documentation files that reference examples or notebooks
  - _Requirements: 2.1, 2.2_

- [ ] 3.2 Create user migration guidance
  - Write migration guide explaining the change to users
  - Create redirect notices for common example access patterns
  - Update contribution guidelines to direct example contributions to new repo
  - Add clear links and instructions in main repository README
  - _Requirements: 2.3, 5.1, 5.2, 5.4_

- [ ] 4. Implement dependency synchronization system
  - Create scripts/sync_dependencies.py to keep examples aligned with main repo
  - Write version compatibility checking and validation logic
  - Implement automated dependency update workflows
  - Create monitoring for breaking changes in main repository
  - _Requirements: 4.2, 4.3_

- [ ] 4.1 Create example metadata and validation system
  - Write scripts/validate_examples.py for example testing and validation
  - Create example metadata schema and validation functions
  - Implement automated testing for all examples against multiple Python versions
  - Write performance monitoring and resource usage tracking
  - _Requirements: 4.1, 4.2_

- [x] 5. Clean up main repository after migration
  - Remove examples/ directory from main repository
  - Remove notebooks/ directory from main repository
  - Update .gitignore and other configuration files as needed
  - Remove example-related CI/CD workflows from main repository
  - _Requirements: 1.5, 5.1_

- [ ] 5.1 Update main repository CI/CD configuration
  - Remove example testing from main repository CI workflows
  - Update GitHub Actions to exclude examples and notebooks directories
  - Modify any scripts or tools that reference the removed directories
  - Test that main repository CI/CD still functions correctly
  - _Requirements: 1.5, 4.1_

- [ ] 6. Test and validate complete migration
  - Execute comprehensive testing of all examples in new repository
  - Validate all documentation links work correctly
  - Test the dependency synchronization system
  - Verify git history and attribution are preserved
  - _Requirements: 2.1, 2.2, 3.1, 3.2, 4.1, 4.2_

- [ ] 6.1 Perform integration testing and user acceptance validation
  - Test example installation and execution flow from user perspective
  - Validate cross-repository references and navigation
  - Test contribution workflow for new examples
  - Gather community feedback and address any issues
  - _Requirements: 2.1, 2.2, 4.1, 5.4_

- [x] 8. Implement migration observability and status reporting
  - Add CLI flags: `--verbose/-v/-vv`, `--debug`, `--json`, `--status-file`, `--resume`, `--dry-run`
  - Implement `StatusReporter` with phase/step banners, timestamps, elapsed time, and heartbeat every 30s
  - Emit NDJSON events with required fields when `--json` is enabled
  - Persist checkpoints after each step to `--status-file`; support `--resume` to skip completed steps
  - Print compact error summary on failure with last checkpoint and remediation hint
  - Print final summary table with counts and durations
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9_

- [x] 8.1 Tests for observability and status reporting
  - Unit tests for `StatusReporter` formatting and NDJSON schema
  - Integration tests for `--dry-run`, `--json`, `--resume` flows
  - Watchdog test to ensure heartbeat is emitted during long operations
  - Snapshot tests for final summary table and error summaries
  - _Requirements: 6.1, 6.2, 6.4, 6.5, 6.7, 6.8, 6.9_

- [ ] 7. Deploy and announce migration completion
  - Make final repository public and announce to community
  - Update all external references and documentation
  - Monitor for issues and provide user support during transition
  - Document lessons learned and update migration procedures
  - _Requirements: 5.1, 5.2, 5.4_