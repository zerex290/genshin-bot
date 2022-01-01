"""Service use only"""


class Initial:
    @staticmethod
    def parts(pic: dict) -> dict:
        response = {
            'id': pic.get('id'),
            'favourites': pic.get('fav_count'),
            'resized_url': pic.get('large_file_url'),
            'original_url': pic.get('file_url'),
            'ext': pic.get('file_ext'),
            'date': str(pic.get('created_at'))[:str(pic.get('created_at')).find('T')],
            'general': pic.get('tag_string_general').split(),
            'characters': pic.get('tag_string_character').split(),
            'universes': pic.get('tag_string_copyright').split(),
            'artists': pic.get('tag_string_artist').split()
        }
        return response

    @staticmethod
    def prettified_tags(characters: list, universes: list, artists: list, general: list, donut=False):
        if not donut:
            characters = ', '.join([f"#{c[:c.find('_(')] if c.find('_(') >= 0 else c}@bot_genshin" for c in characters])
            universes = ', '.join([f"#{uvs[:uvs.find('_(')] if uvs.find('_(') != -1 else uvs}" for uvs in universes])
            artists = ', '.join([f"#{ast[:ast.find('_(')] if ast.find('_(') != -1 else ast}" for ast in artists])
            general = ', '.join([f"#{t[:t.find('_(')] if t.find('_(') != -1 else t}@bot_genshin" for t in general])
        else:
            characters = ', '.join([f"{c[:c.find('_(')] if c.find('_(') != -1 else c}" for c in characters])
            universes = ', '.join([f"{uvs[:uvs.find('_(')] if uvs.find('_(') != -1 else uvs}" for uvs in universes])
            artists = ', '.join([f"{ast[:ast.find('_(')] if ast.find('_(') != -1 else ast}" for ast in artists])
            general = '\n'.join([f"{tag[:tag.find('_(')] if tag.find('_(') != -1 else tag}" for tag in general])

        response = {
            'characters': characters,
            'universes': universes,
            'artists': artists,
            'general': general
        }
        return response

    @staticmethod
    def message(tags: dict, favourites: int, date: str, donut=False) -> str:
        response = (
            f"{'#Art@bot_genshin' if not donut else 'Art'}\n"
            f"Вселенная: {tags['universes']}\n"
            f"Художники: {tags['artists']}\n"
            f"Персонажи: {tags['characters']}\n"
            f"Количество лайков на сайте: {favourites}💜\n"
            f"Дата публикации арта на сайте: {date}\n\n"
            f"{'Дополнительные теги:' if donut else ''}\n{tags['general'] if donut else ''}"
        )
        return response
