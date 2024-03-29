from __future__ import annotations
import asyncio
import re
import os
from typing import Optional, List, Union, Dict

import aiohttp
import aiofiles

from lxml import html
from lxml.html import HtmlElement
from lxml.etree import ParserError

from ..utils import json, catch_aiohttp_errors
from ..config import honeyimpact
from ..config.dependencies.paths import FILECACHE
from ..models import honeyimpact as mdl
from ..types.uncategorized import Month, IntMonth, Weekday, IntWeekday
from ..types.genshin import Character, Element, Region, WeaponType, Stat, EnemyType, Grade, DomainType


__all__ = (
    'CharacterParser',
    'WeaponParser',
    'ArtifactParser',
    'EnemyParser',
    'BookParser',
    'DomainParser',
    'DailyFarmParser',
    'TalentBookParser',
    'BossMaterialParser'
)


class _AsyncHtmlElement:
    def __init__(self, _element: HtmlElement) -> None:
        super().__init__()
        self._element = _element

    def __str__(self) -> str:
        return str(self._element)

    def __repr__(self) -> str:
        return repr(self._element)

    def __getattr__(self, attr):
        return getattr(self._element, attr)

    async def xpath(self, expr: str, *args) -> List[Union[_AsyncHtmlElement, str, float, int]]:
        loop = asyncio.get_running_loop()
        if self._element is not None:
            return [
                _AsyncHtmlElement(e) if isinstance(e, HtmlElement) else e
                for e in await loop.run_in_executor(None, self._element.xpath, expr, *args)
            ]
        else:
            return []

    async def text(self, sep: str = '') -> str:
        """Returns text inside the current element.

        :param sep: custom separator between text parts
        :return: Str representation of text
        """
        return sep.join(await self.xpath('.//text()')).strip()

    async def position(self) -> Optional[int]:
        """Returns current element position within the parent.
        Element indexing starts with 1 according to html document structure.

        :return: Int with element position
        """
        loop = asyncio.get_running_loop()
        try:
            parent = await loop.run_in_executor(None, self._element.getparent)
            return (await loop.run_in_executor(None, parent.index, self._element)) + 1
        except ValueError:
            return None


