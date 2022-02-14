"""Service use only"""


import requests
from lxml import html

from fake_useragent import UserAgent
from fake_useragent.errors import FakeUserAgentError

import constants
import templates.honeyimpact


class Parser:
    """Base params"""
    BASE_URL = 'https://genshin.honeyhunterworld.com/'
    HEADERS = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,'
                  'image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'ru,en;q=0.9',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like '
                      'Gecko) Chrome/94.0.4606.85 YaBrowser/21.11.0.1996 Yowser/2.5 Safari/537.36',
        'Content-Type': 'text/html; charset=UTF-8',
    }
    ATTRIBUTES = {
        'lang': ''
    }

    def __init__(self, lang='RU'):
        self.lang = lang
        self.ATTRIBUTES['lang'] = self.lang
        self.html = None
        self.tree = None

    def upd_user_agent(self) -> int:
        try:
            ua = UserAgent()
            self.HEADERS['user-agent'] = ua.random
        except FakeUserAgentError:
            return 0
        return 1

    def parse(self, url: str) -> int:
        try:
            self.html = requests.get(url=url, headers=self.HEADERS, params=self.ATTRIBUTES).text
            self.tree = html.document_fromstring(self.html)
        except requests.exceptions.RequestException:
            self.tree = html.document_fromstring('<html></html>')
        return 1


