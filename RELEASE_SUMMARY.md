# TRD CEA Toolkit - v0.1.1 Release Summary

## Repository Status
The repository has been successfully tidied and prepared for release:

- Base directory cleaned and organized
- Build artifacts removed from version control
- Version updated to 0.1.1
- Git tag v0.1.1 created and pushed to remote
- Release files organized in releases/ directory

## Release Structure
The v0.1.1 release includes:

1. `releases/v0.1.1/` directory with:
   - Built wheel distribution: `trd_cea_toolkit-0.1.1-py3-none-any.whl`
   - CITATION.cff for proper citation
   - LICENSE file
   - README.md with project overview
   - CHANGELOG.md with release history
   - RELEASE_NOTES.md with specific v0.1.1 information

## TestPyPI Upload Instructions

To upload to TestPyPI:

1. Install twine if not already installed:
   ```bash
   pip install twine build
   ```

2. Upload to TestPyPI:
   ```bash
   twine upload --repository testpypi dist/trd_cea_toolkit-0.1.1-py3-none-any.whl
   ```

3. Test installation from TestPyPI:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ trd-cea-toolkit==0.1.1
   ```

## GitHub Release
Version 0.1.1 has been tagged in the repository with git tag `v0.1.1`. The release can be accessed at:
https://github.com/edithatogo/ee_trd/releases/tag/v0.1.1

## Repository Organization
- `reports/` - Project reports and documentation
- `development/` - Development tools and configuration files  
- `archives/` - Backup and archive files
- `releases/` - Distribution packages for each release
- `analysis/`, `config/`, `data/`, `docs/`, `scripts/`, `src/`, `tests/` - Core project directories
- Base directory contains only essential project files

## License
The project is licensed under Apache 2.0 License.

## Citation
Dylan A Mordaunt (2025). TRD CEA Toolkit: Health Economic Evaluation Tools. 
Available at https://github.com/edithatogo/ee_trd