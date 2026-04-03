"""
Service principal de gestion des devis
Orchestration des différents services (PDF, Email, Signature)
"""
import logging
from typing import Dict, Optional
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Sum, Avg
from django.db.models.functions import TruncMonth
from datetime import timedelta
from .pdf_service import PDFService
from .email_service import EmailService
from .signature_service import SignatureService
from ..utils.decorators import log_quote_action
from ..utils.validators import QuoteValidator
from ..utils.constants import (
    QuoteStatus,
    EmailType,
    ErrorMessages,
    SuccessMessages,
)

logger = logging.getLogger(__name__)


class QuoteService:
    """Service principal pour gérer toutes les opérations sur les devis"""

    @staticmethod
    @log_quote_action("Création complète d'un devis")
    @transaction.atomic
    def create_quote(quote) -> bool:
        """
        Crée un devis complet: génération PDF + envoi email

        Args:
            quote: Instance du modèle Quote (déjà sauvegardée)

        Returns:
            True si la création complète a réussi

        Raises:
            Exception: Si une étape critique échoue
        """
        # 1. Générer le PDF
        try:
            PDFService.generate_and_save_pdf(quote)
        except Exception as e:
            logger.error(f"La génération du PDF a échoué pour le devis {quote.id}: {str(e)}")
            # On continue même si le PDF échoue, il pourra être régénéré plus tard

        # 2. Envoyer l'email avec mise à jour du statut
        try:
            EmailService.send_email_with_status_update(quote, EmailType.CREATED)
        except Exception as e:
            logger.error(f"L'envoi de l'email a échoué pour le devis {quote.id}: {str(e)}")
            # On continue, le devis est créé même sans email

        logger.info(f"Devis {quote.id} créé avec succès")
        return True

    @staticmethod
    @log_quote_action("Mise à jour du statut du devis")
    def update_quote_status(quote, new_status: str, **extra_fields) -> bool:
        """
        Met à jour le statut d'un devis avec des champs additionnels

        Args:
            quote: Instance du modèle Quote
            new_status: Nouveau statut
            **extra_fields: Champs additionnels à mettre à jour

        Returns:
            True si la mise à jour a réussi
        """
        update_fields = ['status']

        quote.status = new_status

        # Gérer les champs de timestamp selon le statut
        if new_status == QuoteStatus.SENT and not quote.sent_at:
            quote.sent_at = timezone.now()
            update_fields.append('sent_at')

        elif new_status == QuoteStatus.VIEWED and not quote.viewed_at:
            quote.viewed_at = timezone.now()
            update_fields.append('viewed_at')

        elif new_status == QuoteStatus.ACCEPTED and not quote.accepted_at:
            quote.accepted_at = timezone.now()
            update_fields.append('accepted_at')

        elif new_status == QuoteStatus.REJECTED and not quote.rejected_at:
            quote.rejected_at = timezone.now()
            update_fields.append('rejected_at')

        # Ajouter les champs supplémentaires
        for field, value in extra_fields.items():
            setattr(quote, field, value)
            if field not in update_fields:
                update_fields.append(field)

        quote.save(update_fields=update_fields)
        logger.info(f"Statut du devis {quote.id} mis à jour: {new_status}")
        return True

    @staticmethod
    @log_quote_action("Signature du devis")
    @transaction.atomic
    def sign_quote(quote, signature_data: Dict, request) -> Dict:
        """
        Traite la signature complète d'un devis

        Args:
            quote: Instance du modèle Quote
            signature_data: Dictionnaire avec signature, signer_name, terms_accepted
            request: Objet request Django

        Returns:
            Dictionnaire avec success et message

        Raises:
            ValueError: Si la validation échoue
            Exception: Si une erreur se produit
        """
        # Traiter la signature (validation + sauvegarde)
        success, message = SignatureService.process_signature(quote, signature_data, request)

        if not success:
            raise ValueError(message)

        # Envoyer l'email d'acceptation (non-bloquant)
        try:
            EmailService.send_accepted_email(quote)
        except Exception as e:
            logger.warning(f"L'email d'acceptation n'a pas pu être envoyé: {str(e)}")
            # On ne bloque pas le processus de signature pour un problème d'email

        return {
            'success': True,
            'message': SuccessMessages.QUOTE_SIGNED
        }

    @staticmethod
    @log_quote_action("Refus du devis")
    @transaction.atomic
    def reject_quote(quote, rejection_data: Optional[Dict] = None) -> Dict:
        """
        Traite le refus d'un devis

        Args:
            quote: Instance du modèle Quote
            rejection_data: Données optionnelles (raison du refus, etc.)

        Returns:
            Dictionnaire avec success et message

        Raises:
            ValueError: Si le devis ne peut pas être rejeté
        """
        # Valider si le devis peut être rejeté
        can_reject, error_msg = QuoteValidator.can_reject_quote(quote)
        if not can_reject:
            raise ValueError(error_msg)

        # Mettre à jour le statut
        QuoteService.update_quote_status(quote, QuoteStatus.REJECTED)

        # Enregistrer la raison si fournie
        if rejection_data and 'rejection_reason' in rejection_data:
            quote.rejection_reason = rejection_data['rejection_reason']
            quote.save(update_fields=['rejection_reason'])

        # Envoyer l'email de refus (non-bloquant)
        try:
            EmailService.send_rejected_email(quote)
        except Exception as e:
            logger.warning(f"L'email de refus n'a pas pu être envoyé: {str(e)}")

        return {
            'success': True,
            'message': SuccessMessages.QUOTE_REJECTED
        }

    @staticmethod
    @log_quote_action("Envoi/renvoi du devis par email")
    def send_quote(quote) -> Dict:
        """
        Envoie ou renvoie un devis par email

        Args:
            quote: Instance du modèle Quote

        Returns:
            Dictionnaire avec success et message

        Raises:
            ValueError: Si le devis ne peut pas être envoyé
        """
        # Valider si le devis peut être envoyé
        can_resend, error_msg = QuoteValidator.can_resend_quote(quote)
        if not can_resend:
            raise ValueError(error_msg)

        # Régénérer le PDF si nécessaire
        if not quote.pdf_file:
            try:
                PDFService.generate_and_save_pdf(quote)
            except Exception as e:
                logger.error(f"Impossible de générer le PDF: {str(e)}")
                raise Exception(ErrorMessages.PDF_GENERATION_ERROR)

        # Envoyer l'email avec mise à jour du statut
        EmailService.send_email_with_status_update(quote, EmailType.CREATED)

        return {
            'success': True,
            'message': SuccessMessages.QUOTE_SENT
        }

    @staticmethod
    @log_quote_action("Duplication du devis")
    @transaction.atomic
    def duplicate_quote(quote, user) -> 'Quote':
        """
        Duplique un devis existant

        Args:
            quote: Instance du modèle Quote à dupliquer
            user: Utilisateur qui crée la duplication

        Returns:
            Nouvelle instance de Quote
        """
        from ..models import Quote

        # Copier les champs principaux
        new_quote = Quote(
            created_by=user,
            client_name=quote.client_name,
            client_email=quote.client_email,
            client_phone=quote.client_phone,
            client_address=quote.client_address,
            # project_name removed as it is not a field on Quote
            project_description=quote.project_description,
            # project_category removed as it is not a field on Quote
            project_type=quote.project_type,
            design_option=quote.design_option,
            complexity_level=quote.complexity_level,
            # base_price, design_option_price, complexity_price removed as they are not fields
            discount_type=quote.discount_type,
            discount_value=quote.discount_value,
            discount_reason=quote.discount_reason,
            tva_rate=quote.tva_rate,
            # project_duration_weeks removed, mapped to estimated_duration_days
            estimated_duration_days=quote.estimated_duration_days,
            # payment percents removed as they are not fields
            internal_notes=quote.internal_notes,
            status=QuoteStatus.DRAFT,
        )

        new_quote.save()

        # Copier les options supplémentaires
        new_quote.supplementary_options.set(quote.supplementary_options.all())

        # Recalculer les prix et appliquer les valeurs calculées au modèle
        prices = new_quote.calculate_prices()
        for field, value in prices.items():
            setattr(new_quote, field, value)
        new_quote.save()

        logger.info(f"Devis {quote.id} dupliqué vers nouveau devis {new_quote.id}")
        return new_quote

    @staticmethod
    @log_quote_action("Marquage du devis comme consulté")
    def mark_as_viewed(quote) -> bool:
        """
        Marque un devis comme consulté

        Args:
            quote: Instance du modèle Quote

        Returns:
            True si la mise à jour a été effectuée
        """
        if not quote.viewed_at:
            quote.viewed_at = timezone.now()

            # Passer de 'sent' à 'viewed' si nécessaire
            if quote.status == QuoteStatus.SENT:
                QuoteService.update_quote_status(quote, QuoteStatus.VIEWED)
            else:
                quote.save(update_fields=['viewed_at'])

            logger.info(f"Devis {quote.id} marqué comme consulté")
            return True

        return False

    @staticmethod
    def get_statistics() -> Dict:
        """
        Calcule les statistiques globales des devis.

        Returns:
            Dictionnaire avec total_quotes, total_amount, average_amount,
            status_breakdown, conversion_rate, quotes_by_month, top_project_types.
        """
        from ..models import Quote

        aggregates = Quote.objects.aggregate(
            total_amount=Sum('total_ttc'),
            average_amount=Avg('total_ttc'),
        )

        status_breakdown = dict(
            Quote.objects.values('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        )

        sent_count = Quote.objects.filter(status__in=['sent', 'viewed', 'accepted']).count()
        accepted_count = Quote.objects.filter(status='accepted').count()
        conversion_rate = (accepted_count / sent_count * 100) if sent_count > 0 else 0

        twelve_months_ago = timezone.now() - timedelta(days=365)
        quotes_by_month = list(
            Quote.objects.filter(created_at__gte=twelve_months_ago)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'), total=Sum('total_ttc'))
            .order_by('month')
        )

        top_project_types = list(
            Quote.objects.values('project_type__name')
            .annotate(count=Count('id'), total_amount=Sum('total_ttc'))
            .order_by('-count')[:5]
        )

        return {
            'total_quotes': Quote.objects.count(),
            'total_amount': aggregates['total_amount'] or 0,
            'average_amount': aggregates['average_amount'] or 0,
            'status_breakdown': status_breakdown,
            'conversion_rate': round(conversion_rate, 2),
            'quotes_by_month': quotes_by_month,
            'top_project_types': top_project_types,
        }