class CharacterParser:
    def __init__(self, element: str, name: str) -> None:
        self._data = json.load('characters')[element][name]
        self.element = element
        self.name = name
        self.href: str = self._data[0]
        self.icon: str = self._data[1]
        self.rarity: int = self._data[2]
        self.weapon: str = self._data[3]
        del self._data

    @classmethod
    async def get_characters(cls) -> Optional[Dict[str, dict]]:
        characters = {e.value: {} for e in Element}

        for endpoint in _ENDPOINTS[cls.__name__]:
            tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + endpoint)
            if tree is None:
                return None
            table = await _deserialize(
                (await tree.xpath('//section[@id="characters"]//script/text()'))[0],
                'sortable_data'
            )
            for character in table:
                _, name, rarity, weapon, element, _ = character
                href = re.search(r'\w+', (await name.xpath('//@href'))[0])[0]
                icon = f"{honeyimpact.URL}img/{href}.webp"
                name = Character[href.split('_')[0].upper()].value
                rarity = int(re.search(r'\d', await rarity.text())[0])
                weapon = WeaponType[re.search(r'\w+', await weapon.text())[0].upper()].value
                element = Element[re.search(r'\w+', await element.text())[0].upper()].value
                characters[element][name] = [href, icon, rarity, weapon]
        del characters['Мульти']  #: Aether and Lumine has no future...
        return characters

    async def get_information(self) -> Optional[mdl.characters.Information]:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = (await tree.xpath('//table[@class="genshin_table main_table"]'))
        if not table:
            return None
        table = table[0]

        title = ''.join(await table.xpath('.//td[contains(text(), "Title")]/following-sibling::td/text()'))
        occ = ''.join(await table.xpath('.//td[contains(text(), "Occupation")]/following-sibling::td/text()'))
        association = Region[
            ''.join(await table.xpath('.//td[contains(text(), "Association")]/following-sibling::td/text()'))
            .upper()
        ].value
        birthdate = (await table.xpath('.//td[contains(text(), "of Birth")]/following-sibling::td/text()'))
        if len(birthdate) == 2:
            birthdate = f"{Month[IntMonth(int(birthdate[1])).name].value} {birthdate[0]}"
        else:
            birthdate = '--'
        con = (await table.xpath('.//td[contains(text(), "Constellation")]/following-sibling::td/text()'))[-1]
        desc = ''.join(await table.xpath('.//td[contains(text(), "Description")]/following-sibling::td/text()'))
        asc_stat = _format_stat(
            ''.join(
                await (await tree.xpath('//table[@class="genshin_table stat_table"]/thead'))[0]
                .xpath('.//td[last()-2]/text()')
            )
        )
        return mdl.characters.Information(
            self.name, title, occ, association,
            self.rarity, self.weapon, self.element,
            asc_stat, birthdate, con, desc
        )

    async def get_active_skills(self) -> List[mdl.characters.Skill]:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = await tree.xpath('//section[@id="char_skills"]/*')
        if not table:
            return []
        table = table[2:-11]

        active_skills = [
            table[0],  #: Auto attack
            table[1],  #: Elemental skill
            table[-1]  #: Elemental burst
        ]
        if len(table) % 4 == 0:
            active_skills.append(table[-2])  #: Alternative sprint
        return [
            mdl.characters.Skill(
                ''.join(await skill.xpath('.//tr[1]/td[2]/a/text()')),  #: Skill title
                await (await skill.xpath('.//tr[2]/td[1]'))[0].text(' ')  #: Skill description
            )
            for skill in active_skills
        ]

    async def get_passive_skills(self) -> List[mdl.characters.Skill]:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = await tree.xpath('//section[@id="char_skills"]/*')
        if not table:
            return []
        table = table[-10:-7]

        return [
            mdl.characters.Skill(
                ''.join(await skill.xpath('.//tr[1]/td[2]/a/text()')),
                await (await skill.xpath('.//tr[2]/td[1]'))[0].text(' ')
            )
            for skill in table[:3]  #: Passive skills from 1 to 3
        ]

    async def get_constellations(self) -> List[mdl.characters.Skill]:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = await tree.xpath('//section[@id="char_skills"]/*')
        if not table:
            return []
        table = table[-6:]

        return [
            mdl.characters.Skill(
                ''.join(await skill.xpath('.//tr[1]/td[2]/a/text()')),
                await (await skill.xpath('.//tr[2]/td[1]'))[0].text(' ')
            )
            for skill in table[:6]  #: Constellations for 1 to 6
        ]

    async def get_ascension(self) -> mdl.characters.Ascension:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        stat_table = await tree.xpath('//table[@class="genshin_table stat_table"]')
        asc_table = await tree.xpath('//table[@class="genshin_table asc_table"]')
        gacha_icon = self.icon.replace('.webp', '_gacha_card.webp')
        if not stat_table and not asc_table:
            return mdl.characters.Ascension(gacha_icon, [], [])

        lvl = []
        for a in await stat_table[1].xpath('./tr[last()-2]/td[3]/a'):
            href = re.search(r'\w+\d+', (await a.xpath('.//@href'))[0])[0]
            icon = f"{honeyimpact.URL}img/{href}.webp"
            quantity = await a.text()
            quantity = int(quantity) if 'K' not in quantity else 2092000  #: Total Mora
            lvl.append(mdl.characters.AscensionMaterial(icon, quantity))
        lvl.append(mdl.characters.AscensionMaterial(f"{honeyimpact.URL}/img/i_13.webp", 432))  #: Hero's Wit
        if not asc_table:
            return mdl.characters.Ascension(gacha_icon, lvl, [])

        talents = []
        for a in await asc_table[0].xpath('./tr[last()]/td[3]/a'):
            href = re.search(r'\w+\d+', (await a.xpath('.//@href'))[0])[0]
            icon = f"{honeyimpact.URL}img/{href}.webp"
            quantity = int((await a.text()).replace('K', '000')) * 3
            talents.append(mdl.characters.AscensionMaterial(icon, quantity))
        return mdl.characters.Ascension(gacha_icon, lvl, talents)


