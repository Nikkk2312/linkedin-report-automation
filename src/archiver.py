"""
Archive and clean up old report files.

Moves reports older than a configurable number of days to an archive
directory, and optionally deletes very old archived reports to reclaim
disk space.
"""

import os
import shutil
import sys
import time


def archive_old_reports(output_dir='output', max_age_days=30,
                        archive_dir='output/archive', delete_after_days=90):
    """Move old report files to an archive folder and clean up stale archives.

    Scans output_dir for PPTX, PDF, JSON, and HTML report files. Files older
    than max_age_days are moved to archive_dir. Archived files older than
    delete_after_days are permanently deleted.

    Args:
        output_dir: Directory containing report files (default: 'output').
        max_age_days: Move files older than this many days (default: 30).
        archive_dir: Destination for archived files (default: 'output/archive').
        delete_after_days: Delete archived files older than this (default: 90).

    Returns:
        Dict with stats: {'archived': N, 'deleted': N, 'freed_mb': float,
                          'cleaned_dirs': N}.
    """
    stats = {
        'archived': 0,
        'deleted': 0,
        'freed_mb': 0.0,
        'cleaned_dirs': 0,
    }

    now = time.time()
    max_age_secs = max_age_days * 86400
    delete_age_secs = delete_after_days * 86400

    report_extensions = {'.pptx', '.pdf', '.json', '.html', '.htm'}

    # Ensure output directory exists
    if not os.path.isdir(output_dir):
        print(f"  Warning: Output directory not found: {output_dir}",
              file=sys.stderr)
        return stats

    # Create archive directory
    os.makedirs(archive_dir, exist_ok=True)

    # STEP 1: Archive old reports from output_dir
    for filename in os.listdir(output_dir):
        filepath = os.path.join(output_dir, filename)

        # Skip directories and the archive dir itself
        if not os.path.isfile(filepath):
            continue

        ext = os.path.splitext(filename)[1].lower()
        if ext not in report_extensions:
            continue

        file_age = now - os.path.getmtime(filepath)
        if file_age > max_age_secs:
            dest = os.path.join(archive_dir, filename)
            # Avoid overwriting: append timestamp if conflict
            if os.path.exists(dest):
                base, extension = os.path.splitext(filename)
                dest = os.path.join(
                    archive_dir,
                    f'{base}_{int(os.path.getmtime(filepath))}{extension}',
                )
            try:
                shutil.move(filepath, dest)
                stats['archived'] += 1
            except Exception as e:
                print(f"  Warning: Could not archive {filename}: {e}",
                      file=sys.stderr)

    # STEP 2: Delete very old archived files
    if os.path.isdir(archive_dir):
        for filename in os.listdir(archive_dir):
            filepath = os.path.join(archive_dir, filename)
            if not os.path.isfile(filepath):
                continue

            file_age = now - os.path.getmtime(filepath)
            if file_age > delete_age_secs:
                file_size = os.path.getsize(filepath)
                try:
                    os.remove(filepath)
                    stats['deleted'] += 1
                    stats['freed_mb'] += file_size / (1024 * 1024)
                except Exception as e:
                    print(f"  Warning: Could not delete {filename}: {e}",
                          file=sys.stderr)

    # STEP 3: Clean up empty demographic CSV subdirectories
    for entry in os.listdir(output_dir):
        dirpath = os.path.join(output_dir, entry)
        if not os.path.isdir(dirpath):
            continue
        if entry == 'archive':
            continue
        # Check if directory is empty or contains only empty subdirs
        try:
            contents = os.listdir(dirpath)
            if not contents:
                os.rmdir(dirpath)
                stats['cleaned_dirs'] += 1
        except Exception:
            pass

    stats['freed_mb'] = round(stats['freed_mb'], 2)

    if stats['archived'] or stats['deleted'] or stats['cleaned_dirs']:
        print(f"  Archiver: {stats['archived']} archived, "
              f"{stats['deleted']} deleted ({stats['freed_mb']} MB freed), "
              f"{stats['cleaned_dirs']} empty dirs removed.",
              file=sys.stderr)

    return stats
