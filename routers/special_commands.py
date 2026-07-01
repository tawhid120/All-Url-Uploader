from __future__ import annotations

import logging
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, LinkPreviewOptions

from config import Settings
from services.download_history import DownloadHistoryManager
from utils import text
from utils.logging_config import safe_url_label

router = Router(name="special_commands")
logger = logging.getLogger(__name__)


@router.message(Command("cleanup"), F.chat.type == "private")
async def cleanup_command(message: Message, settings: Settings) -> None:
    """Delete all downloads except the last 2"""
    if not message.from_user:
        return
    
    user_id = message.from_user.id
    history_dir = settings.download_location / "history"
    history_manager = DownloadHistoryManager(history_dir)
    
    removed_count = history_manager.cleanup(user_id)
    
    if removed_count == 0:
        await message.answer(
            "📁 <b>Cleanup Result:</b>\n\n"
            "No downloads to cleanup (you have 2 or fewer).",
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
    else:
        await message.answer(
            f"✅ <b>Cleanup Complete!</b>\n\n"
            f"🗑️ Removed: <b>{removed_count}</b> old download(s)\n"
            f"📦 Kept: Last 2 downloads",
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
    
    logger.info("Cleanup executed | user=%s removed=%s", user_id, removed_count)


@router.message(Command("swaplast"), F.chat.type == "private")
asyncync def swaplast_command(message: Message, settings: Settings) -> None:
    """Re-download the last file in opposite format (video->audio or audio->video)"""
    if not message.from_user:
        return
    
    user_id = message.from_user.id
    history_dir = settings.download_location / "history"
    history_manager = DownloadHistoryManager(history_dir)
    
    last_download = history_manager.get_last_download(user_id)
    
    if not last_download:
        await message.answer(
            "❌ <b>No Download History</b>\n\n"
            "You haven't downloaded anything yet.",
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
        return
    
    # Determine opposite format
    opposite_format = None
    if last_download.send_type == "audio":
        opposite_format = "video"
    elif last_download.send_type == "video":
        opposite_format = "audio"
    else:
        await message.answer(
            "❌ <b>Cannot Swap Format</b>\n\n"
            f"Last download was a {last_download.send_type}, cannot convert.",
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
        return
    
    # Prepare re-download message
    await message.answer(
        f"🔄 <b>Re-downloading in {opposite_format.upper()} format...</b>\n\n"
        f"📄 File: <code>{last_download.file_name}</code>\n"
        f"🔗 Source: <code>{safe_url_label(last_download.source_url)}</code>",
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )
    
    # TODO: Implement actual re-download logic
    # For now, just notify the user
    logger.info(
        "Swaplast command | user=%s last_file=%s target_format=%s",
        user_id,
        last_download.file_name,
        opposite_format,
    )