class WeaponParser:
    def __init__(self, w_type: str, name: str) -> None:
        self._data = json.load('weapons')[w_type][name]
        self.type = w_type
        self.name = name
        self.href: str = self._data[0]
        self.icon: str = self._data[1]
        self.rarity: int = self._data[2]
        self.atk: float = self._data[3]
        self.sub: str = self._data[4]
        self.value: Union[int, float, str] = self._data[5]
        self.affix: str = self._data[6]
        del self._data

    @classmethod
    async def get_weapons(cls) -> Optional[Dict[str, dict]]:
        weapons = {w.value: {} for w in WeaponType}

        for endpoint in _ENDPOINTS[cls.__name__]:
            tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + endpoint)
            if tree is None:
                return None
            table = await _deserialize(
                (await tree.xpath('//section[@id="weapons"]//script/text()'))[0],
                'sortable_data'
            )
            for weapon in table:
                _, name, rarity, atk, sub, value, affix, _ = weapon
                href = re.search(r'\w+\d+', (await name.xpath('//@href'))[0])[0]
                icon = f"{honeyimpact.URL}img/{href}.webp"
                name = re.search(r'[\w\s:?-]+', await name.text())[0]
                rarity = int(re.search(r'\d', await rarity.text())[0])
                if isinstance(sub, _AsyncHtmlElement):
                    sub = _format_stat(await sub.text())
                if isinstance(value, _AsyncHtmlElement):
                    value = await value.text()
                if isinstance(affix, _AsyncHtmlElement):
                    affix = re.sub(r'<[^>]+>', '', await affix.text())
                weapons[WeaponType[endpoint.split('_')[-1][:-1].upper()].value][name] = [
                    href, icon, rarity, atk, sub, value, affix
                ]
        return weapons

    async def get_information(self) -> Optional[mdl.weapons.Information]:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = (await tree.xpath('//table[@class="genshin_table main_table"]'))
        if not table:
            return None
        table = table[0]

        desc = ''.join(await table.xpath('.//td[text()="Description"]/following-sibling::td/text()'))
        return mdl.weapons.Information(
            self.name, self.type, self.rarity, 'Базовая атака', self.atk, self.sub, self.value, desc
        )

    async def get_ability(self) -> Optional[mdl.weapons.Ability]:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = (await tree.xpath('//table[@class="genshin_table main_table"]'))
        if not table:
            return None
        table = table[0]

        title = ''.join(await table.xpath('//td[text()="Weapon Affix"]/following-sibling::td/text()'))
        return mdl.weapons.Ability(title, self.affix)

    async def get_progression(self) -> List[mdl.weapons.Progression]:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = (await tree.xpath('//table[@class="genshin_table stat_table"]/tr'))

        return [
            mdl.weapons.Progression(
                (await row.xpath('./td[1]/text()'))[0],
                'Атака',
                (await row.xpath('./td[2]/text()'))[0],
                self.sub,
                (await row.xpath('./td[3]/text()'))[0]
            )
            for row in table  #: Returns empty list if not any progression information is presented
        ]

    async def get_refinement(self) -> List[mdl.weapons.Refinement]:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = (await tree.xpath('//table[@class="genshin_table affix_table"]/tr'))

        return [
            mdl.weapons.Refinement(
                (await row.xpath('./td[1]/text()'))[0],
                ''.join(await row.xpath('./td[2]//text()'))
            )
            for row in table
        ]

    async def get_story(self) -> str:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        return ''.join(await tree.xpath('//table[@class="genshin_table quotes_table"]/tr//text()')).strip()


