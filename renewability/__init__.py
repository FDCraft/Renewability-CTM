# -*- coding: utf-8 -*-
import json
import re
from typing import Optional
from mcdreforged.api.all import *

from .PlayerDataGetter import PlayerDataGetter

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
    def __init__(self, item_id: str, count: int, nbt_str: int):
        self.id = item_id
        self.count = count
        self.nbt = nbt_str
        
    @classmethod
    def from_str(cls, itemstack_str):
        ID_REGEX = re.compile(r'^{id: "(.+?)", tag: ')
        ID_REGEX_2 = re.compile(r'^{id: "(.+?)"')
        item_id = ID_REGEX.search(itemstack_str)
        if item_id:
            item_id = item_id.group(1)
            itemstack_str = ID_REGEX.sub('', itemstack_str)
        else:
            item_id = ID_REGEX_2.search(itemstack_str).group(1)
            itemstack_str = ID_REGEX_2.sub('', itemstack_str)
            

        COUNT_REGEX = re.compile(r', Count: (\d{1,2}?)b}$')
        count = COUNT_REGEX.search(itemstack_str).group(1)
        nbt_str = COUNT_REGEX.sub('', itemstack_str).replace(' ', '')
        
        return cls(item_id, count, nbt_str)


def msg(content: str):
    return MsgPrefix + content

def get_itemstack(server: ServerInterface, player):
    try:
        
        itemstack_str = player_data_getter.get_player_info(player, 'SelectedItem', timeout=1)
        return str(itemstack_str)
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
    itemstack_str = get_itemstack(server, player)
    itemstack = ItemStack.from_str(itemstack_str)
    
    if itemstack:
        server.execute(f'give {player} {itemstack.id}{itemstack.nbt} {itemstack.count}')
        source.reply(msg(f'§a物品§7 {itemstack.id} §a复制成功§r'))
        server.logger.info(f'{player} cloned an item {itemstack.id}')
    else:
        source.reply(msg('§c当前主手上无物品§r'))
        return None


player_data_getter: PlayerDataGetter

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
    
    player_data_getter = PlayerDataGetter(server)
    if hasattr(prev, 'player_data_getter'):
        player_data_getter.queue_lock = prev.player_data_getter.queue_lock
        player_data_getter.work_queue = prev.player_data_getter.work_queue
    
def on_info(server, info):
	player_data_getter.on_info(info)