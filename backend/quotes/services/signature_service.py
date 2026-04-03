"""
Service de gestion des signatures électroniques pour les devis
"""
import base64
import binascii
import uuid
import logging
from typing import Dict, Tuple
from django.core.files.base import ContentFile
from django.utils import timezone
from ..utils.decorators import log_quote_action
from ..utils.validators import QuoteValidator
from ..utils.constants import (
    QuoteStatus,
    FileExtensions,
    ErrorMessages,
)
from config.utils import get_client_ip

logger = logging.getLogger(__name__)


class SignatureService:
    """Service pour gérer les signatures électroniques des devis"""

    @staticmethod
    @log_quote_action("Traitement de la signature électronique")
    def process_signature(quote, signature_data: Dict, request) -> Tuple[bool, str]:
        """
        Traite et enregistre la signature électronique d'un devis

        Args:
            quote: Instance du modèle Quote
            signature_data: Dictionnaire contenant les données de signature
            request: Objet request Django pour récupérer l'IP

        Returns:
            Tuple (success, message)

        Raises:
            ValueError: Si les données de validation sont invalides
            Exception: Si une erreur se produit lors du traitement
        """
        # Valider si le devis peut être signé
        can_sign, error_msg = QuoteValidator.can_sign_quote(quote)
        if not can_sign:
            raise ValueError(error_msg)

        # Valider les données de signature
        is_valid, error_msg = QuoteValidator.validate_signature_data(signature_data)
        if not is_valid:
            raise ValueError(error_msg)

        # Extraire les données
        signature = signature_data.get('signature', '').strip()
        signer_name = signature_data.get('signer_name', '').strip()

        # Décoder et sauvegarder l'image de signature
        try:
            decoded_image, file_ext = SignatureService._decode_signature_image(signature)
        except (ValueError, TypeError, binascii.Error) as e:
            logger.error(f"Erreur lors du décodage de la signature: {str(e)}")
            raise ValueError(ErrorMessages.SIGNATURE_INVALID)

        # Générer le nom de fichier
        signature_filename = f"signature_{quote.quote_number or quote.id}_{uuid.uuid4().hex[:8]}.{file_ext}"

        # Sauvegarder la signature et mettre à jour le devis
        quote.signature_image.save(
            signature_filename,
            ContentFile(decoded_image),
            save=False
        )
        quote.signer_name = signer_name
        quote.signed_at = timezone.now()
        quote.accepted_at = timezone.now()
        quote.status = QuoteStatus.ACCEPTED

        # Enregistrer l'IP du client
        quote.client_ip = get_client_ip(request)

        # Sauvegarder le devis
        quote.save()

        logger.info(f"Devis {quote.id} signé avec succès par {signer_name}")
        return True, "Devis signé avec succès"

    @staticmethod
    def _decode_signature_image(signature_data: str) -> Tuple[bytes, str]:
        """
        Décode une image de signature en base64

        Args:
            signature_data: Chaîne base64 de l'image

        Returns:
            Tuple (image_décodée, extension_fichier)

        Raises:
            ValueError: Si le format est invalide
            binascii.Error: Si le décodage base64 échoue
        """
        # Extraire le format et les données encodées
        if ';base64,' in signature_data:
            header, encoded = signature_data.split(';base64,', 1)
            file_ext = header.split('/')[-1].lower()
        else:
            encoded = signature_data
            file_ext = FileExtensions.SIGNATURE_DEFAULT

        # Décoder l'image
        decoded_image = base64.b64decode(encoded)

        # Valider et normaliser l'extension
        if file_ext not in FileExtensions.SIGNATURE_ALLOWED:
            file_ext = FileExtensions.SIGNATURE_DEFAULT

        return decoded_image, file_ext

