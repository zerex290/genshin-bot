import asyncio
import re
import os
import random
from typing import Dict, List, Optional, Tuple

import aiohttp
import aiofiles
from vkbottle import API

from lxml import html
from lxml.html import HtmlElement

from fake_useragent import UserAgent
from fake_useragent.errors import FakeUserAgentError

from bot.utils import json
from bot.utils.files import download, upload
from bot.src import templates as tpl, models as mdl
from bot.config.honeyimpact import URL, HEADERS, ATTRIBUTES
from bot.config.dependencies.paths import FILECACHE
from bot.src.types.uncategorized import Months
from bot.src.types.genshin import Characters, Elements, Weapons, Artifacts, Enemies


__all__ = (
    'CharacterParser',
    'WeaponParser',
    'ArtifactParser',
    'EnemyParser',
    'BookParser'
)


class HoneyImpactParser:
    def __init__(self, lang: str = 'RU') -> None:
        self.base_url = URL
        self.lang = lang

        self._headers = HEADERS
        self._attributes = ATTRIBUTES

    def _set_headers(self) -> Dict[str, str]:
        headers = self._headers.copy()
        try:
            useragent = UserAgent()
            headers['user_agent'] = useragent.random
        except FakeUserAgentError:
            pass
        return headers

    def _set_attributes(self) -> Dict[str, str]:
        attributes = self._attributes.copy()
        attributes['lang'] = self.lang
        return attributes

    async def _compile_html(self, page_url: str) -> HtmlElement:
        loop = asyncio.get_running_loop()
        async with aiohttp.ClientSession() as session:
            async with session.get(page_url, headers=self._set_headers(), params=self._set_attributes()) as query:
                if query.ok:
                    html_element = await query.text()
                    return await loop.run_in_executor(None, html.document_fromstring, html_element)
        return await loop.run_in_executor(None, html.document_fromstring, '<html></html>')

    @staticmethod
    async def _xpath(html_element: HtmlElement, query: str) -> List[HtmlElement]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, html_element.xpath, query)

    @staticmethod
    async def get_icon_attachment(api: API, url: str) -> Optional[str]:
        file = await download(url, FILECACHE, f"icon{random.randint(0, 10)}", 'png')
        if file:
            attachment = await upload(api, 'photo_messages', file)
            os.remove(file)
            return attachment
        return None


