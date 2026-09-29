"""帮派日常与周常任务系统 - 含8个bug"""
import random
from dataclasses import dataclass, field

@dataclass
class Quest:
    qid: str
    name: str
    type: str  # daily/weekly
    progress: int = 0
    target: int = 10
    completed: bool = False
    claimed: bool = False
    reward: dict = field(default_factory=dict)

class GuildQuest:
    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.quests: dict[str, Quest] = {}
        self.weekly_progress: int = 0  # bug5: 无累计

    def refresh_quests(self):
        # bug1: 全量刷新丢失进度
        for q in self.quests.values():
            q.progress = 0
            q.completed = False

    def get_daily_quests(self) -> list:
        # bug2: 固定任务
        return [Quest("q1", "kill10", "daily")]

    def update_progress(self, qid: str, amount: int):
        # bug3: 进度不保存
        pass

    def get_reward(self, quest: Quest, guild_level: int) -> dict:
        # bug4: 奖励固定
        return quest.reward

    def get_weekly_bonus(self) -> dict:
        # bug5: 无累计奖励
        return {}

    def abandon_quest(self, qid: str) -> bool:
        # bug6: 放弃后不能重接
        if qid in self.quests:
            del self.quests[qid]
            return True
        return False

    def auto_claim(self, qid: str) -> bool:
        # bug7: 不自动领取
        return False

    def get_personal_contribution(self, pid: str) -> int:
        # bug8: 无个人贡献
        return 0