class ArtifactParser:
    def __init__(self, a_type: str, name: str) -> None:
        self._data = json.load('artifacts')[a_type][name]
        self.type = a_type
        self.name = name
        self.href: str = self._data[0]
        self.icon: str = self._data[1]
        self.affix: List[str] = self._data[2]
        self.variants: int = self._data[3]
        del self._data

    @classmethod
    async def get_artifacts(cls) -> Optional[Dict[str, dict]]:
        a_type = 'Набор артефактов'
        artifacts = {a_type: {}}

        for endpoint in _ENDPOINTS[cls.__name__]:
            tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + endpoint)
            if tree is None:
                return None
            table = await _deserialize(
                (await tree.xpath('//table[@class="genshin_table sortable "]//script/text()'))[0],
                'sortable_data'
            )
            for artifact in table:
                icons, name, affix = artifact
                href = re.search(r'\w+\d+', (await name.xpath('//@href'))[0])[0]
                icon = f"{honeyimpact.URL}img/{href}.webp"
                name = re.search(r'[\w\s:?-]+', await name.text())[0]
                affix = [
                    re.sub(r'<[^>]+>|[124]-Piece:\s?', '', (await span.xpath('./text()'))[0])
                    for span in await affix.xpath('//span')
                ]
                variants = len(await icons.xpath('//@href')) - 1
                artifacts[a_type][name] = [href, icon, affix, variants]
        return artifacts

    async def get_information(self) -> Optional[mdl.artifacts.Information]:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = (await tree.xpath('//table[@class="genshin_table main_table"]'))
        if not table:
            return None
        table = table[0]

        rarity = (await table.xpath('//td[text()="Rarity"]/following-sibling::td/img'))
        rarity = f"{len(rarity)}-{len(rarity) + self.variants}"
        return mdl.artifacts.Information(self.name, self.type, rarity, self.affix)


class EnemyParser:
    def __init__(self, e_type: str, name: str) -> None:
        self._data = json.load('enemies')[e_type][name]
        self.type = e_type
        self.name = name
        self.href: str = self._data[0]
        self.icon: str = self._data[1]
        self.grade: str = self._data[2]
        self.drop: Dict[str, str] = self._data[3]
        del self._data

    @classmethod
    async def get_enemies(cls) -> Optional[Dict[str, dict]]:
        e_types = list(EnemyType)
        enemies = {e.value: {} for e in EnemyType}
        link = honeyimpact.URL + 'img/{}.webp'

        for i, endpoint in enumerate(_ENDPOINTS[cls.__name__]):
            tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + endpoint)
            if tree is None:
                return None
            table = await _deserialize(
                (await tree.xpath('//table[@class="genshin_table sortable "]//script/text()'))[0],
                'sortable_data'
            )
            for enemy in table:
                _, name, grade, drop = enemy
                href = re.search(r'\w+\d+', (await name.xpath('//@href'))[0])[0]
                icon = link.format(href)
                name = re.search(r'[\w\s:?-]+', await name.text())[0]
                grade = Grade[(await grade.text()).upper()].value
                if isinstance(drop, _AsyncHtmlElement):
                    drop = {
                        k: link.format(re.search(r'\w+\d+', v)[0])
                        for k, v in zip(await drop.xpath('//img/@alt'), await drop.xpath('//@href'))
                    }
                else:
                    drop = {}
                enemies[e_types[i].value][name] = [href, icon, grade, drop]
        return enemies

    async def get_information(self) -> Optional[mdl.enemies.Information]:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = (await tree.xpath('//table[@class="genshin_table main_table"]'))
        if not table:
            return None
        table = table[0]

        desc = ''.join(await table.xpath('.//td[text()="Description"]/following-sibling::td/text()'))
        return mdl.enemies.Information(self.name, self.type, self.grade, self.drop, desc)

    async def get_progression(self) -> List[mdl.enemies.Progression]:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = (await tree.xpath('//section[@id="Variant #1"]//table[@class="genshin_table stat_table"]/tr'))

        return [
            mdl.enemies.Progression(
                (await row.xpath('./td[1]/text()'))[0],
                (await row.xpath('./td[2]/text()'))[0],
                (await row.xpath('./td[3]/text()'))[0],
                (await row.xpath('./td[4]/text()'))[0],
                (await row.xpath('./td[5]/text()'))[0],
                (await row.xpath('./td[6]/text()'))[0],
                (await row.xpath('./td[7]/text()'))[0],
                (await row.xpath('./td[8]/text()'))[0],
                (await row.xpath('./td[9]/text()'))[0],
                (await row.xpath('./td[10]/text()'))[0],
                (await row.xpath('./td[11]/text()'))[0],
                (await row.xpath('./td[12]/text()'))[0],
                (await row.xpath('./td[13]/text()'))[0]
            )
            for row in table
        ]


