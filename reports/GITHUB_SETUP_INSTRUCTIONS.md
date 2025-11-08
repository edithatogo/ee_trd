# GitHub Setup Instructions

Follow these steps to connect this repository to GitHub:

## 1. Create a New Repository on GitHub

1. Go to https://github.com/new
2. Choose a repository name (e.g., `trd-cea-toolkit`)
3. Add a description: "Health Economic Evaluation Toolkit for Treatment-Resistant Depression Interventions"
4. Select "Private" or "Public" depending on your preference
5. **DO NOT** initialize with a README, .gitignore, or license (we already have these)
6. Click "Create repository"

## 2. Link Your Local Repository to GitHub

After creating the repository on GitHub, copy and run these commands in your terminal:

```bash
cd "/Users/doughnut/Library/CloudStorage/GoogleDrive-d.a.mordaunt@gmail.com/My Drive/Project - EE - IV Ketamine vs ECT/trd_cea"

# Add the remote origin
git remote add origin https://github.com/[YOUR-USERNAME]/trd-cea-toolkit.git

# Verify the remote was added
git remote -v
```

Replace `[YOUR-USERNAME]/trd-cea-toolkit` with your actual GitHub username and chosen repository name.

## 3. Push the Initial Commit

```bash
# Push the main branch to GitHub
git branch -M main
git push -u origin main
```

## 4. Set Up GitHub Features (Optional)

After pushing, you can enable additional GitHub features:

1. Go to your repository's "Settings" tab
2. In the "Features" section, consider enabling:
   - Wikis
   - Issues
   - Projects
   - Discussions

3. In the "Options" section:
   - Enable "Automatically delete head branches"
   - Set up branch protection rules for main branch

## 5. Configure GitHub Actions (Already Set Up)

This repository already includes GitHub Actions workflows for:
- Testing on pushes and pull requests
- Code quality checks
- Security scanning
- Documentation generation

These will automatically run once pushed to GitHub.

## 6. Update Project Settings

Once on GitHub, consider configuring:

1. **Repository Topics**: Add topics like `health-economics`, `cost-effectiveness`, `psycadelic-research`, `mental-health`, `data-science`
2. **README**: The README has already been customized for GitHub
3. **Issues**: Templates are already configured in `.github/ISSUE_TEMPLATE`
4. **Pull Requests**: Template is already configured in `.github/PULL_REQUEST_TEMPLATE`

## 7. Additional Recommendations

- Consider setting up branch protection rules for the main branch
- Configure code review requirements
- Set up automated dependency updates
- Consider setting up a CODEOWNERS file for specific directories

## Troubleshooting

If you encounter issues with pushing, make sure:

1. You have proper permissions for the repository
2. You're using the correct SSH key or personal access token
3. Your local git configuration is correct

For authentication issues, you may need to generate a personal access token:
1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate a new token with appropriate permissions
3. Use the token instead of password when prompted