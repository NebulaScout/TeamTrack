from django.db import models


class SeedRun(models.Model):
    name = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, default="running")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.status})"


class SeededObject(models.Model):
    seed_run = models.ForeignKey(
        "core.SeedRun", on_delete=models.CASCADE, related_name="seeded_objects"
    )
    model_label = models.CharField(max_length=100)  # e.g. "tasks.TaskModel"
    object_id = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("seed_run", "model_label", "object_id")
        indexes = [
            models.Index(fields=["seed_run", "model_label"]),
        ]

    def __str__(self):
        return f"{self.model_label}:{self.object_id} ({self.seed_run.name})"
