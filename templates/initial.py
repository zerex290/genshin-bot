"""Service use only"""

import constants


class Initial:
    @staticmethod
    def _parts(picture: dict) -> dict:
        response = {
            'id': picture.get('id'),
            'favourites': picture.get('fav_count'),
            'resized_url': picture.get('large_file_url'),
            'original_url': picture.get('file_url'),
            'ext': picture.get('file_ext'),
            'date': str(picture.get('created_at'))[:str(picture.get('created_at')).find('T')],
            'general': picture.get('tag_string_general').split(),
            'characters': picture.get('tag_string_character').split(),
            'universes': picture.get('tag_string_copyright').split(),
            'artists': picture.get('tag_string_artist').split()
        }
        return response

    @staticmethod
    def primary_sorting(pictures: dict) -> dict:
        pictures = [
            Initial._parts(picture) for picture in pictures
            if (picture.get('id') and picture.get('fav_count', 0) >= 30
                and (picture.get('file_ext') == 'jpg' or picture.get('file_ext') == 'png'))
        ]
        fav_id = {picture['favourites']: picture['id'] for picture in pictures}

        try:
            return [picture for picture in pictures if picture['id'] == fav_id[max(fav_id)]][0]
        except IndexError:
            return {}

    @staticmethod
    def _tag_formatting(picture: dict) -> dict:
        symbols = constants.Uncategorized.SYMBOLS

        def formatting(tags: list) -> list:
            response_ = []
            for tag in tags:
                temp = tag
                for symbol in symbols:
                    temp = temp.replace(symbol, '')
                tag = temp.replace('-', '_')
                response_.append(tag)

            return response_

        response = {
            'characters': formatting(picture['characters']),
            'general': formatting(picture['general']),
            'universes': formatting(picture['universes']),
            'artists': formatting(picture['artists'])
        }
        return response

    @staticmethod
    def secondary_sorting(picture: dict, donut: bool) -> dict:
        picture = picture
        tags = Initial._tag_formatting(picture)
        picture['characters'] = tags['characters']
        picture['general'] = tags['general']
        picture['universes'] = tags['universes']
        picture['artists'] = tags['artists']

        if not donut and {'areola_slip', 'bdsm', 'lingerie'}.issubset(picture['general']):
            return {}
        elif donut and {'anus', 'penis'}.issubset(picture['general']):
            return {}
        else:
            return picture

    @staticmethod
    def _prettify_tags(characters: list, universes: list, artists: list, general: list, donut: bool):
        if not donut:
            characters = ', '.join([f"#{c[:c.find('_(')] if c.find('_(') >= 0 else c}@bot_genshin" for c in characters])
            universes = ', '.join([f"#{u[:u.find('_(')] if u.find('_(') != -1 else u}@bot_genshin" for u in universes])
            artists = ', '.join([f"#{a[:a.find('_(')] if a.find('_(') != -1 else a}@bot_genshin" for a in artists])
            general = ', '.join([f"#{t[:t.find('_(')] if t.find('_(') != -1 else t}@bot_genshin" for t in general])
        else:
            characters = ', '.join([f"{c[:c.find('_(')] if c.find('_(') != -1 else c}" for c in characters])
            universes = ', '.join([f"{u[:u.find('_(')] if u.find('_(') != -1 else u}" for u in universes])
            artists = ', '.join([f"{a[:a.find('_(')] if a.find('_(') != -1 else a}" for a in artists])
            general = '\n'.join([f"{t[:t.find('_(')] if t.find('_(') != -1 else t}" for t in general])

        response = {
            'characters': characters,
            'universes': universes,
            'artists': artists,
            'general': general
        }
        return response

    @staticmethod
    def _prettify_message(tags: dict, favourites: int, date: str, donut: bool) -> str:
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

    @staticmethod
    def get_message(picture: dict, donut: bool):
        tags = Initial._prettify_tags(
            picture['characters'], picture['universes'], picture['artists'], picture['general'], donut
        )
        return Initial._prettify_message(tags, picture['favourites'], picture['date'], donut)
