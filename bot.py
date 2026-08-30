import inspect
import sys

# Исправление для Python 3.14
if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
from aiohttp import web
from vkbottle import Bot, Keyboard, KeyboardButtonColor, Text
from vkbottle.bot import Message
from vkbottle import BaseStateGroup

# ===== НАСТРОЙКИ =====
VK_TOKEN = "vk1.a.a_3dITwtsV9pQscXoUm1fgSpAtJDYBCaFkPZ30GRn4KqdpreBbX_9TP_e5oKJ7Kq5VSu_b1wKtNjcadpGDpN8AOxuipt34XEIvsW8KohkWGBO2Xtp7X5EK2H4e4ScGGWnRAWOx0726cjUYPWwtVX-wK_39mIA_nM0SCyvKhr6KgNbGZeqnTDp4ru_hSXj9jTeHkpBG1xPcYkNoanCMfY-g"
GROUP_ID = 240718452  # ID вашей группы
ADMIN_IDS = [111655732]  # ID администраторов (можно несколько)
VK_COMMUNITY_URL = "https://vk.com/club240718452"
STATS_FILE = "stats.json"
PORT = int(os.environ.get("PORT", 10000))

# ... остальной код без изменений ...
