from django.db import models


class InventoryItem(models.Model):
    ITEM_TYPES = [
        ('weapon',    'Weapon'),
        ('armor',     'Armor'),
        ('accessory', 'Accessory'),
    ]
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)
    item_name = models.CharField(max_length=150)
    added_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'inventory_items'
        unique_together = [['item_type', 'item_name']]
        ordering        = ['item_type', 'item_name']

    def __str__(self):
        return f"[{self.item_type}] {self.item_name}"