from datetime import datetime
from typing import Optional

from vkbottle_types.objects import UsersUserFull

from ..types.uncategorized import Month, IntMonth
from ..models.customcommands import CustomCommand


def format_information(command: CustomCommand, creator: UsersUserFull, editor: Optional[UsersUserFull] = None) -> str:
    if editor is not None:
        month = Month[IntMonth(command.date_edited.month).name].value
        ddmmyy = f"{month} {command.date_edited.day}, {command.date_edited.year}"
        edition_information = (
            f"📝Количество редактирований: {command.edits_num}\n"
            f"🗓Дата последнего редактирования: {ddmmyy}; {datetime.strftime(command.date_edited, '%H:%M:%S')}\n"
            f"👤Автор последнего редактирования: {editor.first_name} {editor.last_name} [vk.com/{editor.domain}]\n"
        )
    else:
        edition_information = ''

    month = Month[IntMonth(command.date_added.month).name].value
    ddmmyy = f"{month} {command.date_added.day}, {command.date_added.year}"
    formatted_information = (
        f"🖼Информация по команде '{command.name}':\n"
        f"🖌Создатель: {creator.first_name} {creator.last_name} [vk.com/{creator.domain}]\n"
        f"🎉Дата создания: {ddmmyy}; {datetime.strftime(command.date_added, '%H:%M:%S')}\n"
        f"📞Количество использований: {command.times_used}\n"
        f"{edition_information}"
        f"💬Текст команды: {'указан' if command.message else 'не указан'}\n"
        f"📷Изображения: {'прикреплены' if command.photo_id else 'не прикреплены'}\n"
        f"🎧Аудио: {'прикреплены' if command.audio_id else 'не прикреплены'}\n"
        f"📂Файлы: {'прикреплены' if command.document_id else 'не прикреплены'}"
    )
    return formatted_information
