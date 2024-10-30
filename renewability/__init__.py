# -*- coding: utf-8 -*-
import json
import re
from typing import Optional
from mcdreforged.api.all import *

Prefix = '!!clone'
MsgPrefix = '[{0}] '
HelpMessage = '''
------ {1} v{2} ------
一个允许玩家§a复制§c物品§r的插件
§d【格式说明】§r
§7{0} §r复制手中物品
§7{0} help §r查看帮助
'''.strip()
# {0} = Prefix
# {1} = PLUGIN_METADATA.name
# {2} = PLUGIN_METADATA.version

PLUGIN_METADATA = Metadata({'id': 'renewability'})

class ItemStack:
    def __init__(self, item_id: str, count: int, componets: int):
        self.id = item_id
        self.count = count
        self.componets = componets
        
    @classmethod
    def from_json(cls, itemstack_json: dict):
        itemstack_json = json.loads(json.dumps(itemstack_json))
        
        item_id = itemstack_json['id']
        count = itemstack_json['count']
        
        componets = itemstack_json.get('components', None)
        
        if componets is None:
            return cls(item_id, count, '')
        
        componets_formatted = '['
            
        for key, value in componets.items():
            value = '\'' + value + '\'' if isinstance(value, str) else value
            componets_formatted += f'{key}={str(value)},'
        
        componets_formatted = componets_formatted[:-1]
        componets_formatted += ']'
        
        return cls(item_id, count, componets_formatted)


def msg(content: str):
    return MsgPrefix + content

def get_itemstack(server: ServerInterface, player):
    MCDataAPI = server.get_plugin_instance('minecraft_data_api')
    try:
        itemstack_json = MCDataAPI.get_player_info(player, 'SelectedItem', timeout=1)
        return itemstack_json
    except Exception as e:
        server.logger.error('Error occurred while getting item')
        server.logger.error(e)
        return None


@new_thread(PLUGIN_METADATA.name)
def clone_item(source: CommandSource):
    if not source.is_player:
        source.reply(msg('§c不可在 Console 中使用§r'))
        return None
    server = source.get_server()
    player = source.get_info().player
    itemstack_json = get_itemstack(server, player)
    itemstack = ItemStack.from_json(itemstack_json)
    
    if itemstack:
        server.execute(f'give {player} {itemstack.id}{itemstack.componets} {itemstack.count}')
        source.reply(msg(f'§a物品§7 {itemstack.id} §a复制成功§r'))
        server.logger.info(f'{player} cloned an item {itemstack.id}')
    else:
        source.reply(msg('§c当前主手上无物品§r'))
        return None


def on_load(server: PluginServerInterface, prev):
    global PLUGIN_METADATA, MsgPrefix, HelpMessage, player_data_getter
    PLUGIN_METADATA = server.get_self_metadata()
    
    MsgPrefix = MsgPrefix.format(PLUGIN_METADATA.name)
    HelpMessage = HelpMessage.format(Prefix, PLUGIN_METADATA.name, PLUGIN_METADATA.version)
    server.register_help_message(Prefix, '复制手中的不可再生物品')
    server.register_command(
        Literal(Prefix). \
        then(Literal('help').runs(lambda source: source.reply(HelpMessage))). \
        runs(clone_item)
    )