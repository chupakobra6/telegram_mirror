import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Iterable, Optional, Tuple
from urllib.parse import urlparse

import yt_dlp
from yt_dlp.utils import DownloadError  # type: ignore

try:
    from playwright.async_api import async_playwright  # type: ignore
except Exception:  # pragma: no cover - Playwright is optional at runtime
    async_playwright = None  # type: ignore


logger = logging.getLogger(__name__)


def _partial_paths(final_path: Path) -> list[Path]:
    candidates: list[Path] = []
    try:
        # Common yt-dlp partial markers
        candidates.append(final_path.with_suffix(final_path.suffix + ".part"))
        candidates.append(final_path.with_suffix(final_path.suffix + ".ytdl"))
        # Some formats may use an intermediate container before merge
        candidates.append(final_path.with_suffix(".part"))
    except Exception:
        return []
    return candidates


def _remove_partials(final_path: Path) -> None:
    for p in _partial_paths(final_path):
        try:
            if p.exists():
                p.unlink(missing_ok=True)
        except Exception:
            continue


def _cleanup_artifacts(final_path: Path) -> None:
    """Remove leftover yt-dlp artifacts like '<final>.part-*' and '<final>.<ext>.ytdl'."""
    try:
        directory = final_path.parent
        prefix = final_path.name + ".part"
        for child in directory.iterdir():
            name = child.name
            if name == final_path.name:
                continue
            if name.startswith(prefix):
                try:
                    child.unlink(missing_ok=True)
                except Exception:
                    continue
        # Common sidecar file created by yt-dlp while downloading
        sidecar = final_path.with_suffix(final_path.suffix + ".ytdl")
        try:
            if sidecar.exists():
                sidecar.unlink(missing_ok=True)
        except Exception:
            pass
    except Exception:
        # Cleanup is best-effort; do not fail the whole run
        logger.exception("Artifacts cleanup failed")


def _sweep_leftovers(directory: Path) -> None:
    """Best-effort sweep: remove *.part* and *.ytdl files if their final file exists."""
    try:
        for child in directory.iterdir():
            name = child.name
            # Handle sidecar .ytdl
            if name.endswith(".ytdl"):
                base = name[:-5]
                if (directory / base).exists():
                    try:
                        child.unlink(missing_ok=True)
                    except Exception:
                        continue
                continue
            # Handle .part-based temp files
            if ".part" in name:
                base = name.split(".part", 1)[0]
                if (directory / base).exists():
                    try:
                        child.unlink(missing_ok=True)
                    except Exception:
                        continue
    except Exception:
        logger.exception("Leftovers sweep failed")


def _ensure_output_dir(base_dir: Path, url: str) -> Path:
    parsed = urlparse(url)
    domain = parsed.netloc or "unknown-domain"
    destination = base_dir / domain
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def _get_chrome_like_base(browser: str) -> Path | None:
    base: Path | None = None
    match sys.platform:
        case "darwin":
            match browser:
                case "chrome":
                    base = Path.home() / "Library/Application Support/Google/Chrome"
                case "brave":
                    base = Path.home() / "Library/Application Support/BraveSoftware/Brave-Browser"
                case "edge":
                    base = Path.home() / "Library/Application Support/Microsoft Edge"
                case "chromium":
                    base = Path.home() / "Library/Application Support/Chromium"
                case _:
                    base = None
        case "linux" | "linux2":
            match browser:
                case "chrome":
                    base = Path.home() / ".config/google-chrome"
                case "brave":
                    base = Path.home() / ".config/BraveSoftware/Brave-Browser"
                case "edge":
                    base = Path.home() / ".config/microsoft-edge"
                case "chromium":
                    base = Path.home() / ".config/chromium"
                case _:
                    base = None
        case _:
            base = None
    return base


def _map_display_name_to_profile_dir(base: Path, display_name: str) -> str | None:
    """Map Chrome display name (e.g., "Игорь") to directory name (e.g., "Profile 1")."""
    try:
        local_state_path = base / "Local State"
        if not local_state_path.exists():
            return None
        data = json.loads(local_state_path.read_text(encoding="utf-8"))
        info_cache = (data or {}).get("profile", {}).get("info_cache", {})
        target = display_name.strip().casefold()
        candidates_log: list[str] = []
        for dir_name, meta in info_cache.items():
            try:
                if not isinstance(meta, dict):
                    continue
                name = str(meta.get("name", "")).strip()
                gaia = str(meta.get("gaia_name", "")).strip()
                candidates_log.append(f"{dir_name} -> name='{name}', gaia='{gaia}'")
                if name and name.strip().casefold() == target:
                    return dir_name
                if gaia and gaia.strip().casefold() == target:
                    return dir_name
            except Exception:
                continue
        # Log available names to help user pick if mapping failed
        if candidates_log:
            logger.info("Available Chrome profiles", extra={"candidates": "; ".join(candidates_log)})
    except Exception:
        return None
    return None


