from django.db import models


class CrawledMetaComment(models.Model):
    """Tracks crawler-owned comments without adding a visible source tag."""

    source = models.CharField(max_length=20)
    meta_id = models.BigIntegerField()
    position = models.PositiveIntegerField()
    comment_id = models.BigIntegerField(unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('source', 'meta_id', 'position'),
                name='unique_crawled_comment_position',
            ),
        ]
