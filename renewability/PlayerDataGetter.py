import re
from queue import Queue, Empty
from threading import RLock
from typing import Dict, Optional

from mcdreforged.api.all import *

class PlayerDataGetter:
	class QueueTask:
		def __init__(self):
			self.queue = Queue()
			self.count = 0

	def __init__(self, server: PluginServerInterface):
		self.queue_lock = RLock()
		self.work_queue: Dict[str, PlayerDataGetter.QueueTask] = {}
		self.server: PluginServerInterface = server

	@classmethod
	def remove_command_result_prefix(cls, text: str) -> str:
		__COMMAND_RESULT_PREFIX_REGEX = re.compile(r'^[^ ]* has the following entity data: ')
		return __COMMAND_RESULT_PREFIX_REGEX.sub('', text)
	def get_queue_task(self, player: str) -> Optional[QueueTask]:
		with self.queue_lock:
			return self.work_queue.get(player)

	def get_or_create_queue_task(self, player: str) -> QueueTask:
		with self.queue_lock:
			if player not in self.work_queue:
				self.work_queue[player] = self.QueueTask()
			return self.work_queue[player]

	def get_player_info(self, player: str, path: str, timeout: float):
		if self.server.is_on_executor_thread():
			raise RuntimeError('Cannot invoke get_player_info on the task executor thread')
		if len(path) >= 1 and not path.startswith(' '):
			path = ' ' + path
		command = 'data get entity {}{}'.format(player, path)
		task = self.get_or_create_queue_task(player)
		task.count += 1
		try:
			self.server.execute(command)
			content = task.queue.get(timeout=timeout)
		except Empty:
			self.server.logger.warning('Query for player {} at path {} timeout'.format(player, path))
			return None
		finally:
			task.count -= 1
		return self.remove_command_result_prefix(content)

	__ENTITY_DATE_REGEX = re.compile(r'^\w+ has the following entity data: .*$')

	def on_info(self, info: Info):
		if not info.is_user:
			if self.__ENTITY_DATE_REGEX.match(info.content):
				player = info.content.split(' ')[0]
				task = self.get_queue_task(player)
				if task is not None and task.count > 0:
					task.queue.put(info.content)