def _get_display_name_for_dir(base: Path, dir_name: str) -> str | None:
    try:
        local_state_path = base / "Local State"
        if not local_state_path.exists():
            return None
        data = json.loads(local_state_path.read_text(encoding="utf-8"))
        info_cache = (data or {}).get("profile", {}).get("info_cache", {})
        meta = info_cache.get(dir_name)
        if isinstance(meta, dict):
            name = str(meta.get("name") or "").strip() or None
            if name:
                return name
            gaia = str(meta.get("gaia_name") or "").strip() or None
            return gaia
    except Exception:
        return None
    return None


def _find_profile_name(browser: str, requested_profile: str | None) -> str | None:
    base = _get_chrome_like_base(browser)
    if base is None:
        return requested_profile

    def _has_cookies(dir_name: str) -> bool:
        profile_dir = base / dir_name
        if not profile_dir.exists():
            return False
        # Chrome may store cookies under "Cookies" or "Network/Cookies"
        return (profile_dir / "Cookies").exists() or (profile_dir / "Network" / "Cookies").exists()

    # If requested is provided, try direct folder, then map display name via Local State
    if requested_profile:
        direct = base / requested_profile
        if _has_cookies(requested_profile):
            return requested_profile
        mapped = _map_display_name_to_profile_dir(base, requested_profile)
        if mapped and _has_cookies(mapped):
            return mapped

    # Fallback to common directories
    for candidate in ["Default", "Profile 1", "Profile 2", "Profile 3"]:
        if _has_cookies(candidate):
            return candidate
    return None


async def _capture_stream_with_playwright(
    page_url: str,
    browser: str,
    resolved_profile: str | None,
    force_system_chrome: bool,
    wait_timeout_sec: int = 45,
) -> Tuple[str, dict[str, str], Optional[str]] | None:
    """
    Launch installed Chrome/Edge profile via Playwright persistent context and capture
    first HLS/DASH manifest request (.m3u8/.mpd). Returns (manifest_url, request_headers).
    """
    if async_playwright is None:
        return None

    # Map our browser choice to Playwright channel and user data dir
    channel: str | None
    match browser:
        case "chrome":
            channel = "chrome"
        case "edge":
            channel = "msedge"
        case _:
            channel = None  # Fallback to bundled chromium if available (no OS profile)

    base = _get_chrome_like_base(browser)
    user_data_dir: Path | None = base if base and base.exists() else None

    # Use profile-directory flag when launching Chrome/Edge so the right profile is used
    launch_args: list[str] = []
    if resolved_profile:
        launch_args.append(f"--profile-directory={resolved_profile}")

    try:
        async with async_playwright() as p:  # type: ignore
            context = None
            if channel and user_data_dir is not None:
                try:
                    context = await p.chromium.launch_persistent_context(  # type: ignore
                        user_data_dir=str(user_data_dir),
                        channel=channel,
                        headless=False,
                        args=[
                            "--autoplay-policy=no-user-gesture-required",
                            *launch_args,
                        ],
                    )
                except Exception:
                    context = None

            if context is None and not force_system_chrome:
                # Fallback: bundled chromium without OS profile (may not be authenticated)
                context = await p.chromium.launch_persistent_context(  # type: ignore
                    user_data_dir=str(Path.cwd() / ".pw-temp-profile"),
                    headless=False,
                    args=["--autoplay-policy=no-user-gesture-required"],
                )
            elif context is None and force_system_chrome:
                # Respect user's choice to only use system Chrome
                return None

            page = await context.new_page()
            # Allow autoplay to trigger media requests
            try:
                await page.add_init_script("""
                    Object.defineProperty(document, 'visibilityState', {get: () => 'visible'});
                    Object.defineProperty(document, 'hidden', {get: () => false});
                """)
            except Exception:
                pass

            found: asyncio.Future[tuple[str, dict[str, str]]] = asyncio.get_event_loop().create_future()

            def _maybe_set(req_url: str, headers: dict[str, str]) -> None:
                try:
                    if any(s in req_url for s in [".m3u8", ".mpd", "format=m3u8"]):
                        if not found.done():
                            found.set_result((req_url, headers))
                except Exception:
                    pass

            page.on("request", lambda request: _maybe_set(request.url, request.headers))  # type: ignore
            
            async def on_response(response):  # type: ignore
                try:
                    url = response.url
                    ctype = (response.headers or {}).get("content-type", "")
                    if any(s in url for s in [".m3u8", ".mpd"]) or (
                        "mpegurl" in ctype or "dash+xml" in ctype
                    ):
                        # Responses don't expose request headers directly; use the matching request
                        req = response.request
                        _maybe_set(url, req.headers)
                except Exception:
                    pass

            page.on("response", on_response)  # type: ignore

            await page.goto(page_url, wait_until="domcontentloaded")
            # Capture a reasonable title for output filename
            page_title: Optional[str] = None
            try:
                page_title = await page.title()
            except Exception:
                page_title = None
            # Try to click on common video elements to start playback
            selectors = [
                "video",
                "jugru-video video",
                "button[aria-label='Воспроизвести']",
                "[data-testid='play'], .play, .video-play",
            ]
            for sel in selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        await el.click(timeout=2000)
                except Exception:
                    continue
            # Also try to programmatically play first <video>
            try:
                await page.evaluate("""
                    const v = document.querySelector('video');
                    if (v) { v.muted = true; v.play().catch(()=>{}); }
                """)
            except Exception:
                pass

            try:
                logger.info(
                    "Waiting for video manifest (you can sign in now)",
                    extra={"timeout_sec": wait_timeout_sec},
                )
                manifest_url, req_headers = await asyncio.wait_for(found, timeout=wait_timeout_sec)
                await context.close()
                return manifest_url, req_headers, page_title
            except asyncio.TimeoutError:
                await context.close()
                return None
    except Exception:
        logger.exception("Playwright capture failed")
        return None


