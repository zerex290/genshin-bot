from __future__ import annotations
import asyncio
import re
import os
from typing import Optional

import aiohttp
import aiofiles

from lxml import html
from lxml.html import HtmlElement
from lxml.etree import ParserError

from ..utils import json, catch_aiohttp_errors
from ..config import honeyimpact
from ..templates import honeyimpact as tpl
from ..models import honeyimpact as mdl
from ..config.dependencies.paths import FILECACHE
from ..types.uncategorized import Months, MonthIntegers
from ..types.genshin import Characters, Elements, Regions, Weapons, Stats, Enemies, Grades, Domains


__all__ = (
    'CharacterParser',
    'WeaponParser',
    'ArtifactParser',
    'EnemyParser',
    'BookParser',
    'DomainParser'
)


_ENDPOINTS = {
        'CharacterParser': ['fam_chars/'],
        'WeaponParser': [
            'fam_sword/',
            'fam_claymore/',
            'fam_polearm/',
            'fam_bow/',
            'fam_catalyst/'
        ],
        'ArtifactParser': ['fam_art_set/'],
        'EnemyParser': [
            'mcat_20011201/',  #: Elemental Lifeforms
            'mcat_21010101/',  #: Hilichurls
            'mcat_22010101/',  #: The Abyss Order
            'mcat_23010601/',  #: Fatui
            'mcat_24010101/',  #: Automaton
            'mcat_25010101/',  #: Other Human Factions
            'mcat_26010201/',  #: Magical Beasts
            'mcat_29010101/'  #: Bosses
        ],
        'BookParser': [''],
        'DomainParser': [
            'dcat_1/',  #: Artifact
            'dcat_10/',  #: Character Material
            'dcat_2/',  #: Weapon Material
            'dcat_1006/'  #: Boss
        ],
    }