class CharacterParser(HoneyImpactParser):
    RELEASED = 'db/char/characters/'
    BETA = 'db/char/unreleased-and-upcoming-characters/'

    def __init__(self, lang: str = 'RU') -> None:
        super().__init__(lang)

    async def get_characters(self) -> Dict[str, dict]:
        characters = {e.value: {} for e in Elements}
        urls = (self.base_url + self.RELEASED, self.base_url + self.BETA)

        for url in urls:
            tree = await self._compile_html(url)
            table = await self._xpath(tree, '//div[@class="char_sea_cont"]//span[@class="sea_charname"]')
            for character in table:
                path = (await self._xpath(character, './..'))[0].items()[0][-1].rstrip(f"?lang={self.lang}")[1:]
                name = Characters[path.split('/')[-2].upper()].value
                element = await self._xpath(character, './../..//img[contains(@class, "element")]')
                element = element[0].items()[-1][-1].split('/')[-1].rstrip('_35.png').upper()
                characters[Elements[element].value][name] = path
        return characters

    async def get_information(self, name: str, element: str) -> str:
        tree = await self._compile_html(self.base_url + json.load('characters')[element][name])
        table = (await self._xpath(tree, '//div[@class="wrappercont"]//table[@class="item_main_table"][1]'))[0]

        ascension_stat = (await self._xpath(tree, '//div[@class="skilldmgwrapper"][preceding-sibling::span][1]'))[0]
        ascension_stat = (await self._xpath((await self._xpath(ascension_stat, './/tr'))[0], './td/text()'))[4]
        title = ''.join(await self._xpath(table, './/td[contains(text(), "Title")]/following-sibling::td/text()'))
        allegiance = await self._xpath(table, './/td[contains(text(), "Allegiance")]/following-sibling::td/text()')
        allegiance = ''.join(allegiance)
        rarity = len(await self._xpath(table, './/td[contains(text(), "Rarity")]/following-sibling::td/div'))
        weapon = (await self._xpath(table, './/td[contains(text(), "Weapon")]/following-sibling::td/a/text()'))[0]
        weapon = Weapons[weapon.upper()].value
        birthday = ''.join(await self._xpath(table, './/td[contains(text(), "Birthday")]/following-sibling::td/text()'))
        if len(birthday.split()) > 1:
            day, month = birthday.split()
            birthday = f"{Months[month.upper()].value} {day}"
        else:
            birthday = Months[birthday.upper().strip()].value
        a_name = ''.join(await self._xpath(table, './/td[contains(text(), "Astrolabe")]/following-sibling::td/text()'))

        desc = ''.join(await self._xpath(table, './/td[contains(text(), "Description")]/following-sibling::td/text()'))
        match name:
            case 'Итер':
                desc = re.sub(r'\{F#[а-яА-ЯёЁ\s]+}', '', desc)
                desc = re.sub(r'[{M#}]', '', desc)
            case 'Люмин':
                desc = re.sub(r'\{M#[а-яА-ЯёЁ\s]+}', '', desc)
                desc = re.sub(r'[{F#}]', '', desc)
            case _:
                pass

        character = mdl.honeyimpact.characters.Information(
            name, title, allegiance, rarity, weapon, element, ascension_stat, birthday, a_name, desc
        )
        return tpl.honeyimpact.Characters.format_information(character)

    async def get_active_skills(self, name: str, element: str) -> str:
        tree = await self._compile_html(self.base_url + json.load('characters')[element][name])
        table = (
            await self._xpath(
                tree,
                '//table[preceding-sibling::span[text()="Attack Talents"]]'
                '[following-sibling::span[contains(text(), "Talent Ascension Materials")]]'
            )
        )
        auto_attack = table[-4] if (len(table) % 4 == 0) else table[-3] if table else ''
        elemental_skill = table[-3] if (len(table) % 4 == 0) else table[-2] if table else ''
        alternative_sprint = table[-2] if (len(table) % 4 == 0 and table) else ''
        elemental_burst = table[-1] if table else ''
        if not isinstance(auto_attack, str):
            auto_attack_title = ''.join(await self._xpath(auto_attack, './/tr[1]/td[2]/a/text()'))
            auto_attack_desc = ''.join(await self._xpath(auto_attack, './/tr[2]//div//text()')).replace('•', '')
        else:
            auto_attack_title, auto_attack_desc = '', ''
        if not isinstance(elemental_skill, str):
            elemental_skill_title = ''.join(await self._xpath(elemental_skill, './/tr[1]/td[2]/a/text()'))
            elemental_skill_desc = ''.join(await self._xpath(elemental_skill, './/tr[2]//div//text()')).replace('•', '')
        else:
            elemental_skill_title, elemental_skill_desc = '', ''
        if not isinstance(alternative_sprint, str):
            alternative_sprint_title = ''.join(await self._xpath(alternative_sprint, './/tr[1]/td[2]/a/text()'))
            alternative_sprint_desc = ''.join(await self._xpath(alternative_sprint, './/tr[2]//div//text()'))
            alternative_sprint_desc = alternative_sprint_desc.replace('•', '')
        else:
            alternative_sprint_title, alternative_sprint_desc = '', ''
        if not isinstance(elemental_burst, str):
            elemental_burst_title = ''.join(await self._xpath(elemental_burst, './/tr[1]/td[2]/a/text()'))
            elemental_burst_desc = ''.join(await self._xpath(elemental_burst, './/tr[2]//div//text()')).replace('•', '')
        else:
            elemental_burst_title, elemental_burst_desc = '', ''

        auto_attack = mdl.honeyimpact.characters.Skill(auto_attack_title, auto_attack_desc)
        elemental_skill = mdl.honeyimpact.characters.Skill(elemental_skill_title, elemental_skill_desc)
        alternative_sprint = mdl.honeyimpact.characters.Skill(alternative_sprint_title, alternative_sprint_desc)
        elemental_burst = mdl.honeyimpact.characters.Skill(elemental_burst_title, elemental_burst_desc)

        response = tpl.honeyimpact.Characters.format_active_skills(
            auto_attack, elemental_skill, alternative_sprint, elemental_burst
        )
        return response

    async def get_passive_skills(self, name: str, element: str) -> str:
        tree = await self._compile_html(self.base_url + json.load('characters')[element][name])
        table = (
            await self._xpath(
                tree,
                '//div[@class="wrappercont"]//table[preceding-sibling::span[@id="beta_scroll_passive_talent"]]'
                '[following-sibling::span[@id="beta_scroll_constellation"]]/tr'
            )
        )
        first_passive_title = ''.join(await self._xpath(table[0], './/text()')) if table else ''
        first_passive_desc = ''.join(await self._xpath(table[1], './/text()')).replace('•', '') if table else ''
        second_passive_title = ''.join(await self._xpath(table[2], './/text()')) if table else ''
        second_passive_desc = ''.join(await self._xpath(table[3], './/text()')).replace('•', '') if table else ''
        third_passive_title = ''.join(await self._xpath(table[-2], './/text()')) if table else ''
        third_passive_desc = ''.join(await self._xpath(table[-1], './/text()')).replace('•', '') if table else ''

        first_passive = mdl.honeyimpact.characters.Skill(first_passive_title, first_passive_desc)
        second_passive = mdl.honeyimpact.characters.Skill(second_passive_title, second_passive_desc)
        third_passive = mdl.honeyimpact.characters.Skill(third_passive_title, third_passive_desc)

        response = tpl.honeyimpact.Characters.format_passive_skills(
            first_passive, second_passive, third_passive
        )
        return response

    async def get_constellations(self, name: str, element: str) -> str:
        tree = await self._compile_html(self.base_url + json.load('characters')[element][name])
        table = (
            await self._xpath(
                tree,
                '//div[@class="wrappercont"]//table[preceding-sibling::span[@id="beta_scroll_constellation"]]/tr'
            )
        )
        first_constellation_title = ''.join(await self._xpath(table[0], './/text()')) if table else ''
        first_constellation_desc = ''.join(await self._xpath(table[1], './/text()')) if table else ''
        second_constellation_title = ''.join(await self._xpath(table[2], './/text()')) if table else ''
        second_constellation_desc = ''.join(await self._xpath(table[3], './/text()')) if table else ''
        third_constellation_title = ''.join(await self._xpath(table[4], './/text()')) if table else ''
        third_constellation_desc = ''.join(await self._xpath(table[5], './/text()')) if table else ''
        fourth_constellation_title = ''.join(await self._xpath(table[6], './/text()')) if table else ''
        fourth_constellation_desc = ''.join(await self._xpath(table[7], './/text()')) if table else ''
        fifth_constellation_title = ''.join(await self._xpath(table[8], './/text()')) if table else ''
        fifth_constellation_desc = ''.join(await self._xpath(table[9], './/text()')) if table else ''
        sixth_constellation_title = ''.join(await self._xpath(table[10], './/text()')) if table else ''
        sixth_constellation_desc = ''.join(await self._xpath(table[11], './/text()')) if table else ''

        first_constellation = mdl.honeyimpact.characters.Skill(first_constellation_title, first_constellation_desc)
        second_constellation = mdl.honeyimpact.characters.Skill(second_constellation_title, second_constellation_desc)
        third_constellation = mdl.honeyimpact.characters.Skill(third_constellation_title, third_constellation_desc)
        fourth_constellation = mdl.honeyimpact.characters.Skill(fourth_constellation_title, fourth_constellation_desc)
        fifth_constellation = mdl.honeyimpact.characters.Skill(fifth_constellation_title, fifth_constellation_desc)
        sixth_constellation = mdl.honeyimpact.characters.Skill(sixth_constellation_title, sixth_constellation_desc)

        response = tpl.honeyimpact.Characters.format_constellations(
            first_constellation, second_constellation, third_constellation,
            fourth_constellation, fifth_constellation, sixth_constellation
        )
        return response