class BookParser:
    def __init__(self, b_type: str, v_name: str) -> None:
        self._data = json.load('books')[b_type][v_name]
        self.type = b_type
        self.href: str = self._data[0]
        self.icon: str = self._data[1]
        self.rarity: int = self._data[2]
        self.v_num: int = self._data[3]
        self.story: Optional[str] = None
        del self._data

    @classmethod
    async def get_books(cls) -> Optional[Dict[str, dict]]:
        books = {}

        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL)
        if tree is None:
            return None
        b_table = await tree.xpath(
            '//label[@class="menu_item_text" and text()="Codex Series"][1]/following-sibling::div[1]/a'
        )
        for book in b_table:
            href = re.search(r'\w+\d+', (await book.xpath('./@href'))[0])[0]
            b_type = await book.text()
            tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + href)
            if tree is None:
                return None
            try:
                v_table = await _deserialize(
                    (await tree.xpath('//table[@class="genshin_table sortable "]//script/text()'))[0],
                    'sortable_data'
                )
            except IndexError:
                continue
            books[b_type] = {}
            for i, volume in enumerate(v_table):
                _, name, rarity, _ = volume
                href = re.search(r'\w+\d+', (await name.xpath('//@href'))[0])[0]
                icon = f"{honeyimpact.URL}img/{href}.webp"
                rarity = len(await rarity.xpath('//div/img'))
                v_num = i + 1
                books[b_type][f"Часть {v_num}"] = [href, icon, rarity, v_num]
        return books

    async def save(self) -> str:
        save_path = os.path.join(FILECACHE, f"{self.type} [{self.v_num}].txt")
        async with aiofiles.open(save_path, 'w') as book:
            await book.write(self.story)
        return save_path

    async def get_information(self) -> mdl.books.Information:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)

        self.story = ''.join(await tree.xpath('//table[@class="genshin_table quotes_table"]/tr//text()')).strip()
        return mdl.books.Information(self.type, self.v_num, self.story)


class DomainParser:
    def __init__(self, d_type: str, name: str) -> None:
        self._data = json.load('domains')[d_type][name]
        self.type = d_type
        self.name = name
        self.href: str = self._data[0]
        self.icon: str = self._data[1]
        self.monsters: List[str] = self._data[2]
        self.rewards: List[str] = self._data[3]
        del self._data

    @classmethod
    async def get_domains(cls) -> Optional[Dict[str, dict]]:
        d_types = list(DomainType)
        domains = {d.value: {} for d in DomainType}
        link = honeyimpact.URL + 'img/{}.webp'

        for i, endpoint in enumerate(_ENDPOINTS[cls.__name__]):
            tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + endpoint)
            if tree is None:
                return None
            table = await _deserialize(
                    (await tree.xpath('//table[@class="genshin_table sortable "]//script/text()'))[0],
                    'sortable_data'
                )
            for domain in table:
                _, name, monsters, rewards = domain
                href = re.search(r'\w+\d+', (await name.xpath('//@href'))[0])[0]
                icon = link.format(href)
                name = re.search(r'[\w\s:?-]+', await name.text())[0]
                if isinstance(monsters, _AsyncHtmlElement):
                    monsters = [link.format(re.search(r'\w+\d+', m)[0]) for m in await monsters.xpath('//@href')]
                else:
                    monsters = []
                if isinstance(rewards, _AsyncHtmlElement):
                    rewards = [link.format(re.search(r'\w+\d+', r)[0]) for r in await rewards.xpath('//@href')]
                else:
                    rewards = []
                domains[d_types[i].value][name] = [href, icon, monsters, rewards]
        return domains

    async def get_information(self) -> Optional[mdl.domains.Information]:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = (await tree.xpath('//table[@class="genshin_table main_table"]'))
        if not table:
            return None
        table = table[0]

        desc = ''.join(await table.xpath('.//td[text()="Description"]/following-sibling::td/text()'))
        return mdl.domains.Information(self.name, self.type, desc)