def _build_ydl_opts(
    output_dir: Path,
    url: str,
    browser: str,
    browser_profile: str | None,
    cookies_file: Path | None,
) -> dict:
    # Use Referer/Origin headers for stricter CDNs
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    ydl_opts: dict = {
        "quiet": True,
        "no_warnings": True,
        # Keep filenames short; avoid embedding IDs or query strings
        "outtmpl": str(output_dir / "%(title).100B.%(ext)s"),
        "trim_file_name": 120,
        "outtmpl_na_placeholder": "NA",
        "writesubtitles": False,
        "writeinfojson": False,
        "writedescription": False,
        "writethumbnail": False,
        "restrictfilenames": False,
        "concurrent_fragment_downloads": 8,
        "continuedl": True,
        "ignoreerrors": False,
        "noprogress": False,
        "http_headers": {
            "Referer": url,
            "Origin": origin,
        },
        # Ensure final container is mp4 when possible
        "merge_output_format": "mp4",
        "postprocessors": [
            {"key": "FFmpegMetadata", "add_metadata": True},
        ],
        "postprocessor_args": ["-movflags", "+faststart"],
        "prefer_ffmpeg": True,
        # Do not overwrite completed files; we will explicitly resume/clean partials
        "overwrites": False,
    }

    # Cookies strategy: explicit cookies.txt wins; otherwise try detected browser profile
    if cookies_file is not None and cookies_file.exists():
        ydl_opts["cookiefile"] = str(cookies_file)
        logger.info(f"Using cookies.txt file: {cookies_file}")
    else:
        resolved_profile = _find_profile_name(browser, browser_profile)
        if resolved_profile is None:
            logger.info(f"Using browser cookies from default profile for {browser}")
            ydl_opts["cookiesfrombrowser"] = (browser, None, None, None)
        else:
            base = _get_chrome_like_base(browser)
            display = _get_display_name_for_dir(base, resolved_profile) if base else None
            if display:
                logger.info(
                    f"Using browser cookies from profile '{display}' → '{resolved_profile}' for {browser}",
                )
            else:
                logger.info(
                    f"Using browser cookies from profile '{resolved_profile}' for {browser}",
                )
            ydl_opts["cookiesfrombrowser"] = (browser, resolved_profile, None, None)
    return ydl_opts