class Characters(Parser):
    """Character links"""
    CERTAIN = 'db/char/'
    RELEASED = 'db/char/characters/'
    BETA = 'db/char/unreleased-and-upcoming-characters/'

    def __init__(self, lang='RU'):
        super().__init__(lang)
        self.characters = self._get_characters()
        self._template = templates.honeyimpact.Characters()

    def _get_characters(self) -> dict:
        characters = {}
        urls = (self.BASE_URL + self.BETA, self.BASE_URL + self.RELEASED)

        for el in constants.Genshin.ELEMENT:
            characters[constants.Genshin.ELEMENT[el]['ru']] = {}

        for url in urls:
            self.upd_user_agent()
            self.parse(url)
            container = self.tree.xpath('//div[@class="char_sea_cont"]//span[@class="sea_charname"]')

            for char in container:
                name = ''.join(char.xpath('./text()'))
                pointer = char.xpath('./..')[0].items()[0][-1].split('/')[-2]

                elem = char.xpath('./../..//img[contains(@class, "element")]')
                elem = elem[0].items()[-1][-1].split('/')[-1].replace('_35.png', '').capitalize()

                characters[constants.Genshin.ELEMENT[elem]['ru']][name] = pointer
        return characters

    def _get_certain_character(self, name: str, elem: str) -> int:
        self.parse(f"{self.BASE_URL}{self.CERTAIN}{self.characters[elem][name]}/")
        return 1

    def get_icon(self, api, name: str, elem: str) -> list:
        url = f"{self.BASE_URL}img/char/{self.characters[elem][name]}.png"
        response = api.vk.files.get_files_id(
            api.vk.files.upload_file(
                2000000005, api.vk.files.download_file(url, 'photo', 'png', cache=True), 'photo'
            )
        )
        return response

    def get_information(self, name: str, elem: str) -> str:
        self._get_certain_character(name, elem)
        table = self.tree.xpath('//div[@class="wrappercont"]//table[@class="item_main_table"][1]')[0]
        title = ''.join(table.xpath('.//td[contains(text(), "Title")]/following-sibling::td/text()'))
        allegiance = ''.join(table.xpath('.//td[contains(text(), "Allegiance")]/following-sibling::td/text()'))
        rarity = len(table.xpath('.//td[contains(text(), "Rarity")]/following-sibling::td/div'))
        weapon = constants.Genshin.WEAPON_TYPES[
            ''.join(table.xpath('.//td[contains(text(), "Weapon")]/following-sibling::td/a/text()'))
        ]
        birthday = ''.join(table.xpath('.//td[contains(text(), "Birth")]/following-sibling::td/text()')).split()

        try:
            birthday = ''.join(table.xpath('.//td[contains(text(), "Birth")]/following-sibling::td/text()')).split()
            day, month = birthday
            birthday = f"{constants.Uncategorized.MONTHS[month]} {day}"
        except ValueError:
            birthday = constants.Uncategorized.MONTHS[''.join(birthday)]

        const = ''.join(table.xpath('.//td[contains(text(), "Astrolabe")]/following-sibling::td/text()'))
        desc = ''.join(table.xpath('.//td[contains(text(), "Description")]/following-sibling::td/text()'))

        info = {
            'name': name,
            'title': title,
            'allegiance': allegiance,
            'rarity': rarity,
            'weapon_type': weapon,
            'element': elem,
            'birthday': birthday,
            'constellation_title': const,
            'description': desc
        }
        return self._template.main(info)

    def get_skills(self, name: str, elem: str) -> str:
        self._get_certain_character(name, elem)
        table = self.tree.xpath(
            '//table[preceding-sibling::span[text()="Attack Talents"]]'
            '[following-sibling::span[contains(text(), "Talent Ascension Materials")]]'
        )
        auto = table[0] if table else ''
        e = table[1] if table else ''
        sprint = table[2] if len(table) == 4 or len(table) == 8 else ''
        ult = (table[3] if len(sprint) else table[2]) if table else ''
        if not isinstance(auto, str):
            auto_title = ''.join(auto.xpath('.//tr[1]/td[2]/a/text()'))
            auto_desc = ''.join(auto.xpath('.//tr[2]//div//text()')).replace('•', '')
        else:
            auto_title, auto_desc = '', ''
        if not isinstance(e, str):
            e_title = ''.join(e.xpath('.//tr[1]/td[2]/a/text()'))
            e_desc = ''.join(e.xpath('.//tr[2]//div//text()'))
        else:
            e_title, e_desc = '', ''
        if not isinstance(sprint, str):
            sprint_title = ''.join(sprint.xpath('.//tr[1]/td[2]/a/text()'))
            sprint_desc = ''.join(sprint.xpath('.//tr[2]//div//text()')).replace('•', '')
        else:
            sprint_title, sprint_desc = '', ''
        if not isinstance(ult, str):
            ult_title = ''.join(ult.xpath('.//tr[1]/td[2]/a/text()'))
            ult_desc = ''.join(ult.xpath('.//tr[2]//div//text()')).replace('•', '')
        else:
            ult_title, ult_desc = '', ''

        info = {
            'auto_attack': {'title': auto_title, 'description': auto_desc},
            'elemental_skill': {'title': e_title, 'description': e_desc},
            'sprint': {'title': sprint_title, 'description': sprint_desc},
            'elemental_burst': {'title': ult_title, 'description': ult_desc}
        }
        return self._template.skills(info)

    def get_passives(self, name: str, elem: str) -> str:
        self._get_certain_character(name, elem)
        table = self.tree.xpath(
            '//div[@id="live_data"]/table[preceding-sibling::span[@id="scroll_passive_talent"]]'
            '[following-sibling::span[@id="scroll_constellation"]]/tr'
        )
        if not table:
            table = self.tree.xpath(
                '//div[@class="wrappercont"]//table[preceding-sibling::span[@id="beta_scroll_passive_talent"]]'
                '[following-sibling::span[@id="beta_scroll_constellation"]]/tr'
            )
        first_passive_name = ''.join(table[0].xpath('.//text()')) if table else ''
        first_passive_desc = ''.join(table[1].xpath('.//text()')).replace('•', '') if table else ''
        second_passive_name = ''.join(table[2].xpath('.//text()')) if table else ''
        second_passive_desc = ''.join(table[3].xpath('.//text()')).replace('•', '') if table else ''
        third_passive_name = ''.join(table[-2].xpath('.//text()')) if table else ''
        third_passive_desc = ''.join(table[-1].xpath('.//text()')).replace('•', '') if table else ''

        info = {
            'first_passive': {'title': first_passive_name, 'description': first_passive_desc},
            'second_passive': {'title': second_passive_name, 'description': second_passive_desc},
            'third_passive': {'title': third_passive_name, 'description': third_passive_desc}
        }
        return self._template.passives(info)

    def get_constellations(self, name: str, elem: str) -> str:
        self._get_certain_character(name, elem)
        table = self.tree.xpath(
            '//div[@id="live_data"]/table[preceding-sibling::span[@id="scroll_constellation"]]/tr'
        )
        if not table:
            table = self.tree.xpath(
                '//div[@class="wrappercont"]//table[preceding-sibling::span[@id="beta_scroll_constellation"]]/tr'
            )
        first_con_name = ''.join(table[0].xpath('.//text()')) if table else ''
        first_con_desc = ''.join(table[1].xpath('.//text()')) if table else ''
        second_con_name = ''.join(table[2].xpath('.//text()')) if table else ''
        second_con_desc = ''.join(table[3].xpath('.//text()')) if table else ''
        third_con_name = ''.join(table[4].xpath('.//text()')) if table else ''
        third_con_desc = ''.join(table[5].xpath('.//text()')) if table else ''
        fourth_con_name = ''.join(table[6].xpath('.//text()')) if table else ''
        fourth_con_desc = ''.join(table[7].xpath('.//text()')) if table else ''
        fifth_con_name = ''.join(table[8].xpath('.//text()')) if table else ''
        fifth_con_desc = ''.join(table[9].xpath('.//text()')) if table else ''
        sixth_con_name = ''.join(table[10].xpath('.//text()')) if table else ''
        sixth_con_desc = ''.join(table[11].xpath('.//text()')) if table else ''

        info = {
            'first_constellation': {'title': first_con_name, 'description': first_con_desc},
            'second_constellation': {'title': second_con_name, 'description': second_con_desc},
            'third_constellation': {'title': third_con_name, 'description': third_con_desc},
            'fourth_constellation': {'title': fourth_con_name, 'description': fourth_con_desc},
            'fifth_constellation': {'title': fifth_con_name, 'description': fifth_con_desc},
            'sixth_constellation': {'title': sixth_con_name, 'description': sixth_con_desc}
        }
        return self._template.constellations(info)


