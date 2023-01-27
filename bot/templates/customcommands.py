from datetime import datetime

from vkbottle_types.objects import UsersUserFull

from ..types.uncategorized import Month, IntMonth
from ..models.customcommands import CustomCommand


def format_information(command: CustomCommand, user: UsersUserFull) -> str:
    ddmmyy = (
        f"{Month[IntMonth(command.date_added.month).name].value} {command.date_added.day}, {command.date_added.year}"
    )
    formatted_information = (
        f"🖼Информация по команде '{command.name}':\n"
        f"🖌Создатель: {user.first_name} {user.last_name} [vk.com/{user.domain}]\n"
        f"🎉Дата создания: {ddmmyy}; {datetime.strftime(command.date_added, '%H:%M:%S')}\n"
        f"📞Количество использований: {command.times_used}\n"
        f"💬Текст команды: {'указан' if command.message else 'не указан'}\n"
        f"📷Изображения: {'прикреплены' if command.photo_id else 'не прикреплены'}\n"
        f"🎧Аудио: {'прикреплены' if command.audio_id else 'не прикреплены'}\n"
        f"📂Файлы: {'прикреплены' if command.document_id else 'не прикреплены'}"
    )
    return formatted_information