class WeaponParser(HoneyImpactParser):
    def __init__(self, lang: str = 'RU') -> None:
        super().__init__(lang)

    async def get_weapons(self) -> Dict[str, dict]:
        weapons = {w.value: {} for w in Weapons}

        for weapon_type in weapons:
            tree = (await self._compile_html(self.base_url + 'db/weapon/' + Weapons(weapon_type).name.lower()))
            table = (await self._xpath(tree, '//div[@class="scrollwrapper"]/table[@class="art_stat_table"]/tr//a'))
            for element in table:
                if await self._xpath(element, './text()'):
                    name = ''.join(await self._xpath(element, './text()'))
                    code = element.get('href').split('/')[3] if element.get('href').find('weapon') != -1 else ''
                    rarity = len(await self._xpath(element, '../following-sibling::td/div[contains(@class, "stars")]'))
                    weapons[weapon_type][name] = (code, rarity)
        return weapons

    async def get_information(self, name: str, weapon_type: str) -> str:
        code, rarity = json.load('weapons')[weapon_type][name]
        tree = await self._compile_html(self.base_url + 'weapon/' + code)
        table = (await self._xpath(tree, '//div[@class="wrappercont"]//table[@class="item_main_table"]'))
        match len(table):
            case 2:
                table = table[1]
            case 4:
                #: I hate Whiteblind and Prototype: Archaic
                #: They both have shitty table with Diluc passive skill
                #: https://genshin.honeyhunterworld.com/db/weapon/w_2309/?lang=EN
                table = table[2]
            case _:
                table = table[0]

        first_stat_title = 'Базовая атака'
        first_stat = (await self._xpath(table, './/td[text()="Base Attack"]/following-sibling::td/text()'))[0]
        second_stat_title = (await self._xpath(table, './/td[text()="Secondary Stat"]/following-sibling::td/text()'))[0]
        second_stat = (await self._xpath(table, './/td[text()="Secondary Stat Value"]/following-sibling::td/text()'))[0]

        desc = await self._xpath(
            table, './/tr/td[contains(text(), "In-game Description")]/following-sibling::td/text()'
        )
        desc = ''.join(desc)

        weapon = mdl.honeyimpact.weapons.Information(
            name, weapon_type, rarity, first_stat_title, first_stat, second_stat_title, second_stat, desc
        )
        return tpl.honeyimpact.Weapons.format_information(weapon)

    async def get_ability(self, name: str, weapon_type: str) -> str:
        tree = await self._compile_html(self.base_url + 'weapon/' + json.load('weapons')[weapon_type][name][0])
        table = (await self._xpath(tree, '//div[@class="wrappercont"]//table[@class="item_main_table"]'))[1]

        title = ''.join(
            await self._xpath(table, './/tr/td[text()="Special (passive) Ability"]/following-sibling::td/text()')
        )
        desc = ''.join(
            await self._xpath(table, './/tr/td[contains(text(), "Ability Desc")]/following-sibling::td//text()')
        )

        ability = mdl.honeyimpact.weapons.Ability(title, desc)
        return tpl.honeyimpact.Weapons.format_ability(ability)

    async def get_progression(self, name: str, weapon_type: str) -> str:
        tree = await self._compile_html(self.base_url + 'weapon/' + json.load('weapons')[weapon_type][name][0])
        table = await self._xpath(
            tree,
            '//table[@class="add_stat_table"][preceding-sibling::span[contains(text(), "Stat Progress")]]'
            '[following-sibling::span[contains(text(), "Refine")]]'
        )

        information: List[mdl.honeyimpact.weapons.ProgressionRow] = []
        second_stat = await self._xpath(
            tree,
            '//div[@class="wrappercont"]//td[text()="Secondary Stat"]/following-sibling::td/text()'
        )
        for row in await self._xpath(table[1], './tr[position()>1]'):
            information.append(
                mdl.honeyimpact.weapons.ProgressionRow(
                    (await self._xpath(row, './td[1]/text()'))[0],
                    'Атака',
                    (await self._xpath(row, './td[2]/text()'))[0],
                    second_stat[-1],
                    (await self._xpath(row, './td[3]/text()'))[0]
                )
            )
        progression = mdl.honeyimpact.weapons.Progression(information)
        return tpl.honeyimpact.Weapons.format_progression(progression)

    async def get_story(self, name: str, weapon_type: str) -> str:
        tree = await self._compile_html(self.base_url + 'weapon/' + json.load('weapons')[weapon_type][name][0])
        story = await self._xpath(
            tree,
            '//span[@class="item_secondary_title"][text()="Item Story"]/following-sibling::table//text()'
        )
        return tpl.honeyimpact.Weapons.format_story(''.join(story))


