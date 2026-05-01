# Register all seeded data for each seed run
import os
from core.models import SeedRun, SeededObject


def get_active_seed_run():
    name = os.getenv("SEED_RUN_NAME")
    if not name:
        return None
    try:
        return SeedRun.objects.get(name=name)
    except SeedRun.DoesNotExist:
        return None


def record_seeded(seed_run, *objs):
    if not seed_run or not objs:
        return

    rows = []
    for obj in objs:
        if obj is None or getattr(obj, "pk", None) is None:
            continue
        rows.append(
            SeededObject(
                seed_run=seed_run,
                model_label=obj._meta.label,
                object_id=obj.pk,
            )
        )

    if rows:
        SeededObject.objects.bulk_create(rows, ignore_conflicts=True)
