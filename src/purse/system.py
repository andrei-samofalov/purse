def get_start_cmd() -> str:
    """Return root process cmd string."""
    try:
        import psutil
    except ImportError:
        raise ImportError("psutil is not installed")

    process = psutil.Process()
    cmd = ' '.join(process.cmdline())
    return cmd