def download_videos(
    urls: Iterable[str],
    base_output_dir: Path,
    browser: str = "chrome",
    browser_profile: str | None = None,
    cookies_file: Path | None = None,
) -> None:
    # Track per-domain progress and titles in the order of links
    domain_to_total: dict[str, int] = {}
    domain_to_success: dict[str, int] = {}
    domain_to_titles: dict[str, list[str]] = {}

    for raw_url in urls:
        url = raw_url.strip()
        if not url:
            continue

        try:
            destination = _ensure_output_dir(base_output_dir, url)
            parsed_for_domain = urlparse(url)
            domain = parsed_for_domain.netloc or "unknown-domain"
            domain_to_total[domain] = domain_to_total.get(domain, 0) + 1
            if domain not in domain_to_titles:
                domain_to_titles[domain] = []
            # Sweep any stale leftovers in destination before processing this URL
            _sweep_leftovers(destination)
            ydl_opts = _build_ydl_opts(
                destination,
                url,
                browser,
                browser_profile,
                cookies_file,
            )

            logger.info("Downloading video", extra={"url": url, "dest": str(destination)})

            last_output_path: Path | None = None
            expected_path: Path | None = None

            def _hook(d: dict) -> None:
                status = d.get("status")
                match status:
                    case "downloading":
                        fragment = d.get("fragment_index")
                        total = d.get("fragment_count")
                        speed = d.get("speed")
                        try:
                            name = d.get("filename")
                            if name:
                                nonlocal last_output_path
                                last_output_path = Path(str(name))
                        except Exception:
                            pass
                        if fragment and total:
                            logger.debug(
                                "progress", extra={"fragment": fragment, "total": total, "speed": speed}
                            )
                    case "finished":
                        # Avoid reserved LogRecord attributes like 'filename'
                        logger.info("Merging fragments", extra={"output_file": d.get("filename")})
                        try:
                            name = d.get("filename")
                            if name:
                                _cleanup_artifacts(Path(str(name)))
                        except Exception:
                            pass
                    case _:
                        return

            ydl_opts["progress_hooks"] = [_hook]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    # Pre-compute expected output file to support skip/resume
                    try:
                        probe_info = ydl.extract_info(url, download=False)
                        try:
                            expected_path = Path(ydl.prepare_filename(probe_info))
                            last_output_path = expected_path
                            # Skip if final file exists and no partial markers are present
                            has_partials = any(p.exists() for p in _partial_paths(expected_path))
                            if expected_path.exists() and not has_partials:
                                logger.info("Already downloaded, skipping", extra={"file": str(expected_path)})
                                _cleanup_artifacts(expected_path)
                                try:
                                    title_for_list = expected_path.stem
                                    domain_to_titles[domain].append(title_for_list)
                                    domain_to_success[domain] = domain_to_success.get(domain, 0) + 1
                                except Exception:
                                    pass
                                continue
                        except Exception:
                            pass
                    except DownloadError:
                        # Unsupported URL during probe will be handled by outer flow
                        pass

                    # Helper to download with one clean-retry if partials are corrupt
                    def _download_with_retry(target_url: str) -> None:
                        retry_cleaned = False
                        while True:
                            try:
                                ydl.extract_info(target_url, download=True)
                                return
                            except DownloadError as inner_e:
                                message_inner = str(inner_e)
                                # If we have a partial file, try to remove and retry once
                                has_partials = False
                                try:
                                    if last_output_path is not None:
                                        for p in _partial_paths(last_output_path):
                                            if p.exists():
                                                has_partials = True
                                                break
                                except Exception:
                                    has_partials = False
                                if has_partials and not retry_cleaned:
                                    logger.info(
                                        "Retrying after cleaning partial files",
                                        extra={"file": str(last_output_path) if last_output_path else None},
                                    )
                                    if last_output_path is not None:
                                        _remove_partials(last_output_path)
                                    retry_cleaned = True
                                    continue
                                raise

                    # Use extract_info with download=True so Unsupported URL raises DownloadError
                    _download_with_retry(url)
                    # Record title in link order on success
                    try:
                        final_for_title = last_output_path or expected_path
                        if final_for_title is not None:
                            domain_to_titles[domain].append(final_for_title.stem)
                            domain_to_success[domain] = domain_to_success.get(domain, 0) + 1
                    except Exception:
                        pass
                except DownloadError as e:
                    message = str(e)
                    if "Unsupported URL" in message or "does not pass URL" in message:
                        # Try Playwright fallback to capture manifest URL
                        resolved_profile = _find_profile_name(browser, browser_profile)
                        logger.info("Trying Playwright fallback to capture manifest URL")
                        result = asyncio.run(
                            _capture_stream_with_playwright(
                                url, browser, resolved_profile, force_system_chrome=False, wait_timeout_sec=45
                            )
                        )
                        if result is None:
                            raise
                        manifest_url, req_headers, page_title = result
                        # Merge captured auth headers (e.g., Authorization) with existing ones
                        headers = dict(ydl.params.get("http_headers", {}))  # type: ignore
                        for key in ("authorization", "Authorization"):
                            if key in req_headers:
                                headers["Authorization"] = req_headers[key]
                                break
                        # Some CDNs require Origin to match page origin; keep existing
                        ydl.params["http_headers"] = headers  # type: ignore
                        # If a title was captured from the page, use it to name the file
                        if page_title:
                            safe_title = page_title.replace("/", "-").replace("\\", "-").strip()
                            ydl.params["outtmpl"] = {"default": str(destination / f"{safe_title}.%(ext)s")}  # type: ignore
                            logger.info("Using page title for filename", extra={"title": safe_title})
                        # Re-probe to compute target filename for skip/resume after changing template
                        skip_due_to_existing = False
                        try:
                            probe_info2 = ydl.extract_info(manifest_url, download=False)
                            expected_path2 = Path(ydl.prepare_filename(probe_info2))
                            last_output_path = expected_path2
                            has_partials2 = any(p.exists() for p in _partial_paths(expected_path2))
                            if expected_path2.exists() and not has_partials2:
                                logger.info("Already downloaded, skipping", extra={"file": str(expected_path2)})
                                skip_due_to_existing = True
                                _cleanup_artifacts(expected_path2)
                        except DownloadError:
                            pass
                        if skip_due_to_existing:
                            # Go straight to next URL
                            try:
                                domain_to_titles[domain].append(expected_path2.stem)  # type: ignore[name-defined]
                                domain_to_success[domain] = domain_to_success.get(domain, 0) + 1
                            except Exception:
                                pass
                            continue
                        else:
                            logger.info(f"Retrying with captured manifest: {manifest_url}")
                            _download_with_retry(manifest_url)
                            try:
                                final_for_title2 = last_output_path or expected_path2  # type: ignore[name-defined]
                                if final_for_title2 is not None:
                                    domain_to_titles[domain].append(final_for_title2.stem)
                                    domain_to_success[domain] = domain_to_success.get(domain, 0) + 1
                            except Exception:
                                pass
                    else:
                        raise

        except Exception:
            logger.exception("Failed to download video")

    # After processing all URLs, emit per-domain titles file if all links for that domain succeeded
    try:
        for domain, total in domain_to_total.items():
            successes = domain_to_success.get(domain, 0)
            if total > 0 and successes == total:
                try:
                    out_dir = base_output_dir / domain
                    out_dir.mkdir(parents=True, exist_ok=True)
                    titles_path = out_dir / "titles.txt"
                    content = "\n".join(domain_to_titles.get(domain, [])) + "\n"
                    titles_path.write_text(content, encoding="utf-8")
                    logger.info(
                        "Wrote titles file",
                        extra={"domain": domain, "path": str(titles_path), "count": len(domain_to_titles.get(domain, []))},
                    )
                except Exception:
                    logger.exception("Failed to write titles file", extra={"domain": domain})
    except Exception:
        logger.exception("Post-processing of titles failed")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download authenticated videos with yt-dlp using your browser cookies. "
            "Outputs to rendered_messages/videos/<domain>/"
        )
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help=(
            "List of URLs and/or paths to text files with URLs (one per line). "
            "Files are detected by existing paths."
        ),
    )
    parser.add_argument(
        "--browser",
        default="chrome",
        choices=["chrome", "brave", "edge", "chromium", "safari"],
        help="Browser to read cookies from (must be logged in).",
    )
    parser.add_argument(
        "--browser-profile",
        default=None,
        help="Optional browser profile name (e.g. 'Default', 'Profile 1').",
    )
    parser.add_argument(
        "--output-root",
        default=str(Path("rendered_messages") / "videos"),
        help="Root output directory (default: rendered_messages/videos)",
    )
    return parser.parse_args(argv)


def _resolve_urls(inputs: list[str]) -> list[str]:
    urls: list[str] = []
    for item in inputs:
        path = Path(item)
        if path.exists() and path.is_file():
            urls.extend([line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()])
        else:
            urls.append(item)
    return urls


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def main(argv: list[str] | None = None) -> None:
    _configure_logging()
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    urls = _resolve_urls(args.inputs)
    base_dir = Path(args.output_root)
    download_videos(urls=urls, base_output_dir=base_dir, browser=args.browser, browser_profile=args.browser_profile)


if __name__ == "__main__":
    main()


