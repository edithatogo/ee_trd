def ensure_v3_output_dir(path):
    """Ensure output path is under nextgen_v3/out/ or orchestration/out_versions/."""
    if not (path.startswith('nextgen_v3/out/') or path.startswith('orchestration/out_versions/')):
        raise ValueError(f"Outputs must be under nextgen_v3/out/ or orchestration/out_versions/, got {path}")