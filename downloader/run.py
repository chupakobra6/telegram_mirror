import logging
from pathlib import Path
from typing import Iterable

import tomllib

# Support both `python -m downloader.run` and `python downloader/run.py`
try:
    from .service import download_videos  # type: ignore
except Exception:  # pragma: no cover - runtime import robustness
    import sys
    package_dir = Path(__file__).resolve().parent
    project_root = package_dir.parent  # telegram_mirror
    sys.path.insert(0, str(project_root))
    from downloader.service import download_videos  # type: ignore


logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def _read_config(config_path: Path) -> dict:
    with config_path.open("rb") as f:
        return tomllib.load(f)


def _read_links(path: Path) -> list[str]:
    if not path.exists():
        logger.info("links file not found, creating a template", extra={"path": str(path)})
        path.write_text("# Add your URLs here, one per line\n", encoding="utf-8")
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]


def main() -> None:
    _configure_logging()
    # When executed as a file, project_root is the parent of the package dir
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / "downloader" / "config.toml"

    cfg = _read_config(config_path)
    browser: str = cfg.get("browser", "chrome")
    browser_profile = cfg.get("browser_profile")
    output_root = Path(cfg.get("output_root", "rendered_messages/videos"))
    links_file = cfg.get("links_file", "downloader/links.txt")
    cookies_file_cfg = cfg.get("cookies_file")
    cookies_file = (
        Path(cookies_file_cfg)
        if cookies_file_cfg and Path(cookies_file_cfg).is_absolute()
        else (project_root / cookies_file_cfg) if cookies_file_cfg else None
    )

    links_path = (project_root / links_file) if not Path(links_file).is_absolute() else Path(links_file)
    urls: Iterable[str] = _read_links(links_path)

    if not urls:
        logger.info("No URLs to download. Add some to the links file.", extra={"links_file": str(links_path)})
        return

    logger.info(
        "Starting downloads",
        extra={
            "browser": browser,
            "profile": browser_profile,
            "output_root": str(output_root),
            "count": len(urls),
        },
    )
    download_videos(
        urls=urls,
        base_output_dir=output_root,
        browser=browser,
        browser_profile=browser_profile,
        cookies_file=cookies_file,
    )
    logger.info("All done")


if __name__ == "__main__":
    main()


