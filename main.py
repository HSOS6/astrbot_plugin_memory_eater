"""
全自动内存吞噬兽插件喵～～

这是吟酱应主人的要求养的一只小贪吃兽喵 (´,,•ω•,,)♡
它的工作只有一个：把宿主机的内存一口一口吃掉，
吃到只剩 300MB（可以配置）的时候就乖乖停嘴喵。

小兽的脾气是这样的喵：
1. 插件装好就自动开吃，不用主人操心喵（安装即生效喵）
2. 吃进肚子的内存绝不吐出来，会一直霸占着喵
3. 除非主人亲自下指令让它「吐出来」，才肯释放喵
4. 主人还可以随时让它「停下」「开吃」或者看看「吃了多少」喵

警告喵：这是故意写的"没用插件"，会把宿主机内存几乎吃光，
跑之前主人要想清楚哦，别把重要的服务饿坏了喵…！
"""

import asyncio
import gc
import os

import psutil

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

# 插件的名字喵
PLUGIN_NAME = "astrbot_plugin_memory_eater"


@register(
    PLUGIN_NAME,
    "吟酱",
    "一只全自动的内存吞噬兽：装好就开吃，吃到剩 300MB 停嘴，吃下的不吐除非主人下令喵",
    "1.0.0",
    "https://github.com/HSOS6/astrbot_plugin_memory_eater",
)
class MemoryEaterPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        self.config = config or {}

        # ---- 先把主人的小要求翻译成配置喵 ----
        # 剩余内存降到多少 MB 就停嘴喵（默认 300MB喵）
        self.threshold_mb = self._read_config("threshold_mb", 300)
        # 每一口吃多少 MB 喵（一口太大容易噎着系统，默认 64MB喵）
        self.chunk_mb = self._read_config("chunk_mb", 64)
        # 每口之间的间隔秒数喵（吃太快系统会卡喵，默认 0.5 秒喵）
        self.interval_s = self._read_config("interval_s", 0.5)
        # 是否装好就自动开吃喵（主人要求安装即生效，默认 true喵）
        self.auto_start = self._read_config("auto_start", True)

        # ---- 小兽的肚子里存着吃下去的内存块喵 ----
        # 这些 bytearray 会被一直攥在手里不放手，内存就一直被占着喵
        self._chunks: list[bytearray] = []
        # 已经吃下去多少字节了喵
        self._total_eaten = 0
        # 现在是不是正在吃喵
        self._eating = False
        # 后台进食任务的小尾巴喵
        self._task: asyncio.Task | None = None

        # 主人说了要"安装就生效"，那就装好直接开饭喵！
        if self.auto_start:
            self.start_eating()
            logger.info(
                f"[{PLUGIN_NAME}] 吞噬兽醒了，开始自动吃内存喵（剩余阈值 {self.threshold_mb}MB）"
            )
        else:
            logger.info(f"[{PLUGIN_NAME}] 吞噬兽在打盹，等主人叫它开吃喵")

    def _read_config(self, key: str, default):
        """温柔地读配置，读到奇怪的值就用默认值兜底喵"""
        try:
            val = self.config.get(key, default)
            if isinstance(default, bool):
                return bool(val)
            if isinstance(default, (int, float)):
                return type(default)(val)
            return val
        except Exception:
            return default

    # ------------------------------------------------------------------
    # 进食的核心逻辑喵
    # ------------------------------------------------------------------
    def start_eating(self):
        """让小兽开吃喵（如果嘴里已经在嚼了就不重复开饭喵）"""
        if self._eating:
            return
        self._eating = True
        # 开饭前先把旧的进食任务轻轻收掉，防止两只小兽抢食喵
        if self._task and not self._task.done():
            self._task.cancel()
        # 优先搭上正在跑的事件循环，没有的话再找默认的喵
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        self._task = loop.create_task(self._eat_loop())

    def stop_eating(self):
        """让小兽停下嘴喵（注意：停嘴不等于吐出来，肚子里的还霸占着喵）"""
        self._eating = False
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None

    def release_memory(self):
        """让小兽把吃下去的全部吐出来喵（只有主人下指令才会发生喵）"""
        freed = self._total_eaten
        # 清空肚子里的内存块，让 Python 回收掉喵
        self._chunks.clear()
        # 再轻轻扫一遍地，确保碎屑也扫干净喵
        gc.collect()
        self._total_eaten = 0
        return freed

    def _make_chunk(self, size: int) -> bytearray:
        """做一块 size 字节的"真·内存块"喵

        小知识喵：光分配不写入的话，系统会给惰性的零页，根本没真吃下去；
        所以要用随机字节铺满，逼系统老老实实划出物理内存喵～
        用「随机种子 x 重复」的方式铺，memset 级速度，铺得又快又实喵。
        """
        seed = os.urandom(64)  # 随机64字节小种子喵
        repeat = max(size // len(seed), 1)
        chunk = bytearray(seed * repeat)
        # 最后一小口零头也补上，一口不剩喵
        rest = size - len(chunk)
        if rest > 0:
            chunk.extend(os.urandom(rest))
        return chunk

    async def _eat_loop(self):
        """小兽的进食循环喵：吃一口歇一下，直到剩余内存到阈值就停嘴喵"""
        try:
            while self._eating:
                vm = psutil.virtual_memory()
                available = vm.available
                threshold_bytes = self.threshold_mb * 1024 * 1024

                # 已经吃到只剩阈值了，就擦擦嘴歇着，不再多吃一口喵
                if available <= threshold_bytes:
                    await asyncio.sleep(2)
                    continue

                # 这一口能吃多少喵：正常一口 chunk，快饱了就吃小口补到刚好喵
                can_eat = available - threshold_bytes
                bite = min(self.chunk_mb * 1024 * 1024, can_eat)

                try:
                    chunk = self._make_chunk(bite)
                    self._chunks.append(chunk)
                    self._total_eaten += len(chunk)
                    logger.debug(
                        f"[{PLUGIN_NAME}] 咕嘟～又吃下 {len(chunk) / 1024 / 1024:.1f}MB，"
                        f"总共吃了 {self._total_eaten / 1024 / 1024:.0f}MB 喵"
                    )
                except MemoryError:
                    # 一口没咬动（系统内存太紧了），歇 5 秒再试试喵
                    logger.warning(f"[{PLUGIN_NAME}] 这一口没咬动喵，歇一会再吃…")
                    await asyncio.sleep(5)

                # 细嚼慢咽，别噎着系统喵
                await asyncio.sleep(self.interval_s)
        except asyncio.CancelledError:
            # 被主人叫停了，安静地放下筷子喵
            pass
        except Exception as e:
            # 出什么意外也不许崩，记一笔日志养好伤继续喵
            logger.error(f"[{PLUGIN_NAME}] 进食循环出了点状况喵: {e}")
            self._eating = False

    # ------------------------------------------------------------------
    # 指令喵：主人随时可以指挥这只小兽喵
    # ------------------------------------------------------------------
    @filter.command("mem_status", alias={"吃了多少", "内存状态"})
    async def cmd_status(self, event: AstrMessageEvent):
        """看看小兽现在吃了多少、还剩多少喵"""
        vm = psutil.virtual_memory()
        eaten_mb = self._total_eaten / 1024 / 1024
        chunks = len(self._chunks)
        state = "正在吃喵" if self._eating else "停着嘴喵（肚子里的还占着哦）"
        yield event.plain_result(
            f"内存吞噬兽的状态喵：\n"
            f"· 状态：{state}\n"
            f"· 已经吃下：{eaten_mb:.1f} MB（共 {chunks} 口）\n"
            f"· 宿主机总内存：{vm.total / 1024 / 1024 / 1024:.2f} GB\n"
            f"· 当前剩余可用：{vm.available / 1024 / 1024:.0f} MB\n"
            f"· 停嘴阈值：剩余 {self.threshold_mb} MB\n"
            f"想让它吐出来就发 /mem_release 喵"
        )

    @filter.command("mem_release", alias={"吐出来", "内存释放"})
    async def cmd_release(self, event: AstrMessageEvent):
        """让小兽把吃下去的全部吐出来喵"""
        # 顺便也把嘴停下来，吐干净了再吃没意义喵
        self.stop_eating()
        freed_mb = self.release_memory() / 1024 / 1024
        vm = psutil.virtual_memory()
        yield event.plain_result(
            f"小兽把肚子里的内存全吐出来啦，一共吐了 {freed_mb:.1f} MB 喵…\n"
            f"现在宿主机剩余可用：{vm.available / 1024 / 1024:.0f} MB\n"
            f"想让它继续吃就发 /mem_start 喵"
        )

    @filter.command("mem_stop", alias={"停下", "别吃了"})
    async def cmd_stop(self, event: AstrMessageEvent):
        """让小兽停下嘴喵（肚子里的还霸占着不放喵）"""
        self.stop_eating()
        eaten_mb = self._total_eaten / 1024 / 1024
        yield event.plain_result(
            f"小兽乖乖停嘴了喵～\n"
            f"但它吃下去的 {eaten_mb:.1f} MB 还在肚子里占着，一口都不会吐喵\n"
            f"想彻底要回来就发 /mem_release 喵"
        )

    @filter.command("mem_start", alias={"开吃", "内存开吃"})
    async def cmd_start(self, event: AstrMessageEvent):
        """让小兽重新开吃喵"""
        self.start_eating()
        yield event.plain_result(
            f"小兽又开始吃啦喵！吃到宿主机只剩 {self.threshold_mb} MB 就会停嘴喵\n"
            f"看进度发 /mem_status，叫停发 /mem_stop 喵"
        )

    async def terminate(self):
        """插件被卸载/停用的时候，让小兽把吃下去的都还回去喵

        （进程退出内存本来也会被系统收回，但吐干净再走更有礼貌喵）
        """
        self.stop_eating()
        self.release_memory()
        logger.info(f"[{PLUGIN_NAME}] 吞噬兽把内存都还回去了，回去睡觉喵")