class Weapons(Parser):
    def __init__(self, lang='RU'):
        super().__init__(lang)
        self.weapons = self._get_weapons()
        self._template = templates.honeyimpact.Weapons()

    def _get_weapons(self) -> dict:
        weapons = {}

        for type_ in constants.Genshin.WEAPON_TYPES:
            weapons[constants.Genshin.WEAPON_TYPES[type_]] = {}
            self.parse(f"{self.BASE_URL}db/weapon/{type_.lower()}/")
            table = self.tree.xpath('//div[@class="scrollwrapper"]/table[@class="art_stat_table"]/tr//a')

            for a in table:
                if a.xpath('./text()'):
                    name = ''.join(a.xpath('./text()'))
                    code = a.get('href').split('/')[3] if a.get('href').find('weapon') != -1 else ''
                    rarity = str(len(a.xpath('../following-sibling::td/div[contains(@class, "stars")]')))
                    weapons[constants.Genshin.WEAPON_TYPES[type_]][name] = {}
                    weapons[constants.Genshin.WEAPON_TYPES[type_]][name]['code'] = code
                    weapons[constants.Genshin.WEAPON_TYPES[type_]][name]['rarity'] = rarity
        return weapons

    def _get_certain_weapon(self, name: str, type_: str) -> int:
        self.parse(f"{self.BASE_URL}weapon/{self.weapons[type_][name]['code']}/")
        return 1

    def get_icon(self, api, name: str, type_: str) -> list:
        url = f"{self.BASE_URL}img/weapon/{self.weapons[type_][name]['code']}.png"
        response = api.vk.files.get_files_id(
            api.vk.files.upload_file(
                2000000005, api.vk.files.download_file(url, 'photo', 'png', cache=True), 'photo'
            )
        )
        return response

    def get_information(self, name: str, type_: str) -> str:
        self._get_certain_weapon(name, type_)
        table = self.tree.xpath('//div[@class="wrappercont"]//table[@class="item_main_table"][1]')[0]
        fst_stat_value = ''.join(table.xpath('.//td[text()="Base Attack"]/following-sibling::td/text()'))
        snd_stat = ''.join(table.xpath('.//td[text()="Secondary Stat"]/following-sibling::td/text()'))
        snd_stat_value = ''.join(table.xpath('.//td[text()="Secondary Stat Value"]/following-sibling::td/text()'))
        desc = ''.join(table.xpath('.//tr/td[contains(text(), "In-game Description")]/following-sibling::td/text()'))

        info = {
            'name': name,
            'type': type_,
            'rarity': self.weapons[type_][name]['rarity'],
            'primary_stat': 'Базовая атака',
            'primary_stat_value': fst_stat_value,
            'secondary_stat': snd_stat,
            'secondary_stat_value': snd_stat_value,
            'description': desc
        }
        return self._template.main(info)

    def get_ability(self, name: str, type_: str):
        self._get_certain_weapon(name, type_)

        def get_information(beta: bool = False) -> tuple:
            table_number = 1 if beta else 0

            table_list = self.tree.xpath(f'//div[@class="wrappercont"]//table[@class="item_main_table"]')
            table = table_list[table_number]
            title = ''.join(table.xpath('.//tr/td[text()="Special (passive) Ability"]/following-sibling::td/text()'))
            desc = ''.join(table.xpath('.//tr/td[contains(text(), "Ability Desc")]/following-sibling::td//text()'))
            return title, desc

        abi_title, abi_desc = get_information()
        abi_title, abi_desc = get_information(beta=True) if not abi_title or not abi_desc else (abi_title, abi_desc)
        info = {
            'ability_title': abi_title,
            'ability_description': abi_desc
        }
        return self._template.ability(info)

    def get_progression(self, name: str, type_: str) -> str:
        self._get_certain_weapon(name, type_)
        table = self.tree.xpath(
            '//table[@class="add_stat_table"][preceding-sibling::span[contains(text(), "Stat Progress")]]'
            '[following-sibling::span[contains(text(), "Refine")]]'
        )
        snd_stat = self.tree.xpath(
            '//div[@class="wrappercont"]//td[text()="Secondary Stat"]/following-sibling::td/text()'
        )
        info = []

        for tr in table[0].xpath('./tr[position()>1]'):
            info.append({
                'Лв': tr.xpath('./td[1]/text()')[0], 'Атака': tr.xpath('./td[2]/text()')[0],
                snd_stat[0]: tr.xpath('./td[3]/text()')[0]
            })
        return self._template.progression(info)

    def get_story(self, name: str, type_: str) -> str:
        self._get_certain_weapon(name, type_)

        info = self.tree.xpath(
            '//span[@class="item_secondary_title"][text()="Item Story"]/following-sibling::table//text()'
        )
        response = self._template.story(info)
        return response


