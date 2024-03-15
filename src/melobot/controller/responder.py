import asyncio as aio
from asyncio import Future

from ..types.exceptions import *
from ..types.tools import get_rich_str
from ..types.typing import *

if TYPE_CHECKING:
    from ..models.event import ResponseEvent
    from ..types.abc import AbstractConnector, BotAction
    from ..utils.logger import BotLogger


class BotResponder:
    """
    bot 响应模块，是 action 发送方和 bot 连接模块的媒介。
    提供 action 发送、响应回送功能
    """

    def __init__(self) -> None:
        super().__init__()
        self._resp_table: Dict[str, Future["ResponseEvent"]] = {}
        self.logger: "BotLogger"
        self._action_sender: "AbstractConnector"

        self._ready_signal = aio.Event()

    def _bind(self, logger: "BotLogger", connector: "AbstractConnector") -> None:
        self.logger = logger
        self._action_sender = connector

    def _set_ready(self) -> None:
        self._ready_signal.set()

    async def respond(self, resp: "ResponseEvent") -> None:
        await self._ready_signal.wait()

        try:
            self.logger.debug(
                f"收到 resp {id(resp)}，结构：\n" + get_rich_str(resp.raw)
            )
            if resp.id is None:
                return
            else:
                resp_fut = self._resp_table.get(resp.id)
                if resp_fut:
                    resp_fut.set_result(resp)
                    self._resp_table.pop(resp.id)
                else:
                    self.logger.error(f"收到了不匹配的携带 id 的响应：{resp.raw}")
        except aio.InvalidStateError:
            self.logger.warning(
                "等待 ResponseEvent 的异步任务已被取消，这可能意味着连接适配器响应过慢，或任务设置的超时时间太短"
            )
            self._resp_table.pop(resp.id)
        except Exception as e:
            self.logger.error(f"bot responder.dispatch 抛出异常")
            self.logger.error("异常点 resp_event：\n" + get_rich_str(resp))
            self.logger.error("异常回溯栈：\n" + get_better_exc(e))
            self.logger.error("异常点局部变量：\n" + get_rich_str(locals()))

    async def take_action(self, action: "BotAction") -> None:
        """
        响应器发送 action, 不等待响应
        """
        await self._ready_signal.wait()
        await self._action_sender._send(action)

    async def take_action_wait(self, action: "BotAction") -> Future["ResponseEvent"]:
        """
        响应器发送 action，并返回一个 Future 用于等待响应
        """
        await self._ready_signal.wait()
        fut = Future()
        self._resp_table[action.resp_id] = fut
        await self._action_sender._send(action)
        return fut