class ArtifactParser(HoneyImpactParser):
    def __init__(self, lang: str = 'RU') -> None:
        super().__init__(lang)

    async def get_artifacts(self) -> Dict[str, dict]:
        artifacts = {a.value: {} for a in Artifacts}
        tree = await self._compile_html(self.base_url + 'db/artifact/')
        tables = await self._xpath(tree, '//div[@class="wrappercont"]/table[contains(@class, "art_stat_table")]')

        for i, table in enumerate(tables):
            for row in await self._xpath(table, './tr[position()>1]'):
                if await self._xpath(row, './/a/text()'):
                    name = ''.join(await self._xpath(row, './/a//text()'))
                    code = (await self._xpath(row, './/a'))[0].items()[0][-1].split('/')[-2]
                    rarity = '-'.join(
                        [str(len(div)) for div in await self._xpath(row, './/div[@class="star_art_wrap_cont"]')]
                    )
                    icon = f"{self.base_url}{(await self._xpath(row, './/a//img'))[0].items()[-1][-1][1:-7]}.png"
                    artifacts[list(Artifacts)[i].value][name] = (code, rarity.strip(), icon)
        return artifacts

    async def get_information(self, name: str, artifact_type: str) -> str:
        code, rarity, _ = json.load('artifacts')[artifact_type][name]
        tree = await self._compile_html(self.base_url + 'db/art/family/' + code)
        table = (await self._xpath(tree, '//table[@class="item_main_table"]'))[0]

        piece2 = ''.join(await self._xpath(table, './tr/td[contains(text(), "2 Piece")]/following-sibling::td/text()'))
        piece4 = ''.join(await self._xpath(table, './tr/td[contains(text(), "4 Piece")]/following-sibling::td/text()'))

        artifact = mdl.honeyimpact.artifacts.Information(name, artifact_type, rarity, piece2, piece4)
        return tpl.honeyimpact.Artifacts.format_information(artifact)