class Artifacts(Parser):
    def __init__(self, lang='RU'):
        super().__init__(lang)
        self.artifacts = self._get_artifacts()
        self._template = templates.honeyimpact.Artifacts()

    def _get_artifacts(self) -> dict:
        artifacts = {}

        for type_ in constants.Genshin.ARTIFACT_TYPES:
            artifacts[constants.Genshin.ARTIFACT_TYPES[type_]] = {}

        self.parse(f"{self.BASE_URL}db/artifact/")
        tables = self.tree.xpath('//div[@class="wrappercont"]/table[contains(@class, "art_stat_table")]')
        for i, table in enumerate(tables):
            for tr in table.xpath('./tr[position()>1]'):
                if tr.xpath('.//a/text()'):
                    name = ''.join(tr.xpath('.//a/text()'))
                    code = tr.xpath('.//a')[0].items()[0][-1].split('/')[-2]
                    rarity = '-'.join([str(len(div)) for div in tr.xpath('.//div[@class="star_art_wrap_cont"]')])
                    icon = f"{self.BASE_URL}{tr.xpath('.//a//img')[0].items()[-1][-1][1:-7]}.png"
                    artifacts[list(constants.Genshin.ARTIFACT_TYPES.values())[i]][name] = {}
                    artifacts[list(constants.Genshin.ARTIFACT_TYPES.values())[i]][name]['code'] = code
                    artifacts[list(constants.Genshin.ARTIFACT_TYPES.values())[i]][name]['rarity'] = rarity.strip()
                    artifacts[list(constants.Genshin.ARTIFACT_TYPES.values())[i]][name]['icon'] = icon
        return artifacts

    def _get_certain_artifact(self, name: str, type_: str) -> int:
        self.parse(f"{self.BASE_URL}db/art/family/{self.artifacts[type_][name]['code']}/")
        return 1

    def get_icon(self, api, name: str, type_: str) -> list:
        url = f"{self.artifacts[type_][name]['icon']}"
        response = api.vk.files.get_files_id(
            api.vk.files.upload_file(
                2000000005, api.vk.files.download_file(url, 'photo', 'png', cache=True), 'photo'
            )
        )
        return response

    def get_information(self, name: str, type_: str) -> str:
        self._get_certain_artifact(name, type_)
        table = self.tree.xpath('//table[@class="item_main_table"]')[0]
        two_piece = ''.join(table.xpath('./tr/td[contains(text(), "2 Piece")]/following-sibling::td/text()'))
        four_piece = ''.join(table.xpath('./tr/td[contains(text(), "4 Piece")]/following-sibling::td/text()'))

        info = {
            'name': name,
            'type': type_,
            'rarity': self.artifacts[type_][name]['rarity'],
            'two_piece_bonus': two_piece,
            'four_piece_bonus': four_piece,
        }
        return self._template.main(info)


