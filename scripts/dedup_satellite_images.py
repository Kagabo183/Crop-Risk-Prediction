#!/usr/bin/env python3
"""
Backup and deduplicate `satellite_images` by `file_path`.

What it does:
 - Creates a backup table `satellite_images_backup_YYYYMMDD_HHMMSS` with all rows
 - Finds groups with same `file_path` and more than one row
 - For each group: keeps the row with smallest `id`, merges `extra_metadata` JSON from others,
   updates the kept row, and deletes the duplicates

Run:
  python scripts/dedup_satellite_images.py

Requires DATABASE_URL env var (or supply via editing .env)
"""
from datetime import datetime
import json
import os
from sqlalchemy import create_engine, text


def merge_metadata(dicts):
    # simple merge: later dicts override earlier keys if not None
    result = {}
    for d in dicts:
        if not d:
            continue
        if isinstance(d, str):
            try:
                d = json.loads(d)
            except Exception:
                continue
        if not isinstance(d, dict):
            continue
        for k, v in d.items():
            # prefer existing if key exists and value is not None
            result[k] = v
    return result


def main():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise SystemExit('Set DATABASE_URL in environment before running')

    engine = create_engine(db_url)
    conn = engine.connect()
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_table = f'satellite_images_backup_{ts}'

    print('Creating backup table:', backup_table)
    conn.execute(text(f'CREATE TABLE {backup_table} AS TABLE satellite_images'))

    # find duplicates
    dup_q = text("SELECT file_path, array_agg(id ORDER BY id) AS ids, count(*) as cnt FROM satellite_images GROUP BY file_path HAVING count(*)>1")
    groups = conn.execute(dup_q).fetchall()
    print(f'Found {len(groups)} duplicate file_path groups')

    total_deleted = 0
    total_merged = 0

    for row in groups:
        file_path = row[0]
        ids = row[1]
        if not ids or len(ids) < 2:
            continue
        keep_id = ids[0]
        dup_ids = ids[1:]

        # load metadata for all rows
        rows = conn.execute(text('SELECT id, extra_metadata FROM satellite_images WHERE id = ANY(:ids)'), {'ids': ids}).fetchall()
        # order rows by id ascending
        rows_sorted = sorted(rows, key=lambda r: r[0])
        metas = [r[1] for r in rows_sorted]
        merged = merge_metadata(metas)

        # update kept row
        conn.execute(text('UPDATE satellite_images SET extra_metadata = :meta WHERE id = :id'), {'meta': json.dumps(merged), 'id': keep_id})
        total_merged += 1

        # delete duplicates
        conn.execute(text('DELETE FROM satellite_images WHERE id = ANY(:dup_ids)'), {'dup_ids': dup_ids})
        total_deleted += len(dup_ids)
        print(f'Kept id={keep_id} for {file_path}; deleted ids={dup_ids}')

    print(f'Done. merged_groups={total_merged} deleted_rows={total_deleted}. Backup table: {backup_table}')
    conn.close()


if __name__ == '__main__':
    main()