class _AsyncHtmlElement(HtmlElement):
    def __init__(self, _element: HtmlElement) -> None:
        super().__init__()
        self._element = _element

    def __str__(self) -> str:
        return str(self._element)

    def __repr__(self) -> str:
        return repr(self._element)

    async def xpath(self, expr: str, *args) -> list[_AsyncHtmlElement | str | float | int]:
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
        return sep.join(await self.xpath('.//text()'))

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
    async def get_characters(cls) -> Optional[dict[str, dict]]:
        characters = {e.value: {} for e in Elements}

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
                name = Characters[href.split('_')[0].upper()].value
                rarity = int(re.search(r'\d', await rarity.text())[0])
                weapon = Weapons[re.search(r'\w+', await weapon.text())[0].upper()].value
                element = Elements[re.search(r'\w+', await element.text())[0].upper()].value
                characters[element][name] = [href, icon, rarity, weapon]
        del characters['Мульти']  #: Aether and Lumine has no future...
        return characters

    async def get_information(self) -> str:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = (await tree.xpath('//table[@class="genshin_table main_table"]'))[0]

        title = ''.join(await table.xpath('.//td[contains(text(), "Title")]/following-sibling::td/text()'))
        occ = ''.join(await table.xpath('.//td[contains(text(), "Occupation")]/following-sibling::td/text()'))
        association = Regions[
            ''.join(await table.xpath('.//td[contains(text(), "Association")]/following-sibling::td/text()'))
            .upper()
        ].value
        birthdate = (await table.xpath('.//td[contains(text(), "of Birth")]/following-sibling::td/text()'))
        if len(birthdate) == 2:
            birthdate = f"{Months[MonthIntegers(int(birthdate[1])).name].value} {birthdate[0]}"
        else:
            birthdate = '--'
        con = ''.join(await table.xpath('.//td[contains(text(), "Constellation")]/following-sibling::td/text()'))
        desc = ''.join(await table.xpath('.//td[contains(text(), "Description")]/following-sibling::td/text()'))
        asc_stat = _format_stat(
            ''.join(
                await (await tree.xpath('//table[@class="genshin_table stat_table"]/thead'))[0]
                .xpath('.//td[last()-2]/text()')
            )
        )

        character = mdl.characters.Information(
            self.name, title, occ, association,
            self.rarity, self.weapon, self.element,
            asc_stat, birthdate, con, desc
        )
        return tpl.characters.format_information(character)

    async def get_active_skills(self) -> str:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = await tree.xpath('//section[@id="char_skills"]/*')
        if not table:
            a_atk, e_skill, a_sprint, e_burst = (mdl.characters.Skill('', '') for _ in range(4))
            return tpl.characters.format_active_skills(a_atk, e_skill, a_sprint, e_burst)
        table = table[2:-11]

        a_atk = table[0]
        e_skill = table[1]
        a_sprint = table[-2] if (len(table) % 4 == 0) else ''
        e_burst = table[-1]

        a_atk_title = ''.join(await a_atk.xpath('.//tr[1]/td[2]/a/text()'))
        a_atk_desc = await (await a_atk.xpath('.//tr[2]/td[1]'))[0].text(' ')
        e_skill_title = ''.join(await e_skill.xpath('.//tr[1]/td[2]/a/text()'))
        e_skill_desc = await (await e_skill.xpath('.//tr[2]/td[1]'))[0].text(' ')
        if not isinstance(a_sprint, str):
            a_sprint_title = ''.join(await a_sprint.xpath('.//tr[1]/td[2]/a/text()'))
            a_sprint_desc = await (await a_sprint.xpath('.//tr[2]/td[1]'))[0].text(' ')
        else:
            a_sprint_title, a_sprint_desc = '', ''
        e_burst_title = ''.join(await e_burst.xpath('.//tr[1]/td[2]/a/text()'))
        e_burst_desc = await (await e_burst.xpath('.//tr[2]/td[1]'))[0].text(' ')

        a_atk = mdl.characters.Skill(a_atk_title, a_atk_desc)
        e_skill = mdl.characters.Skill(e_skill_title, e_skill_desc)
        a_sprint = mdl.characters.Skill(a_sprint_title, a_sprint_desc)
        e_burst = mdl.characters.Skill(e_burst_title, e_burst_desc)
        return tpl.characters.format_active_skills(a_atk, e_skill, a_sprint, e_burst)

    async def get_passive_skills(self) -> str:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = await tree.xpath('//section[@id="char_skills"]/*')
        if not table:
            f_passive, s_passive, t_passive = (mdl.characters.Skill('', '') for _ in range(3))
            return tpl.characters.format_passive_skills(f_passive, s_passive, t_passive)
        table = table[-10:-7]

        f_passive = table[0]
        s_passive = table[1]
        t_passive = table[2]

        f_passive_title = ''.join(await f_passive.xpath('.//tr[1]/td[2]/a/text()'))
        f_passive_desc = await (await f_passive.xpath('.//tr[2]/td[1]'))[0].text(' ')
        s_passive_title = ''.join(await s_passive.xpath('.//tr[1]/td[2]/a/text()'))
        s_passive_desc = await (await s_passive.xpath('.//tr[2]/td[1]'))[0].text(' ')
        t_passive_title = ''.join(await t_passive.xpath('.//tr[1]/td[2]/a/text()'))
        t_passive_desc = await (await t_passive.xpath('.//tr[2]/td[1]'))[0].text(' ')

        f_passive = mdl.characters.Skill(f_passive_title, f_passive_desc)
        s_passive = mdl.characters.Skill(s_passive_title, s_passive_desc)
        t_passive = mdl.characters.Skill(t_passive_title, t_passive_desc)
        return tpl.characters.format_passive_skills(f_passive, s_passive, t_passive)

    async def get_constellations(self) -> str:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = await tree.xpath('//section[@id="char_skills"]/*')
        if not table:
            f_passive, s_passive, t_passive = (mdl.characters.Skill('', '') for _ in range(3))
            return tpl.characters.format_passive_skills(f_passive, s_passive, t_passive)
        table = table[-6:]

        first_con = table[0]
        second_con = table[1]
        third_con = table[2]
        fourth_con = table[3]
        fifth_con = table[4]
        sixth_con = table[5]

        first_con_title = ''.join(await first_con.xpath('.//tr[1]/td[2]/a/text()'))
        first_con_desc = await (await first_con.xpath('.//tr[2]/td[1]'))[0].text(' ')
        second_con_title = ''.join(await second_con.xpath('.//tr[1]/td[2]/a/text()'))
        second_con_desc = await (await second_con.xpath('.//tr[2]/td[1]'))[0].text(' ')
        third_con_title = ''.join(await third_con.xpath('.//tr[1]/td[2]/a/text()'))
        third_con_desc = await (await third_con.xpath('.//tr[2]/td[1]'))[0].text(' ')
        fourth_con_title = ''.join(await fourth_con.xpath('.//tr[1]/td[2]/a/text()'))
        fourth_con_desc = await (await fourth_con.xpath('.//tr[2]/td[1]'))[0].text(' ')
        fifth_con_title = ''.join(await fifth_con.xpath('.//tr[1]/td[2]/a/text()'))
        fifth_con_desc = await (await fifth_con.xpath('.//tr[2]/td[1]'))[0].text(' ')
        sixth_con_title = ''.join(await sixth_con.xpath('.//tr[1]/td[2]/a/text()'))
        sixth_con_desc = await (await sixth_con.xpath('.//tr[2]/td[1]'))[0].text(' ')

        first_con = mdl.characters.Skill(first_con_title, first_con_desc)
        second_con = mdl.characters.Skill(second_con_title, second_con_desc)
        third_con = mdl.characters.Skill(third_con_title, third_con_desc)
        fourth_con = mdl.characters.Skill(fourth_con_title, fourth_con_desc)
        fifth_con = mdl.characters.Skill(fifth_con_title, fifth_con_desc)
        sixth_con = mdl.characters.Skill(sixth_con_title, sixth_con_desc)
        return tpl.characters.format_constellations(
            first_con, second_con, third_con, fourth_con, fifth_con, sixth_con
        )


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
        self.value: int | float | str = self._data[5]
        self.affix: str = self._data[6]
        del self._data

    @classmethod
    async def get_weapons(cls) -> Optional[dict[str, dict]]:
        weapons = {w.value: {} for w in Weapons}

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
                name = re.search(r'[\w\s:]+', await name.text())[0]
                rarity = int(re.search(r'\d', await rarity.text())[0])
                if isinstance(sub, _AsyncHtmlElement):
                    sub = _format_stat(await sub.text())
                if isinstance(value, _AsyncHtmlElement):
                    value = await value.text()
                if isinstance(affix, _AsyncHtmlElement):
                    affix = re.sub(r'<[^>]+>', '', await affix.text())
                weapons[Weapons[endpoint.split('_')[-1][:-1].upper()].value][name] = [
                    href, icon, rarity, atk, sub, value, affix
                ]
        return weapons

    async def get_information(self) -> str:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = (await tree.xpath('//table[@class="genshin_table main_table"]'))[0]

        desc = ''.join(await table.xpath('.//td[text()="Description"]/following-sibling::td/text()'))

        weapon = mdl.weapons.Information(
            self.name, self.type, self.rarity, 'Базовая атака', self.atk, self.sub, self.value, desc
        )
        return tpl.weapons.format_information(weapon)

    async def get_ability(self) -> str:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = (await tree.xpath('//table[@class="genshin_table main_table"]'))[0]

        title = ''.join(await table.xpath('//td[text()="Weapon Affix"]/following-sibling::td/text()'))

        ability = mdl.weapons.Ability(title, self.affix)
        return tpl.weapons.format_ability(ability)

    async def get_progression(self) -> str:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = (await tree.xpath('//table[@class="genshin_table stat_table"]/tr'))

        progressions = []
        for row in table:
            progressions.append(
                mdl.weapons.Progression(
                    (await row.xpath('./td[1]/text()'))[0],
                    'Атака',
                    (await row.xpath('./td[2]/text()'))[0],
                    self.sub,
                    (await row.xpath('./td[3]/text()'))[0]
                )
            )
        return tpl.weapons.format_progression(progressions)

    async def get_refinement(self) -> str:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = (await tree.xpath('//table[@class="genshin_table affix_table"]/tr'))

        refinements = []
        for row in table:
            refinements.append(
                mdl.weapons.Refinement(
                    (await row.xpath('./td[1]/text()'))[0],
                    ''.join(await row.xpath('./td[2]//text()'))
                )
            )
        return tpl.weapons.format_refinement(refinements)

    async def get_story(self) -> str:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        story = ''.join(await tree.xpath('//table[@class="genshin_table quotes_table"]/tr//text()')).strip()
        return tpl.weapons.format_story(''.join(story))


