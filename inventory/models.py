from django.db import models


class Item(models.Model):
    """The item list. Stored in data/inventory.sqlite3 and shared by sales and purchases."""
    company_id = models.PositiveIntegerField(db_index=True)
    name = models.CharField(max_length=200)
    hsn = models.CharField(max_length=8, blank=True)
    unit = models.CharField(max_length=10, blank=True)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    sale_rate = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    purchase_rate = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
