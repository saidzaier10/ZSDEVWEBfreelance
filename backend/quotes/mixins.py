"""
Mixins pour le modèle Quote.
Chaque mixin encapsule une responsabilité distincte pour respecter le SRP.
"""
import secrets
import string
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from .utils.constants import QuoteStatus, BillingType, PaymentConfig, QuoteConfig


class QuoteIdentifierMixin:
    """
    Génération automatique des identifiants uniques du devis :
    numéro de devis, token de signature, date d'expiration.
    """

    def generate_quote_number(self):
        """Génère un numéro unique au format DEVIS-YYYYMM-XXX (atomique)."""
        if not self.quote_number:
            date_part = timezone.now().strftime('%Y%m')
            prefix = f'{QuoteConfig.QUOTE_NUMBER_PREFIX}-{date_part}'
            with transaction.atomic():
                count = (
                    self.__class__.objects
                    .select_for_update()
                    .filter(quote_number__startswith=prefix)
                    .count() + 1
                )
                self.quote_number = f'{prefix}-{count:03d}'

    def generate_signature_token(self):
        """Génère un token sécurisé (cryptographique) pour la signature électronique."""
        if not self.signature_token:
            alphabet = string.ascii_letters + string.digits
            self.signature_token = ''.join(
                secrets.choice(alphabet) for _ in range(QuoteConfig.SIGNATURE_TOKEN_LENGTH)
            )

    def calculate_expiration_date(self):
        """Calcule la date d'expiration selon QuoteConfig.DEFAULT_EXPIRATION_DAYS."""
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=QuoteConfig.DEFAULT_EXPIRATION_DAYS)


class QuoteExpirationMixin:
    """Gestion de l'expiration des devis."""

    @property
    def is_expired(self):
        """True si la date d'expiration est dépassée."""
        return bool(self.expires_at and timezone.now() > self.expires_at)

    def check_if_expired(self):
        """Marque le devis comme expiré si nécessaire. Retourne True si l'état a changé."""
        if (
            self.expires_at
            and timezone.now() > self.expires_at
            and self.status in QuoteStatus.EXPIRABLE_STATUSES
        ):
            self.status = QuoteStatus.EXPIRED
            self.save(update_fields=['status'])
            return True
        return False


class QuotePricingMixin:
    """
    Calcul du prix du devis.
    Formule : (base + design) × complexité + options one_time → remise → TVA → TTC → paiements.
    """

    def calculate_prices(self, skip_m2m=False):
        """
        Calcule tous les montants du devis.

        Args:
            skip_m2m: Si True, ignore les options supplémentaires (M2M).
                      À utiliser lors de la création initiale avant que l'ID existe.

        Returns:
            dict avec les clés : subtotal_ht, discount_amount, subtotal_after_discount,
                                 tva_amount, total_ttc, payment_first, payment_second,
                                 payment_final, estimated_duration_days.
        """
        subtotal = Decimal('0.00')

        if self.project_type:
            subtotal = self.project_type.base_price

        if self.design_option:
            subtotal += self.design_option.price_supplement

        if self.complexity_level:
            subtotal *= self.complexity_level.price_multiplier

        if not skip_m2m and self.pk:
            for option in self.supplementary_options.filter(billing_type=BillingType.ONE_TIME):
                subtotal += option.price

        discount_amount = Decimal('0.00')
        if self.discount_value > 0:
            if self.discount_type == 'percent':
                discount_amount = subtotal * (self.discount_value / Decimal('100'))
            elif self.discount_type == 'fixed':
                discount_amount = self.discount_value

        subtotal_after_discount = subtotal - discount_amount
        tva_amount = subtotal_after_discount * (self.tva_rate / Decimal('100'))
        total_ttc = subtotal_after_discount + tva_amount

        payment_first = total_ttc * Decimal(str(PaymentConfig.FIRST_PAYMENT_PERCENT))
        payment_second = total_ttc * Decimal(str(PaymentConfig.SECOND_PAYMENT_PERCENT))
        payment_final = total_ttc * Decimal(str(PaymentConfig.FINAL_PAYMENT_PERCENT))

        estimated_days = self.project_type.estimated_days if self.project_type else 10
        if self.complexity_level:
            estimated_days = int(estimated_days * float(self.complexity_level.price_multiplier))

        return {
            'subtotal_ht': round(subtotal, 2),
            'discount_amount': round(discount_amount, 2),
            'subtotal_after_discount': round(subtotal_after_discount, 2),
            'tva_amount': round(tva_amount, 2),
            'total_ttc': round(total_ttc, 2),
            'payment_first': round(payment_first, 2),
            'payment_second': round(payment_second, 2),
            'payment_final': round(payment_final, 2),
            'estimated_duration_days': estimated_days,
        }