class ArtifactParser:
    def __init__(self, a_type: str, name: str) -> None:
        self._data = json.load('artifacts')[a_type][name]
        self.type = a_type
        self.name = name
        self.href: str = self._data[0]
        self.icon: str = self._data[1]
        self.affix: list[str] = self._data[2]
        self.variants: int = self._data[3]
        del self._data

    @classmethod
    async def get_artifacts(cls) -> Optional[dict[str, dict]]:
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
                name = re.search(r'[\w\s:]+', await name.text())[0]
                affix = [
                    re.sub(r'<[^>]+>|[124]-Piece:\s?', '', (await span.xpath('./text()'))[0])
                    for span in await affix.xpath('//span')
                ]
                variants = len(await icons.xpath('//@href')) - 1
                artifacts[a_type][name] = [href, icon, affix, variants]
        return artifacts

    async def get_information(self) -> str:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = (await tree.xpath('//table[@class="genshin_table main_table"]'))[0]

        rarity = (await table.xpath('//td[text()="Rarity"]/following-sibling::td/img'))
        rarity = f"{len(rarity)}-{len(rarity) + self.variants}"

        artifact = mdl.artifacts.Information(self.name, self.type, rarity, self.affix)
        return tpl.artifacts.format_information(artifact)


class EnemyParser:
    def __init__(self, e_type: str, name: str) -> None:
        self._data = json.load('enemies')[e_type][name]
        self.type = e_type
        self.name = name
        self.href: str = self._data[0]
        self.icon: str = self._data[1]
        self.grade: str = self._data[2]
        self.drop: str = self._data[3]
        del self._data

    @classmethod
    async def get_enemies(cls) -> Optional[dict[str, dict]]:
        e_types = list(Enemies)
        enemies = {e.value: {} for e in Enemies}

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
                icon = f"{honeyimpact.URL}img/{href}.webp"
                name = re.search(r'[\w\s:]+', await name.text())[0]
                grade = Grades[(await grade.text()).upper()].value
                if isinstance(drop, _AsyncHtmlElement):
                    drop = ', '.join(await drop.xpath('//img/@alt'))
                enemies[e_types[i].value][name] = [href, icon, grade, drop]
        return enemies

    async def get_information(self) -> str:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = (await tree.xpath('//table[@class="genshin_table main_table"]'))[0]

        desc = ''.join(await table.xpath('.//td[text()="Description"]/following-sibling::td/text()'))

        enemy = mdl.enemies.Information(self.name, self.type, self.grade, self.drop, desc)
        return tpl.enemies.format_information(enemy)

    async def get_progression(self) -> str:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = (await tree.xpath('//section[@id="Variant #1"]//table[@class="genshin_table stat_table"]/tr'))

        progressions = []
        for row in table:
            progressions.append(
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
            )
        return tpl.enemies.format_progression(progressions)


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
    async def get_books(cls) -> Optional[dict[str, dict]]:
        books = {}

        for endpoint in _ENDPOINTS[cls.__name__]:
            tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + endpoint)
            if tree is None:
                return None
            b_table = await tree.xpath(
                '//label[@class="menu_item_text" and text()="Книги"]/following-sibling::div[1]//a'
            )
            for book in b_table:
                href = re.search(r'\w+\d+', (await book.xpath('./@href'))[0])[0]
                b_type = await book.text()
                tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + href)
                if tree is None:
                    return None
                v_table = await _deserialize(
                    (await tree.xpath('//table[@class="genshin_table sortable "]//script/text()'))[0],
                    'sortable_data'
                )
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

    async def get_information(self) -> str:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)

        self.story = ''.join(await tree.xpath('//table[@class="genshin_table quotes_table"]/tr//text()')).strip()

        book = mdl.books.Information(self.type, self.v_num, self.story)
        information = tpl.books.format_information(book)
        if len(information) > 4096:
            story = 'Недоступно из-за ограничения Вконтакте на максимальную длину сообщения...'
            book = mdl.books.Information(self.type, self.v_num, story)
            information = tpl.books.format_information(book)
        return information