class EnemyParser(HoneyImpactParser):
    def __init__(self, lang: str = 'RU') -> None:
        super().__init__(lang)

    async def get_enemies(self) -> Dict[str, dict]:
        enemies = {e.value: {} for e in Enemies}
        tree = await self._compile_html(self.base_url + 'db/enemy/')
        tables = await self._xpath(tree, '//div[contains(@class, "wrappercont_char")]/*')

        enemy_type = ''
        for item in tables[2:]:  #: First two items aren't necessary
            if item.get('class') == 'enemy_type':
                enemy_type = (''.join(await self._xpath(item, './text()'))).upper().replace(' ', '_')
            else:
                name = ''.join(await self._xpath(item, './a//text()'))
                code = (await self._xpath(item, './a'))[0].items()[0][-1].split('/')[-2]
                enemies[Enemies[enemy_type].value][name] = code
        return enemies

    async def get_information(self, name: str, enemy_type: str) -> str:
        tree = await self._compile_html(self.base_url + 'db/monster/' + json.load('enemies')[enemy_type][name])

        drop = await self._xpath(
            tree,
            '//table[@class="add_stat_table"][preceding-sibling::span[@class="item_secondary_title"]]'
        )
        drop = ', '.join(
            [''.join(await self._xpath(i, './/a//text()')) for i in await self._xpath(drop[0], './tr[position()>1]')]
        )
        desc = ''.join(await self._xpath(tree, '//table[@class="item_main_table"]/tr[last()]/td[last()]//text()'))

        enemy = mdl.honeyimpact.enemies.Information(name, enemy_type, drop, desc)
        return tpl.honeyimpact.Enemies.format_information(enemy)

    async def get_progression(self, name: str, enemy_type: str) -> str:
        tree = await self._compile_html(self.base_url + 'db/monster/' + json.load('enemies')[enemy_type][name])
        table = await self._xpath(tree, '//div[@class="scrollwrapper"]/table')
        stats = await self._xpath(table[0], './tr[position()>1]') if table else []

        information: List[mdl.honeyimpact.enemies.ProgressionRow] = []
        for stat in stats:
            information.append(
                mdl.honeyimpact.enemies.ProgressionRow(
                    (await self._xpath(stat, './td[1]/text()'))[0][2:],
                    (await self._xpath(stat, './td[2]/text()'))[0],
                    (await self._xpath(stat, './td[3]/text()'))[0],
                    (await self._xpath(stat, './td[4]/text()'))[0],
                    (await self._xpath(stat, './td[5]/text()'))[0],
                    (await self._xpath(stat, './td[6]/text()'))[0],
                    (await self._xpath(stat, './td[7]/text()'))[0],
                    (await self._xpath(stat, './td[8]/text()'))[0],
                    (await self._xpath(stat, './td[9]/text()'))[0],
                    (await self._xpath(stat, './td[10]/text()'))[0],
                    (await self._xpath(stat, './td[11]/text()'))[0],
                    (await self._xpath(stat, './td[12]/text()'))[0],
                    (await self._xpath(stat, './td[13]/text()'))[0]
                )
            )
        return tpl.honeyimpact.Enemies.format_progression(mdl.honeyimpact.enemies.Progression(information))