class Enemies(Parser):
    def __init__(self, lang='RU'):
        super().__init__(lang)
        self.enemies = self._get_enemies()
        self._template = templates.honeyimpact.Enemies()

    def _get_enemies(self):
        enemies = {}
        type_ = ''

        self.parse(f"{self.BASE_URL}db/enemy/")
        tables = self.tree.xpath('//div[contains(@class, "wrappercont_char")]/*')

        for item in tables[2:]:
            if str(item).find('span') != -1:
                type_ = ''.join(item.xpath('./text()'))
                if constants.Genshin.ENEMY_TYPES[type_] not in enemies:
                    enemies[constants.Genshin.ENEMY_TYPES[type_]] = {}
            else:
                name = ''.join(item.xpath('./a//text()'))
                code = item.xpath('./a')[0].items()[0][-1].split('/')[-2]
                enemies[constants.Genshin.ENEMY_TYPES[type_]][name] = code
        return enemies

    def _get_certain_enemy(self, name: str, type_: str) -> int:
        self.parse(f"{self.BASE_URL}db/monster/{self.enemies[type_][name]}/")
        return 1

    def get_icon(self, api, name: str, type_: str) -> list:
        url = f"{self.BASE_URL}/img/enemy/{self.enemies[type_][name]}.png"
        response = api.vk.files.get_files_id(
            api.vk.files.upload_file(
                2000000005, api.vk.files.download_file(url, 'photo', 'png', cache=True), 'photo'
            )
        )
        return response

    def get_information(self, name: str, type_: str) -> str:
        self._get_certain_enemy(name, type_)
        desc = ''.join(self.tree.xpath('//table[@class="item_main_table"]/tr[last()]/td[last()]//text()'))
        drop = self.tree.xpath(
            '//table[@class="add_stat_table"][preceding-sibling::span[@class="item_secondary_title"]]'
        )
        drop = ', '.join([''.join(d.xpath('.//a//text()')) for d in drop[0].xpath('./tr[position()>1]')])

        info = {
            'name': name,
            'type': type_,
            'description': desc,
            'drop': drop
        }
        return self._template.main(info)

    def get_progression(self, name: str, type_: str) -> str:
        self._get_certain_enemy(name, type_)
        table = self.tree.xpath('//div[@class="scrollwrapper"]/table')
        table = table[0].xpath('./tr[position()>1]') if table else []
        info = []

        for stat in table:
            info.append({
                'Лв': stat.xpath('./td[1]/text()')[0][2:],
                '💉': stat.xpath('./td[2]/text()')[0],
                '🗡': stat.xpath('./td[3]/text()')[0],
                '🛡': stat.xpath('./td[4]/text()')[0],
                '2⃣👤💉': stat.xpath('./td[5]/text()')[0],
                '2⃣👤🗡': stat.xpath('./td[6]/text()')[0],
                '2⃣👤🛡': stat.xpath('./td[7]/text()')[0],
                '3⃣👤💉': stat.xpath('./td[8]/text()')[0],
                '3⃣👤🗡': stat.xpath('./td[9]/text()')[0],
                '3⃣👤🛡': stat.xpath('./td[10]/text()')[0],
                '4⃣👤💉': stat.xpath('./td[11]/text()')[0],
                '4⃣👤🗡': stat.xpath('./td[12]/text()')[0],
                '4⃣👤🛡': stat.xpath('./td[13]/text()')[0],
            })
        return self._template.progression(info)
