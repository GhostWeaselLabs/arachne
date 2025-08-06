# Meridian Runtime Docs Repository Setup

This guide explains how to set up the separate documentation repository for Meridian Runtime.

## Overview

The documentation is now deployed to a separate repository (`meridian-runtime-docs`) to keep the main source repository clean. The built site is automatically deployed via GitHub Actions.

## Setup Steps

### 1. Create the Docs Repository

Create a new repository called `meridian-runtime-docs` in the GhostWeaselLabs organization:

- **Repository name**: `meridian-runtime-docs`
- **Description**: "Documentation site for Meridian Runtime"
- **Visibility**: Public
- **Initialize with**: README (optional)

### 2. Configure GitHub Pages

In the `meridian-runtime-docs` repository:

1. Go to **Settings** → **Pages**
2. Set **Source** to "Deploy from a branch"
3. Set **Branch** to "main"
4. Set **Folder** to "/ (root)"
5. Click **Save**

### 3. Set Repository Permissions

The GitHub Actions workflow needs permission to push to the docs repository:

1. In the `meridian-runtime` repository, go to **Settings** → **Actions** → **General**
2. Under "Workflow permissions", ensure "Read and write permissions" is selected
3. Save the changes

### 4. Verify Deployment

After pushing changes to the main repository:

1. Check the GitHub Actions workflow in `meridian-runtime`
2. Verify the "Deploy to meridian-runtime-docs" job completes successfully
3. Visit `https://ghostweasellabs.github.io/meridian-runtime-docs/` to see the live site

## Repository Structure

```
meridian-runtime/           # Source code repository
├── docs/                   # Documentation source
├── mkdocs.yml             # MkDocs configuration
├── .github/workflows/     # CI/CD workflows
└── site/                  # Built site (ignored by git)

meridian-runtime-docs/      # Documentation site repository
├── index.html             # Built site files
├── assets/                # Static assets
└── ...                    # All other built files
```

## Benefits

- **Clean source repository**: No large `site/` directory in the main repo
- **Faster clones**: Source repository is much smaller
- **Separation of concerns**: Source code and built artifacts are separate
- **Better performance**: GitHub Pages serves from a dedicated repository
- **Easier maintenance**: Clear separation between source and output

## Troubleshooting

### Workflow Fails to Deploy

1. Check that the `meridian-runtime-docs` repository exists
2. Verify the GitHub token has write access to the docs repository
3. Ensure the workflow has the correct permissions

### Site Not Updating

1. Check the GitHub Actions workflow status
2. Verify the deployment job completed successfully
3. Wait a few minutes for GitHub Pages to update (can take 5-10 minutes)

### Local Development

To test locally without affecting the live site:

```bash
# Build the site locally
mkdocs build

# Serve locally for testing
mkdocs serve
```

The local `site/` directory will be created but is ignored by git.
