from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
import logging

from ..services.subscription_service import SubscriptionsService
from ..services.anime_service import anime_service

router = Router()
logger = logging.getLogger(__name__)
