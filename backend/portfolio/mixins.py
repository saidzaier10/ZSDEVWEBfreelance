import logging
from .image_optimizer import optimize_image

logger = logging.getLogger(__name__)


class ImageOptimizationMixin:
    """
    Mixin to automatically optimize images before saving.
    Define `image_fields` in the model to specify which fields to optimize.
    Format: {'field_name': {'max_width': 1920, 'max_height': 1080, 'quality': 85}}
    """
    image_fields = {}

    def save(self, *args, **kwargs):
        for field_name, options in self.image_fields.items():
            field = getattr(self, field_name, None)
            if field and hasattr(field, 'file'):
                # Only optimize if it's a new upload or changed (basic check)
                # For more robust check, we'd need to compare with old instance
                try:
                    optimized = optimize_image(
                        field,
                        max_width=options.get('max_width', 1920),
                        max_height=options.get('max_height', 1080),
                        quality=options.get('quality', 85)
                    )
                    setattr(self, field_name, optimized)
                except Exception as e:
                    logger.warning("Could not optimize %s: %s", field_name, e)
        
        super().save(*args, **kwargs)