class BookParser(HoneyImpactParser):
    def __init__(self, lang: str = 'RU') -> None:
        super().__init__(lang)

    async def get_books(self) -> Dict[str, dict]:
        tree = await self._compile_html(self.base_url)
        table = await self._xpath(tree, '//div/span[text() = "Книги"]/../following-sibling::div[1]/a')

        books: Dict[str, dict] = {}
        for book in table:
            name = ''.join(await self._xpath(book, './/text()'))
            link = f"{self.base_url}{book.get('href').rstrip(f'?lang={self.lang}')[1:]}"
            books[name] = {}
            for i, volume in enumerate(
                    await self._xpath(await self._compile_html(link), '//div[@class="items_wrap"]//span/..')
            ):
                volume_link = f"{self.base_url}{volume.get('href').rstrip(f'?lang={self.lang}')[1:]}"
                volume_icon = f"{volume_link.replace('db/item', 'img/book').rstrip('/')}.png"
                books[name][f"Том {i + 1}"] = (volume_link, volume_icon)
        return books

    @staticmethod
    async def _get_book_txt(peer_id: int, api: API, text: str, name: str, volume: str) -> str:
        async with aiofiles.open(f"{FILECACHE}{os.sep}{name}-{volume}.txt", 'w') as book:
            await book.write(text)
        attachment = await upload(
            api,
            'document_messages',
            f"{name}: Том {volume}.txt", f"{FILECACHE}{os.sep}{name}-{volume}.txt",
            peer_id=peer_id
        )
        os.remove(f"{FILECACHE}{os.sep}{name}-{volume}.txt")
        return attachment

    async def get_information(self, peer_id: int, api: API, name: str, volume: str) -> Tuple[str, str]:
        tree = await self._compile_html(json.load('books')[name][f"{volume}"][0])

        story = await self._xpath(tree, '//span[text() = "Item Story"]/following-sibling::table//text()')
        if not story:
            story = await self._xpath(
                tree,
                '//div[@class="wrappercont"]//td[text() = "In-game Description"]/following-sibling::td//text()'
            )
        story = '\n'.join(story)
        volume = volume.split()[-1]
        doc = await self._get_book_txt(peer_id, api, story, name, volume)
        if (len(name) + len(volume) + len(story) + 63) >= 4096:  #: Vk message max len constraint
            story = 'Недоступно из-за превышения максимальной длины сообщения Вконтакте...'

        book = mdl.honeyimpact.books.Information(name, volume, story)
        return tpl.honeyimpact.Books.format_information(book), doc