class DailyFarmParser:
    @classmethod
    async def get_zones(cls) -> Optional[List[mdl.dailyfarm.Zone]]:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL)
        if tree is None:
            return None
        table = await tree.xpath('//div[@class="homepage_index_cont calendar_day_wrap"]/*')
        zones = []
        for elem in table:
            if elem.tag == 'span':
                zones.append(
                    {'title': await elem.text(), 'materials': await cls._get_materials(elem), 'consumers': []}
                )
            else:
                zones[-1]['consumers'].append(await cls._get_consumer((await elem.xpath('./div'))[0]))
        return [mdl.dailyfarm.Zone(**zone) for zone in zones]

    @staticmethod
    async def _get_materials(elem: _AsyncHtmlElement) -> List[mdl.dailyfarm.Material]:
        materials = []
        for div in await elem.xpath('./div'):
            weekday = int(div.get('data-days'))
            for ep in await div.xpath('.//img/@src'):
                icon = honeyimpact.URL + re.sub(r'_\d+.webp.+', '.webp', ep[1:])
                materials.append(mdl.dailyfarm.Material(weekday, icon))
        return materials

    @staticmethod
    async def _get_consumer(elem: _AsyncHtmlElement) -> mdl.dailyfarm.Consumer:
        title = await elem.text()
        weekdays = [int(wd) for wd in list(elem.get('data-days'))]
        icon = honeyimpact.URL + re.sub(r'_\d+.webp', '.webp', (await elem.xpath('.//img/@src'))[0][1:])
        rarity = int(elem.get('class').split()[-1].rsplit('_', maxsplit=1)[-1])
        return mdl.dailyfarm.Consumer(title, weekdays, icon, rarity)


class TalentBookParser:
    @classmethod
    async def get_talent_books(cls) -> Optional[Dict[str, list]]:
        talent_books = {}
        link = honeyimpact.URL + 'img/{}.webp'

        for endpoint in _ENDPOINTS[cls.__name__]:
            tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + endpoint)
            if tree is None:
                return None
            table = await _deserialize(
                    (await tree.xpath('//table[@class="genshin_table sortable "]//script/text()'))[0],
                    'sortable_data'
                )
            for talent_book in table[2::3]:
                _, name, _, _, used_by = talent_book
                icon = link.format(re.search(r'\w+\d+', (await name.xpath('//@href'))[0])[0])
                if isinstance(used_by, _AsyncHtmlElement):
                    used_by = [link.format(re.search(r'\w+\d+', ch)[0]) for ch in await used_by.xpath('//@href')]
                else:
                    used_by = []
                talent_books[icon] = used_by
        return talent_books

    @staticmethod
    async def get_related_talent_books() -> List[mdl.talentbooks.TalentBook]:
        talent_books = json.load('talentbooks')
        materials = []
        for zone in await DailyFarmParser.get_zones():
            if len(zone.materials) % 3 == 0 and len(zone.materials) % 4 != 0:
                materials.extend(zone.materials[2::3])

        related_talent_books = {}
        for material in materials:
            if material.icon in talent_books:
                weekday = Weekday[IntWeekday(material.weekday).name]
                if material.icon not in related_talent_books:
                    related_talent_books[material.icon] = [weekday], talent_books[material.icon]
                else:
                    related_talent_books[material.icon][0].append(weekday)
        return [mdl.talentbooks.TalentBook(book, *data) for book, data in related_talent_books.items()]