class DomainParser:
    def __init__(self, d_type: str, name: str) -> None:
        self._data = json.load('domains')[d_type][name]
        self.type = d_type
        self.name = name
        self.href: str = self._data[0]
        self.icon: str = self._data[1]
        self.monsters: list[str] = self._data[2]
        self.rewards: list[str] = self._data[3]
        del self._data

    @classmethod
    async def get_domains(cls) -> Optional[dict[str, dict]]:
        d_types = list(Domains)
        domains = {d.value: {} for d in Domains}

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
                icon = f"{honeyimpact.URL}img/{href}.webp"
                name = re.search(r'[\w\s:]+', await name.text())[0]
                monsters = [honeyimpact.URL + m.replace('\\', '')[1:] for m in await monsters.xpath('//img/@src')]
                rewards = [honeyimpact.URL + r.replace('\\', '')[1:] for r in await rewards.xpath('//img/@src')]
                domains[d_types[i].value][name] = [href, icon, monsters, rewards]
        return domains

    async def get_information(self) -> str:
        tree: Optional[_AsyncHtmlElement] = await _get_tree(honeyimpact.URL + self.href)
        table = (await tree.xpath('//table[@class="genshin_table main_table"]'))[0]

        desc = ''.join(await table.xpath('.//td[text()="Description"]/following-sibling::td/text()'))

        domain = mdl.domains.Information(self.name, self.type, desc)
        return tpl.domains.format_information(domain)


@catch_aiohttp_errors
async def _get_tree(url: str) -> Optional[_AsyncHtmlElement]:
    loop = asyncio.get_running_loop()
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=honeyimpact.HEADERS, params=honeyimpact.ATTRIBUTES) as response:
            if response.ok:
                text = await response.text()
                return _AsyncHtmlElement(await loop.run_in_executor(None, html.document_fromstring, text))


async def _deserialize(text: str, anchor: str) -> list[list[_AsyncHtmlElement | str | float | int]]:
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
    stat_enum = Stats[stat.replace('%', '')]
    return stat.replace(stat_enum.name, f"{stat_enum.value} ")