class BossMaterialParser:
    @classmethod
    async def get_boss_materials(cls) -> Optional[Dict[str, list]]:
        boss_materials = {}
        link = honeyimpact.URL + 'img/{}.webp'

        for endpoint in _ENDPOINTS[cls.__name__]:
            tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + endpoint)
            if tree is None:
                return None
            table = await _deserialize(
                    (await tree.xpath('//table[@class="genshin_table sortable "]//script/text()'))[0],
                    'sortable_data'
                )
            for boss_material in table:
                _, name, _, _, used_by = boss_material
                icon = link.format(re.search(r'\w+\d+', (await name.xpath('//@href'))[0])[0])
                name = re.search(r'[\w\s:?-]+', await name.text())[0]
                if isinstance(used_by, _AsyncHtmlElement):
                    used_by = [link.format(re.search(r'\w+\d+', ch)[0]) for ch in await used_by.xpath('//@href')]
                else:
                    used_by = []
                boss_materials[name] = [icon, used_by]
        return boss_materials

    @staticmethod
    def get_related_bosses() -> List[mdl.bossmaterials.Boss]:
        bosses: Dict[str, list] = json.load('enemies')[EnemyType.BOSSES.value]
        boss_materials: Dict[str, list] = json.load('bossmaterials')

        related_bosses = []
        for boss, boss_data in bosses.items():
            related_materials = []
            for material, material_data in boss_materials.items():
                if material in boss_data[-1]:
                    related_materials.append(mdl.bossmaterials.BossMaterial(*material_data))
            related_bosses.append(mdl.bossmaterials.Boss(boss_data[1], related_materials))
        return related_bosses


_ENDPOINTS = {
    f"{CharacterParser.__name__}": ['fam_chars/'],
    f"{WeaponParser.__name__}": [
        'fam_sword/',
        'fam_claymore/',
        'fam_polearm/',
        'fam_bow/',
        'fam_catalyst/'
    ],
    f"{ArtifactParser.__name__}": ['fam_art_set/'],
    f"{EnemyParser.__name__}": [
        'mcat_20011201/',  #: Elemental Lifeforms
        'mcat_21010101/',  #: Hilichurls
        'mcat_22010101/',  #: The Abyss Order
        'mcat_23010601/',  #: Fatui
        'mcat_24010101/',  #: Automaton
        'mcat_25010101/',  #: Other Human Factions
        'mcat_26010201/',  #: Magical Beasts
        'mcat_29010101/'  #: Bosses
    ],
    f"{DomainParser.__name__}": [
        'dcat_1/',  #: Artifact
        'dcat_10/',  #: Character Material
        'dcat_2/',  #: Weapon Material
        'dcat_1006/'  #: Boss
    ],
    f"{TalentBookParser.__name__}": ['fam_talent_book/'],
    f"{BossMaterialParser.__name__}": ['fam_talent_boss/'],
}


@catch_aiohttp_errors
async def _get_tree(url: str) -> Optional[_AsyncHtmlElement]:
    loop = asyncio.get_running_loop()
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=honeyimpact.HEADERS, params=honeyimpact.ATTRIBUTES) as response:
            if response.ok:
                text = await response.text()
                return _AsyncHtmlElement(await loop.run_in_executor(None, html.document_fromstring, text))


async def _deserialize(text: str, anchor: str) -> List[List[Union[_AsyncHtmlElement, str, float, int]]]:
    """Function fetching and deserializing plain text array data
        from html <script>.

        :param text: plain text containing array data
        :param anchor: name of array
        :return: deserialized data fetched from plain text
        """
    loop = asyncio.get_running_loop()
    data = re.findall(fr"({anchor}.push)(\()(\[.+])(\);)", text.strip())
    data = eval(data[0][2])
    for row in data:
        for i, elem in enumerate(row):
            try:
                elem = _AsyncHtmlElement(await loop.run_in_executor(None, html.fromstring, elem))
            except (TypeError, ParserError):
                pass
            row[i] = elem
    return data


def _format_stat(stat: str) -> str:
    stat = stat.replace(' ', '_').upper()
    stat_enum = Stat[stat.replace('%', '')]
    return stat.replace(stat_enum.name, f"{stat_enum.value} ")
