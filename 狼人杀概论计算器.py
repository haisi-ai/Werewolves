"""
狼人杀概论计算器 v1.0
优化版本：模块化设计 + NumPy加速
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from tkinter import filedialog
import random
from collections import defaultdict
import math
import webbrowser
import json
import os
import datetime
import re
import time
import numpy as np
from typing import Dict, List, Set, Tuple, Optional, Any


class GameConfig:
    """游戏配置类 - 管理游戏基本设置"""

    def __init__(self, total_players=12, wolves=4, gods=4, villagers=4):
        self.total_players = total_players
        self.wolves = wolves
        self.gods = gods
        self.villagers = villagers
        self.players = list(range(1, total_players + 1))

        # 三角形分组
        self.triangles = {
            "🔺159": {1, 5, 9},
            "🔺2610": {2, 6, 10},
            "🔺3711": {3, 7, 11},
            "🔺4812": {4, 8, 12}
        }

        # 三角形之间的对角关系
        self.triangle_opposites = {
            "🔺159": "🔺3711",
            "🔺2610": "🔺4812",
            "🔺3711": "🔺159",
            "🔺4812": "🔺2610"
        }

        # 四角分组
        self.corner_groups = [
            {"name": "🔲四角1", "players": {1, 7, 4, 10}},
            {"name": "🔲四角2", "players": {2, 8, 5, 11}},
            {"name": "🔲四角3", "players": {3, 9, 6, 12}}
        ]

        # 三行分组
        self.rows = [
            {1, 7}, {2, 8}, {3, 9}, {4, 10}, {5, 11}, {6, 12}
        ]
        self.row_combinations = [
            {"name": "行1-3", "players": self.rows[0] | self.rows[1] | self.rows[2]},
            {"name": "行2-4", "players": self.rows[1] | self.rows[2] | self.rows[3]},
            {"name": "行3-5", "players": self.rows[2] | self.rows[3] | self.rows[4]},
            {"name": "行4-6", "players": self.rows[3] | self.rows[4] | self.rows[5]},
            {"name": "行5-6+1", "players": self.rows[4] | self.rows[5] | self.rows[0]},
            {"name": "行6+1-2", "players": self.rows[5] | self.rows[0] | self.rows[1]}
        ]

    def get_player_triangle(self, player: int) -> str:
        """获取玩家所在的三角形"""
        for tri_name, tri_players in self.triangles.items():
            if player in tri_players:
                return tri_name
        return "未知"

    @staticmethod
    def get_total_combinations() -> int:
        """获取总组合数 C(12,4)"""
        return 495

    @staticmethod
    def get_double_wolf_prob() -> float:
        """获取至少一组双狼的概率"""
        return 1 - 81 / 495  # 约 83.64%


class ThemeManager:
    """主题管理类 - 管理深浅色主题"""

    THEMES = {
        "浅色": {
            'bg': '#f0f0f0',
            'fg': '#000000',
            'select': '#e0e0e0',
            'button': '#d9d9d9',
            'button_hover': '#c0c0c0',
            'frame_bg': '#ffffff',
            'tree_bg': '#ffffff',
            'tree_fg': '#000000',
            'tree_select': '#c0c0c0',
            'accent': '#ff4444',
            'wolf': '#cc0000',
            'god': '#9933cc',
            'human': '#008800',
            'gold': '#b8860b',
            'entry_bg': '#ffffff',
            'entry_fg': '#000000',
            'player_bg': '#e6e6e6',
            'player_border': '#cccccc',
            'custom_tag': '#9933cc'
        },
        "深色": {
            'bg': '#2b2b2b',
            'fg': '#ffffff',
            'select': '#404040',
            'button': '#3c3c3c',
            'button_hover': '#4a4a4a',
            'frame_bg': '#333333',
            'tree_bg': '#2d2d2d',
            'tree_fg': '#ffffff',
            'tree_select': '#4a4a4a',
            'accent': '#ff6b6b',
            'wolf': '#ff4757',
            'god': '#1e90ff',
            'human': '#2ecc71',
            'gold': '#ffd700',
            'entry_bg': '#404040',
            'entry_fg': '#ffffff',
            'player_bg': '#3a3a3a',
            'player_border': '#555555',
            'custom_tag': '#b266ff'
        }
    }

    def __init__(self):
        self.current_theme = "浅色"
        self.colors = self.THEMES[self.current_theme].copy()

    def toggle(self) -> Dict:
        """切换主题"""
        self.current_theme = "深色" if self.current_theme == "浅色" else "浅色"
        self.colors = self.THEMES[self.current_theme].copy()
        return self.colors

    def get_colors(self) -> Dict:
        return self.colors

    def apply_to_style(self, style: ttk.Style):
        """应用主题到ttk样式"""
        style.theme_use('clam')

        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('TLabelframe', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('TLabelframe.Label', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('TButton', background=self.colors['button'], foreground=self.colors['fg'],
                        borderwidth=1, focusthickness=3, focuscolor='none')
        style.map('TButton',
                  background=[('active', self.colors['button_hover']),
                              ('pressed', self.colors['select'])])
        style.configure('TCombobox', fieldbackground=self.colors['entry_bg'],
                        foreground=self.colors['entry_fg'], background=self.colors['entry_bg'])
        style.configure('TSpinbox', fieldbackground=self.colors['entry_bg'],
                        foreground=self.colors['entry_fg'], background=self.colors['entry_bg'])

        # 自定义按钮样式
        style.configure('Accent.TButton', background=self.colors['accent'], foreground='white')
        style.map('Accent.TButton',
                  background=[('active', '#ff5252'), ('pressed', '#ff3838')])

        style.configure('Wolf.TButton', background=self.colors['wolf'], foreground='white')
        style.configure('God.TButton', background=self.colors['god'], foreground='white')
        style.configure('Human.TButton', background=self.colors['human'], foreground='white')
        style.configure('CustomTag.TButton', background=self.colors['custom_tag'], foreground='white')


class RoleManager:
    """身份管理类 - 管理所有身份和标签"""

    def __init__(self):
        # 身份分类
        self.role_categories = {
            "好人标记": {
                "金水": "good_mark", "银水": "good_mark", "铜水": "good_mark",
                "爆水": "good_mark", "花露水": "good_mark", "贴脸": "good_mark",
                "离线": "good_mark", "反金": "good_mark", "好人": "good_mark",
            },
            "狼人": {
                "狼人": "wolf", "狼王": "wolf", "白狼王": "wolf", "狼美人": "wolf",
                "石像鬼": "wolf", "赤月使徒": "wolf", "咒狐": "wolf", "噩梦之影": "wolf",
                "蚀时狼妃": "wolf", "狼巫": "wolf", "狼鸦之爪": "wolf", "蚀日侍女": "wolf",
                "寂夜导师": "wolf", "夜之贵族": "wolf", "寻香魅影": "wolf",
                "觉醒狼王": "wolf", "觉醒隐狼": "wolf", "隐狼": "wolf",
                "恶夜骑士": "wolf", "悍跳狼": "wolf",
            },
            "神职": {
                "预言家": "god", "女巫": "god", "猎人": "god", "愚者": "god",
                "守卫": "god", "摄梦人": "god", "魔术师": "god", "骑士": "god",
                "守墓人": "god", "猎魔人": "god", "乌鸦": "god", "奇迹商人": "god",
                "定序王子": "god", "纯白之女": "god", "炼金魔女": "god", "熊": "god",
                "子狐": "god", "河豚": "god", "白猫": "god", "白昼学者": "god",
                "流光伯爵": "god", "觉醒愚者": "god", "觉醒预言家": "god", "魔镜少女": "god",
            },
            "平民": {
                "平民": "human", "羊驼": "human", "孤独少女": "human",
                "千面人": "human", "丘比特": "human",
            }
        }

        # 自定义标签
        self.custom_tags = {
            # 狼面较大类
            "🔪 听杀": {"wolf": 2.1, "god": 0.4, "human": 0.5},
            "🔪 发言爆匪": {"wolf": 2.2, "god": 0.4, "human": 0.4},
            "👑 狼王逻辑": {"wolf": 2.5, "god": 0.3, "human": 0.2},
            "🔄 倒钩发言": {"wolf": 1.8, "god": 0.6, "human": 0.6},
            "💀 匪事干尽": {"wolf": 2.4, "god": 0.3, "human": 0.3},
            "👁️ 狼人视角": {"wolf": 2.2, "god": 0.4, "human": 0.4},
            "🔄 反复横跳": {"wolf": 1.8, "god": 0.8, "human": 1.4},
            "🔪 抗推位": {"wolf": 2.0, "god": 0.5, "human": 1.5},
            "🎣 倒钩": {"wolf": 2.0, "god": 0.8, "human": 0.7},
            "🎭 拱火": {"wolf": 1.8, "god": 0.6, "human": 1.6},

            # 神面较大类
            "💬 发言很正": {"wolf": 0.3, "god": 2.2, "human": 1.5},
            "✅ 逻辑正确": {"wolf": 0.4, "god": 2.3, "human": 1.3},
            "🛡️ 像个身份": {"wolf": 0.3, "god": 2.4, "human": 1.3},
            "👑 强势带队": {"wolf": 0.8, "god": 2.1, "human": 1.1},
            "💎 铁神": {"wolf": 0.2, "god": 2.5, "human": 0.3},

            # 平民面较大类
            "😐 平平无奇": {"wolf": 1.2, "god": 0.8, "human": 2.0},
            "🤔 闭眼玩家": {"wolf": 1.0, "god": 0.9, "human": 2.1},
            "😴 挂机玩家": {"wolf": 1.1, "god": 0.7, "human": 2.2},
            "📝 跟票玩家": {"wolf": 1.2, "god": 0.9, "human": 1.9},
            "👂 听劝玩家": {"wolf": 1.0, "god": 1.0, "human": 2.0},
            "🤐 沉默": {"wolf": 1.1, "god": 1.2, "human": 1.7},
            "🌾 铁民": {"wolf": 0.3, "god": 0.3, "human": 2.4},
            "😴 划水": {"wolf": 1.5, "god": 0.8, "human": 0.7},

            # 中性类
            "🌟 全场乱打": {"wolf": 0.5, "god": 1.8, "human": 1.7},
            "🎲 全场乱打": {"wolf": 1.5, "god": 1.2, "human": 1.3},
            "🔍 疑似好人": {"wolf": 0.5, "god": 1.8, "human": 1.7},
            "💎 逻辑全错": {"wolf": 1.3, "god": 1.2, "human": 1.5},
            "🔄 跟风": {"wolf": 1.3, "god": 1.2, "human": 1.5},
            "🗣️ 话痨": {"wolf": 1.2, "god": 1.5, "human": 1.3},
            "😤 贴脸": {"wolf": 1.3, "god": 1.2, "human": 1.5},
            "💢 暴躁": {"wolf": 1.4, "god": 1.1, "human": 1.5},
            "❓ 身份不明": {"wolf": 1.0, "god": 1.0, "human": 1.0},
        }

        # 已知信息存储
        self.known_info = {}  # {player: {"role": role, "type": type, "category": category}}
        self.behavior_weights = {}  # {player: {"狼权": w, "神权": g, "民权": h}}

        # 所有身份列表
        self.all_roles = []
        for category, roles in self.role_categories.items():
            self.all_roles.extend(roles.keys())

    def get_role_type(self, role: str) -> str:
        """获取身份类型"""
        for category, roles in self.role_categories.items():
            if role in roles:
                if category == "好人标记":
                    return "good_mark"
                elif category == "狼人":
                    return "wolf"
                elif category == "神职":
                    return "god"
                elif category == "平民":
                    return "human"
        return "unknown"

    def add_known_info(self, player: int, role: str, category: str) -> Dict:
        """添加已知信息"""
        self.known_info[player] = {
            "role": role,
            "type": self.get_role_type(role),
            "category": category
        }
        return self.known_info[player]

    def remove_known_info(self, player: int) -> bool:
        """删除已知信息"""
        if player in self.known_info:
            del self.known_info[player]
            return True
        return False

    def add_behavior_weight(self, player: int, wolf: float, god: float, human: float) -> Dict:
        """添加行为权重"""
        self.behavior_weights[player] = {
            '狼权': wolf,
            '神权': god,
            '民权': human
        }
        return self.behavior_weights[player]

    def remove_behavior_weight(self, player: int) -> bool:
        """删除行为权重"""
        if player in self.behavior_weights:
            del self.behavior_weights[player]
            return True
        return False

    def get_remaining_counts(self, config: GameConfig) -> Tuple[int, int, int, int]:
        """获取剩余身份数量"""
        known_wolves = sum(1 for info in self.known_info.values() if info.get("type") == "wolf")
        known_gods = sum(1 for info in self.known_info.values() if info.get("type") == "god")
        known_humans = sum(1 for info in self.known_info.values() if info.get("type") == "human")
        known_marks = sum(1 for info in self.known_info.values() if info.get("type") == "good_mark")

        remaining_wolves = config.wolves - known_wolves
        remaining_gods = config.gods - known_gods
        remaining_humans = config.villagers - known_humans

        return remaining_wolves, remaining_gods, remaining_humans, known_marks

    def clear_all(self):
        """清空所有信息"""
        self.known_info.clear()
        self.behavior_weights.clear()


class ProbabilityCalculator:
    """概率计算核心类 - 使用NumPy加速"""

    def __init__(self, config: GameConfig, role_manager: RoleManager):
        self.config = config
        self.role_manager = role_manager
        self.cache = {
            'triangle_weights': None,
            'last_state': None,
            'basic_probs': None
        }

    def _get_state_hash(self) -> str:
        """获取当前状态的哈希值，用于缓存判断"""
        info_str = str(sorted(self.role_manager.known_info.items()))
        weights_str = str(sorted(self.role_manager.behavior_weights.items()))
        return hash((info_str, weights_str))

    def calculate_triangle_weights(self) -> Dict[str, float]:
        """计算三角形权重（带缓存）"""
        current_state = self._get_state_hash()

        if (self.cache['triangle_weights'] is not None and
                self.cache['last_state'] == current_state):
            return self.cache['triangle_weights']

        triangle_weights = {}

        for tri_name, tri_players in self.config.triangles.items():
            known_wolves = 0
            known_good = 0
            unknown = []

            for player in tri_players:
                if player in self.role_manager.known_info:
                    info = self.role_manager.known_info[player]
                    role_type = info.get("type", "unknown")

                    if role_type == "wolf":
                        known_wolves += 1
                    else:
                        known_good += 1
                else:
                    unknown.append(player)

            if known_wolves == 2:
                triangle_weights[tri_name] = 0.1
            elif known_wolves == 1:
                triangle_weights[tri_name] = 2.0 if unknown else 0.5
            elif known_wolves == 0:
                triangle_weights[tri_name] = 1.8 if len(unknown) >= 2 else 1.0
            else:
                triangle_weights[tri_name] = 1.0

            # 好人太多的地方狼少
            if known_good >= 2:
                triangle_weights[tri_name] *= 0.7

            # 跳棋原则
            opposite_tri = self.config.triangle_opposites.get(tri_name)
            if opposite_tri and known_wolves == 2:
                if opposite_tri in triangle_weights:
                    triangle_weights[opposite_tri] *= 1.3

        self.cache['triangle_weights'] = triangle_weights
        self.cache['last_state'] = current_state
        return triangle_weights

    def monte_carlo_numpy(self, sim_count: int, progress_callback=None) -> Dict[int, Dict[str, float]]:
        """NumPy加速的蒙特卡洛模拟"""
        unknown_players = [p for p in self.config.players
                           if p not in self.role_manager.known_info]

        if not unknown_players:
            return {}

        n_unknown = len(unknown_players)
        remaining_wolves, remaining_gods, remaining_humans, known_marks = \
            self.role_manager.get_remaining_counts(self.config)

        # 处理好人标记的分配
        gods_to_add = remaining_gods
        humans_to_add = remaining_humans

        if known_marks > 0:
            # 使用NumPy随机生成好人标记分配
            marks_to_gods = np.random.binomial(known_marks, 0.5, sim_count)
            gods_matrix = remaining_gods + marks_to_gods
            humans_matrix = remaining_humans + (known_marks - marks_to_gods)
        else:
            gods_matrix = np.full(sim_count, remaining_gods)
            humans_matrix = np.full(sim_count, remaining_humans)

        # 初始化计数矩阵
        wolf_counts = np.zeros(n_unknown, dtype=np.int32)
        god_counts = np.zeros(n_unknown, dtype=np.int32)
        human_counts = np.zeros(n_unknown, dtype=np.int32)

        # 批量模拟
        batch_size = 10000
        n_batches = (sim_count + batch_size - 1) // batch_size

        for batch in range(n_batches):
            start = batch * batch_size
            end = min(start + batch_size, sim_count)
            current_batch = end - start

            # 为当前批次创建身份矩阵
            batch_wolves = np.zeros((current_batch, n_unknown), dtype=np.int32)
            batch_gods = np.zeros((current_batch, n_unknown), dtype=np.int32)
            batch_humans = np.zeros((current_batch, n_unknown), dtype=np.int32)

            for i in range(current_batch):
                # 构建身份池
                roles = ['狼人'] * remaining_wolves
                roles.extend(['神民'] * gods_matrix[start + i])
                roles.extend(['平民'] * humans_matrix[start + i])
                np.random.shuffle(roles)

                # 分配
                for j, role in enumerate(roles):
                    if role == '狼人':
                        batch_wolves[i, j] = 1
                    elif role == '神民':
                        batch_gods[i, j] = 1
                    else:
                        batch_humans[i, j] = 1

            # 累加计数
            wolf_counts += np.sum(batch_wolves, axis=0)
            god_counts += np.sum(batch_gods, axis=0)
            human_counts += np.sum(batch_humans, axis=0)

            if progress_callback:
                progress_callback(int((end / sim_count) * 100))

        # 计算概率
        results = {}
        for idx, player in enumerate(unknown_players):
            results[player] = {
                '狼人': wolf_counts[idx] / sim_count,
                '神民': god_counts[idx] / sim_count,
                '平民': human_counts[idx] / sim_count
            }

        return results

    def triangle_law_simulation(self, sim_count: int, progress_callback=None) -> Dict[int, Dict[str, float]]:
        """三角定律模拟（带权重）"""
        unknown_players = [p for p in self.config.players
                           if p not in self.role_manager.known_info]

        if not unknown_players:
            return {}

        n_unknown = len(unknown_players)
        remaining_wolves, remaining_gods, remaining_humans, known_marks = \
            self.role_manager.get_remaining_counts(self.config)

        # 获取三角形权重
        triangle_weights = self.calculate_triangle_weights()

        # 初始化计数器
        wolf_counts = np.zeros(n_unknown, dtype=np.int32)
        god_counts = np.zeros(n_unknown, dtype=np.int32)
        human_counts = np.zeros(n_unknown, dtype=np.int32)

        batch_size = 5000
        n_batches = (sim_count + batch_size - 1) // batch_size

        for batch in range(n_batches):
            start = batch * batch_size
            end = min(start + batch_size, sim_count)
            current_batch = end - start

            for i in range(current_batch):
                # 处理好人标记分配
                gods_to_assign = remaining_gods
                humans_to_assign = remaining_humans

                if known_marks > 0:
                    gods_from_marks = random.randint(0, known_marks)
                    gods_to_assign += gods_from_marks
                    humans_to_assign += (known_marks - gods_from_marks)

                # 构建身份池
                identity_pool = (['狼人'] * remaining_wolves +
                                 ['神职'] * gods_to_assign +
                                 ['平民'] * humans_to_assign)
                random.shuffle(identity_pool)

                # 根据权重分配
                available = unknown_players.copy()
                assigned = {}

                # 先分配狼人（带权重）
                for _ in range(remaining_wolves):
                    if not available:
                        break

                    # 计算权重
                    weights = []
                    for player in available:
                        tri = self.config.get_player_triangle(player)
                        weight = triangle_weights.get(tri, 1.0)
                        if player in self.role_manager.behavior_weights:
                            weight *= self.role_manager.behavior_weights[player].get('狼权', 1.0)
                        weights.append(weight)

                    # 加权随机选择
                    total = sum(weights)
                    if total > 0:
                        probs = [w / total for w in weights]
                        chosen = random.choices(available, weights=probs)[0]
                    else:
                        chosen = random.choice(available)

                    assigned[chosen] = '狼人'
                    available.remove(chosen)

                # 分配其他身份
                for player in available:
                    if identity_pool:
                        assigned[player] = identity_pool.pop(0)

                # 统计
                for player, role in assigned.items():
                    idx = unknown_players.index(player)
                    if role == '狼人':
                        wolf_counts[idx] += 1
                    elif role == '神职':
                        god_counts[idx] += 1
                    else:
                        human_counts[idx] += 1

            if progress_callback:
                progress_callback(int((end / sim_count) * 100))

        # 计算概率
        results = {}
        for idx, player in enumerate(unknown_players):
            results[player] = {
                '狼人': wolf_counts[idx] / sim_count,
                '神职': god_counts[idx] / sim_count,
                '平民': human_counts[idx] / sim_count
            }

        return results

    def bayesian_update(self) -> Dict[int, Dict[str, float]]:
        """贝叶斯更新（解析解）"""
        unknown_players = [p for p in self.config.players
                           if p not in self.role_manager.known_info]

        if not unknown_players:
            return {}

        n_unknown = len(unknown_players)
        remaining_wolves, remaining_gods, remaining_humans, known_marks = \
            self.role_manager.get_remaining_counts(self.config)

        # 好人标记平均分配
        if known_marks > 0:
            gods_from_marks = known_marks // 2
            remaining_gods += gods_from_marks
            remaining_humans += (known_marks - gods_from_marks)

        # 基础先验概率
        base_wolf = remaining_wolves / n_unknown if n_unknown > 0 else 0
        base_god = remaining_gods / n_unknown if n_unknown > 0 else 0
        base_human = remaining_humans / n_unknown if n_unknown > 0 else 0

        # 三角形权重
        triangle_weights = self.calculate_triangle_weights()

        results = {}
        for player in unknown_players:
            wolf_prob = base_wolf
            god_prob = base_god
            human_prob = base_human

            # 三角形调整
            tri = self.config.get_player_triangle(player)
            tri_weight = triangle_weights.get(tri, 1.0)
            wolf_prob *= tri_weight

            # 归一化
            total = wolf_prob + god_prob + human_prob
            if total > 0:
                wolf_prob /= total
                god_prob /= total
                human_prob /= total

            # 行为权重贝叶斯更新
            if player in self.role_manager.behavior_weights:
                weights = self.role_manager.behavior_weights[player]
                wolf_w = weights.get('狼权', 1.0)
                god_w = weights.get('神权', 1.0)
                human_w = weights.get('民权', 1.0)

                total_w = wolf_w + god_w + human_w
                if total_w > 0:
                    # 似然因子
                    wolf_like = wolf_w / (total_w / 3)
                    god_like = god_w / (total_w / 3)
                    human_like = human_w / (total_w / 3)

                    # 贝叶斯更新
                    new_wolf = wolf_prob * wolf_like
                    new_god = god_prob * god_like
                    new_human = human_prob * human_like

                    total_new = new_wolf + new_god + new_human
                    if total_new > 0:
                        wolf_prob = new_wolf / total_new
                        god_prob = new_god / total_new
                        human_prob = new_human / total_new

            results[player] = {
                '狼人': wolf_prob,
                '神职': god_prob,
                '平民': human_prob
            }

        return results

    def comprehensive_analysis(self, sim_count: int,
                               use_triangle: bool = True,
                               use_weight: bool = True,
                               progress_callback=None) -> Dict[int, Dict[str, float]]:
        """综合分析 - 融合多种算法"""
        unknown_players = [p for p in self.config.players
                           if p not in self.role_manager.known_info]

        if not unknown_players:
            return {}

        # 获取各算法结果
        mc_results = self.monte_carlo_numpy(sim_count // 3,
                                            lambda p: progress_callback(p // 3) if progress_callback else None)

        triangle_results = {}
        if use_triangle:
            triangle_results = self.triangle_law_simulation(sim_count // 3,
                                                            lambda p: progress_callback(
                                                                33 + p // 3) if progress_callback else None)

        bayes_results = {}
        if use_weight:
            bayes_results = self.bayesian_update()
            if progress_callback:
                progress_callback(66)

        # 融合权重
        results = {}
        for player in unknown_players:
            mc_score = mc_results.get(player, {}).get('狼人', 0.25)
            tri_score = triangle_results.get(player, {}).get('狼人', 0.25) if use_triangle else 0.25
            bayes_score = bayes_results.get(player, {}).get('狼人', 0.25) if use_weight else 0.25

            # 加权平均
            wolf_prob = (mc_score * 0.4 + tri_score * 0.3 + bayes_score * 0.3)

            results[player] = {
                '狼人': wolf_prob,
                '神民': mc_score,
                '平民': bayes_score
            }

        if progress_callback:
            progress_callback(100)

        return results

    def calculate_triangle_distribution(self, num_simulations=100000) -> Dict[str, float]:
        """计算三角形分布概率"""
        wolves_array = np.zeros((num_simulations, 4), dtype=np.int32)

        for i in range(num_simulations):
            wolves = set(random.sample(self.config.players, self.config.wolves))
            for j, tri in enumerate(self.config.triangles.values()):
                wolves_array[i, j] = len(wolves.intersection(tri))

        case1 = np.sum((np.sum(wolves_array == 2, axis=1) == 2) &
                       (np.sum(wolves_array == 0, axis=1) == 2))
        case2 = np.sum((np.sum(wolves_array == 2, axis=1) == 1) &
                       (np.sum(wolves_array == 1, axis=1) == 2))
        case3 = np.sum(np.all(wolves_array == 1, axis=1))
        case4 = np.sum(np.any(wolves_array >= 3, axis=1))

        return {
            "两个三角各2狼": case1 / num_simulations,
            "一三角2狼+两三角1狼": case2 / num_simulations,
            "四个三角各1狼": case3 / num_simulations,
            "一三角有3狼": case4 / num_simulations
        }

    def calculate_row_probability(self, num_simulations=100000) -> float:
        """计算三行定律概率"""
        case_count = 0

        for _ in range(num_simulations):
            wolves = set(random.sample(self.config.players, self.config.wolves))
            for combo in self.config.row_combinations:
                if len(wolves.intersection(combo["players"])) >= 3:
                    case_count += 1
                    break

        return case_count / num_simulations

    def calculate_corner_probabilities(self, num_simulations=100000) -> Dict[int, float]:
        """计算四角定律概率"""
        counts = {4: 0, 3: 0, 2: 0, 1: 0}

        for _ in range(num_simulations):
            wolves = set(random.sample(self.config.players, self.config.wolves))
            for group in self.config.corner_groups:
                count = len(wolves.intersection(group["players"]))
                if count >= 1:
                    counts[count] += 1

        total = num_simulations * len(self.config.corner_groups)
        return {k: v / total for k, v in counts.items()}


class PlayerCard:
    """玩家卡片组件"""

    def __init__(self, parent, player_num, colors, click_callback):
        self.player_num = player_num
        self.colors = colors
        self.click_callback = click_callback

        # 创建卡片框架
        self.frame = tk.Frame(parent, bg=colors['player_bg'],
                              relief=tk.RAISED, borderwidth=2)
        self.frame.pack(fill=tk.X, pady=5, ipadx=10, ipady=5)

        self._create_widgets()
        self._bind_events()

    def _create_widgets(self):
        """创建卡片内的组件"""
        # 上部
        top_frame = tk.Frame(self.frame, bg=self.colors['player_bg'])
        top_frame.pack(fill=tk.X, padx=5, pady=2)

        left_frame = tk.Frame(top_frame, bg=self.colors['player_bg'])
        left_frame.pack(side=tk.LEFT)

        # 号码牌
        num_frame = tk.Frame(left_frame, bg=self.colors['player_border'],
                             width=40, height=40)
        num_frame.pack(side=tk.LEFT, padx=2)
        num_frame.pack_propagate(False)

        self.num_label = tk.Label(num_frame, text=str(self.player_num),
                                  bg=self.colors['player_border'],
                                  fg=self.colors['fg'],
                                  font=("微软雅黑", 12, "bold"))
        self.num_label.pack(expand=True, fill=tk.BOTH)

        # 身份图标
        self.icon_label = ttk.Label(left_frame, text="❓", font=("微软雅黑", 14))
        self.icon_label.pack(side=tk.LEFT, padx=5)

        # 身份名称
        self.role_label = ttk.Label(top_frame, text="未知", font=("微软雅黑", 10))
        self.role_label.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

        # 概率显示区域
        prob_frame = tk.Frame(self.frame, bg=self.colors['player_bg'])
        prob_frame.pack(fill=tk.X, padx=5, pady=2)

        # 狼人概率
        wolf_frame = tk.Frame(prob_frame, bg=self.colors['player_bg'])
        wolf_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.wolf_label = tk.Label(wolf_frame, text="🐺0%",
                                   bg=self.colors['player_bg'],
                                   fg=self.colors['wolf'],
                                   font=("微软雅黑", 8))
        self.wolf_label.pack()

        # 神职概率
        god_frame = tk.Frame(prob_frame, bg=self.colors['player_bg'])
        god_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.god_label = tk.Label(god_frame, text="👼0%",
                                  bg=self.colors['player_bg'],
                                  fg=self.colors['god'],
                                  font=("微软雅黑", 8))
        self.god_label.pack()

        # 平民概率
        human_frame = tk.Frame(prob_frame, bg=self.colors['player_bg'])
        human_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.human_label = tk.Label(human_frame, text="👤0%",
                                    bg=self.colors['player_bg'],
                                    fg=self.colors['human'],
                                    font=("微软雅黑", 8))
        self.human_label.pack()

    def _bind_events(self):
        """绑定事件"""
        widgets = [self.frame, self.num_label, self.icon_label, self.role_label]
        for widget in widgets:
            widget.bind('<Button-1>', lambda e: self.click_callback(self.player_num))
            widget.bind('<Enter>', lambda e: widget.config(cursor="hand2"))
            widget.bind('<Leave>', lambda e: widget.config(cursor=""))

    def update(self, known_info: Optional[Dict] = None):
        """更新卡片显示"""
        if known_info and self.player_num in known_info:
            info = known_info[self.player_num]
            role = info["role"]
            role_type = info["type"]

            if role_type == "wolf":
                color = self.colors['wolf']
                icon = "🐺"
            elif role_type == "god":
                color = self.colors['god']
                icon = "👼"
            elif role_type == "human":
                color = self.colors['human']
                icon = "👤"
            elif role_type == "good_mark":
                color = self.colors['gold']
                icon = "⭐"
            else:
                color = self.colors['player_bg']
                icon = "❓"

            self.frame.config(bg=color)
            for child in self.frame.winfo_children():
                if isinstance(child, tk.Frame):
                    child.config(bg=color)

            self.icon_label.config(text=icon)
            self.role_label.config(text=role)
        else:
            self.frame.config(bg=self.colors['player_bg'])
            for child in self.frame.winfo_children():
                if isinstance(child, tk.Frame):
                    child.config(bg=self.colors['player_bg'])

            self.icon_label.config(text="❓")
            self.role_label.config(text="未知")

    def set_probabilities(self, wolf: float, god: float, human: float):
        """设置概率显示"""
        self.wolf_label.config(text=f"🐺{wolf:.1%}")
        self.god_label.config(text=f"👼{god:.1%}")
        self.human_label.config(text=f"👤{human:.1%}")


class ProgressDialog:
    """进度对话框"""

    def __init__(self, parent, title="计算进度", message="正在计算..."):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("300x120")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 居中显示
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")

        # 消息标签
        self.msg_label = ttk.Label(self.dialog, text=message)
        self.msg_label.pack(pady=10)

        # 进度条
        self.progress = ttk.Progressbar(self.dialog, length=250, mode='determinate')
        self.progress.pack(pady=5)

        # 百分比标签
        self.percent_label = ttk.Label(self.dialog, text="0%")
        self.percent_label.pack()

        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
        self.cancelled = False

    def _on_close(self):
        self.cancelled = True
        self.dialog.destroy()

    def update(self, value: int):
        """更新进度"""
        if self.cancelled:
            return False
        self.progress['value'] = value
        self.percent_label.config(text=f"{value}%")
        self.dialog.update()
        return True

    def close(self):
        """关闭对话框"""
        self.dialog.destroy()


class WerewolfProbabilityApp:
    """狼人杀概论计算器主应用类"""

    def __init__(self, root):
        self.root = root
        self.root.title("狼人杀概论计算器 v1.0")
        self.root.geometry("1400x850")
        self.root.minsize(1200, 700)

        # 初始化核心组件
        self.theme_manager = ThemeManager()
        self.config = GameConfig()
        self.role_manager = RoleManager()
        self.calculator = ProbabilityCalculator(self.config, self.role_manager)

        # 模拟次数
        self.simulation_count = 50000

        # 算法开关
        self.use_triangle_law = True
        self.use_behavior_weight = True

        # UI组件存储
        self.player_cards = {}  # {player_num: PlayerCard}
        self.tree = None
        self.log_text = None
        self.triangle_status_text = None
        self.law_right_text = None

        # 发言记录
        self.speech_records = {}  # {(player, round): "发言内容"}

        # 设置UI
        self.setup_ui()

        # 初始化日志
        self.log("系统初始化完成 - 狼人杀概论计算器 v1.0")
        self.log("三角定律核心：85%概率必有一组三角形有双狼")
        self.log("欢迎使用！请选择身份信息开始计算")

    def setup_ui(self):
        """设置用户界面"""
        # 应用主题
        self.theme_manager.apply_to_style(ttk.Style())
        self.root.configure(bg=self.theme_manager.colors['bg'])

        # 创建主框架
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 左侧面板（信息输入）
        left_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(left_frame, weight=1)

        # 中间面板（结果显示 + 可视化号码牌）
        middle_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(middle_frame, weight=4)

        # 右侧面板（实时日志 + 基础定律 + 发言记录）
        right_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(right_frame, weight=2)

        # 创建工具栏
        self.create_toolbar()

        # 设置各个面板
        self.setup_left_panel(left_frame)
        self.setup_middle_panel(middle_frame)
        self.setup_right_panel(right_frame)

        # 创建状态栏
        self.create_status_bar()

    def create_toolbar(self):
        """创建顶部工具栏"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(toolbar, text="🎨 切换主题",
                   command=self.toggle_theme).pack(side=tk.LEFT, padx=2)

        ttk.Button(toolbar, text="💾 保存配置",
                   command=self.save_config).pack(side=tk.LEFT, padx=2)

        ttk.Button(toolbar, text="📂 加载配置",
                   command=self.load_config).pack(side=tk.LEFT, padx=2)

        ttk.Button(toolbar, text="🗑️ 清空所有信息",
                   command=self.clear_all).pack(side=tk.RIGHT, padx=2)

        ttk.Label(toolbar, text="v1.0", font=("微软雅黑", 8)).pack(side=tk.RIGHT, padx=10)

    def toggle_theme(self):
        """切换主题"""
        self.theme_manager.toggle()
        self.theme_manager.apply_to_style(ttk.Style())
        self.root.configure(bg=self.theme_manager.colors['bg'])

        # 更新所有卡片
        for card in self.player_cards.values():
            card.colors = self.theme_manager.colors
            card.update(self.role_manager.known_info)

        # 刷新UI颜色
        self.refresh_ui_colors()
        self.log(f"切换主题为: {self.theme_manager.current_theme}模式")

    def refresh_ui_colors(self):
        """递归刷新UI颜色"""

        def update_widget(widget):
            try:
                if isinstance(widget, tk.Text):
                    widget.config(bg=self.theme_manager.colors['entry_bg'],
                                  fg=self.theme_manager.colors['fg'],
                                  insertbackground=self.theme_manager.colors['fg'])
                elif isinstance(widget, tk.Listbox):
                    widget.config(bg=self.theme_manager.colors['entry_bg'],
                                  fg=self.theme_manager.colors['fg'],
                                  selectbackground=self.theme_manager.colors['tree_select'])
                elif isinstance(widget, tk.Canvas):
                    widget.config(bg=self.theme_manager.colors['bg'])
                elif isinstance(widget, tk.Frame) and widget not in [c.frame for c in self.player_cards.values()]:
                    widget.config(bg=self.theme_manager.colors['bg'])
            except:
                pass

            for child in widget.winfo_children():
                update_widget(child)

        update_widget(self.root)

    def setup_left_panel(self, parent):
        """设置左侧面板（信息输入）"""
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 身份输入页
        input_frame = ttk.Frame(notebook)
        notebook.add(input_frame, text="📝 身份输入")
        self.create_input_tab(input_frame)

        # 权重设置页
        weight_frame = ttk.Frame(notebook)
        notebook.add(weight_frame, text="⚖️ 权重设置")
        self.create_weight_tab(weight_frame)

        # 分析设置页
        setting_frame = ttk.Frame(notebook)
        notebook.add(setting_frame, text="⚙️ 分析设置")
        self.create_setting_tab(setting_frame)

    def create_input_tab(self, parent):
        """创建身份输入标签页"""
        canvas = tk.Canvas(parent, bg=self.theme_manager.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 玩家选择
        player_frame = ttk.Frame(scrollable_frame)
        player_frame.pack(fill=tk.X, pady=5)

        ttk.Label(player_frame, text="👤 玩家编号:", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.player_var = tk.StringVar()
        self.player_combo = ttk.Combobox(player_frame, textvariable=self.player_var,
                                         values=self.config.players, state="readonly", width=15)
        self.player_combo.pack(side=tk.LEFT, padx=10)
        self.player_combo.bind('<<ComboboxSelected>>', self.on_player_selected)

        # 身份分类选择
        self.role_notebook = ttk.Notebook(scrollable_frame)
        self.role_notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        self.role_vars = {}

        for category, roles in self.role_manager.role_categories.items():
            category_frame = ttk.Frame(self.role_notebook)
            self.role_notebook.add(category_frame, text=category)

            self.role_vars[category] = tk.StringVar()

            # 说明文字
            if category == "好人标记":
                ttk.Label(category_frame, text="⭐ 好人标记（可分配到神或民）",
                          foreground=self.theme_manager.colors['gold']).pack(anchor=tk.W, pady=5)
            elif category == "狼人":
                ttk.Label(category_frame, text="🐺 狼人阵营",
                          foreground=self.theme_manager.colors['wolf']).pack(anchor=tk.W, pady=5)
            elif category == "神职":
                ttk.Label(category_frame, text="👼 神职阵营",
                          foreground=self.theme_manager.colors['god']).pack(anchor=tk.W, pady=5)
            elif category == "平民":
                ttk.Label(category_frame, text="👤 平民阵营",
                          foreground=self.theme_manager.colors['human']).pack(anchor=tk.W, pady=5)

            btn_frame = ttk.Frame(category_frame)
            btn_frame.pack(fill=tk.BOTH, expand=True, pady=5)

            roles_list = list(roles.keys())
            for i, role in enumerate(roles_list):
                row, col = i // 3, i % 3

                if category == "狼人":
                    style = 'Wolf.TButton'
                elif category == "神职":
                    style = 'God.TButton'
                elif category == "平民":
                    style = 'Human.TButton'
                else:
                    style = 'TButton'

                rb = ttk.Radiobutton(btn_frame, text=role,
                                     variable=self.role_vars[category],
                                     value=role, style=style)
                rb.grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)

        # 添加按钮
        add_btn = ttk.Button(scrollable_frame, text="➕ 添加已知信息",
                             command=self.add_known_info,
                             style='Accent.TButton')
        add_btn.pack(pady=15)

        ttk.Label(scrollable_frame, text="提示: 选择玩家编号后，点击对应身份添加",
                  font=("微软雅黑", 9), foreground=self.theme_manager.colors['gold']).pack(pady=5)

        # 已知信息列表
        info_frame = ttk.LabelFrame(scrollable_frame, text="📋 当前已知信息", padding="5")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        list_frame = ttk.Frame(info_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.info_listbox = tk.Listbox(list_frame, height=6,
                                       bg=self.theme_manager.colors['entry_bg'],
                                       fg=self.theme_manager.colors['fg'],
                                       selectbackground=self.theme_manager.colors['tree_select'],
                                       font=("微软雅黑", 9))
        self.info_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar2 = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.info_listbox.yview)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_listbox.configure(yscrollcommand=scrollbar2.set)
        self.info_listbox.bind('<Double-Button-1>', lambda e: self.delete_selected_info())

        btn_frame2 = ttk.Frame(info_frame)
        btn_frame2.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame2, text="🗑️ 删除选中",
                   command=self.delete_selected_info).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame2, text="🔄 清空所有",
                   command=self.clear_all).pack(side=tk.LEFT, padx=2)

        self.info_stats = ttk.Label(info_frame, text="已知: 0 | 狼: 0 | 神: 0 | 民: 0 | 标记: 0",
                                    font=("微软雅黑", 8))
        self.info_stats.pack(fill=tk.X, pady=2)

    def create_weight_tab(self, parent):
        """创建权重设置标签页"""
        canvas = tk.Canvas(parent, bg=self.theme_manager.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(scrollable_frame, text="⚖️ 行为权重设置",
                  font=("微软雅黑", 12, "bold")).pack(pady=10)

        ttk.Label(scrollable_frame,
                  text="权重值 >1 表示倾向该身份，<1 表示不倾向\n建议范围: 0.1 - 3.0",
                  foreground=self.theme_manager.colors['gold']).pack(pady=5)

        # 玩家选择
        select_frame = ttk.Frame(scrollable_frame)
        select_frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(select_frame, text="选择玩家:").pack(side=tk.LEFT, padx=2)
        self.weight_player_var = tk.StringVar()
        self.weight_player_combo = ttk.Combobox(select_frame, textvariable=self.weight_player_var,
                                                values=self.config.players, state="readonly", width=8)
        self.weight_player_combo.pack(side=tk.LEFT, padx=2)

        ttk.Label(select_frame, text="标签:").pack(side=tk.LEFT, padx=(10, 2))
        self.tag_preset_var = tk.StringVar()
        tag_list = [""] + list(self.role_manager.custom_tags.keys())
        self.tag_preset_combo = ttk.Combobox(select_frame, textvariable=self.tag_preset_var,
                                             values=tag_list, state="readonly", width=15)
        self.tag_preset_combo.pack(side=tk.LEFT, padx=2)
        self.tag_preset_combo.bind('<<ComboboxSelected>>', self.on_tag_selected)

        # 权重输入
        weight_frame = ttk.LabelFrame(scrollable_frame, text="权重值", padding="10")
        weight_frame.pack(fill=tk.X, pady=10, padx=10)

        wolf_frame = ttk.Frame(weight_frame)
        wolf_frame.pack(fill=tk.X, pady=5)
        ttk.Label(wolf_frame, text="🐺 狼权:", foreground=self.theme_manager.colors['wolf'],
                  width=10).pack(side=tk.LEFT)
        self.wolf_weight = ttk.Entry(wolf_frame, width=20)
        self.wolf_weight.insert(0, "1.0")
        self.wolf_weight.pack(side=tk.LEFT, padx=5)

        god_frame = ttk.Frame(weight_frame)
        god_frame.pack(fill=tk.X, pady=5)
        ttk.Label(god_frame, text="👼 神权:", foreground=self.theme_manager.colors['god'],
                  width=10).pack(side=tk.LEFT)
        self.god_weight = ttk.Entry(god_frame, width=20)
        self.god_weight.insert(0, "1.0")
        self.god_weight.pack(side=tk.LEFT, padx=5)

        human_frame = ttk.Frame(weight_frame)
        human_frame.pack(fill=tk.X, pady=5)
        ttk.Label(human_frame, text="👤 民权:", foreground=self.theme_manager.colors['human'],
                  width=10).pack(side=tk.LEFT)
        self.human_weight = ttk.Entry(human_frame, width=20)
        self.human_weight.insert(0, "1.0")
        self.human_weight.pack(side=tk.LEFT, padx=5)

        self.tag_info_label = ttk.Label(scrollable_frame, text="", foreground=self.theme_manager.colors['gold'])
        self.tag_info_label.pack(fill=tk.X, pady=2, padx=10)

        # 按钮
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(fill=tk.X, pady=10, padx=10)

        apply_btn = ttk.Button(btn_frame, text="✅应用权重",
                               command=self.add_behavior_weight,
                               style='Accent.TButton')
        apply_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)

        save_tag_btn = ttk.Button(btn_frame, text="💾添加/保存标签",
                                  command=self.save_custom_tag,
                                  style='CustomTag.TButton')
        save_tag_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)

        delete_tag_btn = tk.Button(btn_frame, text="🗑️删除标签",
                                   command=self.delete_current_tag,
                                   bg='#ff4444', fg='white',
                                   font=("微软雅黑", 9),
                                   relief=tk.RAISED, borderwidth=1)
        delete_tag_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)

        # 权重列表
        weight_list_frame = ttk.LabelFrame(scrollable_frame, text="已设置权重", padding="5")
        weight_list_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)

        list_container = ttk.Frame(weight_list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)

        self.weight_listbox = tk.Listbox(list_container, height=6,
                                         bg=self.theme_manager.colors['entry_bg'],
                                         fg=self.theme_manager.colors['fg'],
                                         selectbackground=self.theme_manager.colors['tree_select'],
                                         font=("微软雅黑", 9))
        self.weight_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        weight_scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL,
                                         command=self.weight_listbox.yview)
        weight_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.weight_listbox.configure(yscrollcommand=weight_scrollbar.set)
        self.weight_listbox.bind('<<ListboxSelect>>', self.on_weight_selected)

        list_btn_frame = ttk.Frame(weight_list_frame)
        list_btn_frame.pack(fill=tk.X, pady=5)

        delete_selected_btn = ttk.Button(list_btn_frame, text="🗑️ 删除选中",
                                         command=self.delete_selected_weight)
        delete_selected_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)

        clear_btn = ttk.Button(list_btn_frame, text="🔄 清除所有",
                               command=self.clear_all_weights)
        clear_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)

    def create_setting_tab(self, parent):
        """创建设置标签页"""
        canvas = tk.Canvas(parent, bg=self.theme_manager.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(scrollable_frame, text="⚙️ 分析设置",
                  font=("微软雅黑", 12, "bold")).pack(pady=10)

        # 模拟次数
        sim_frame = ttk.LabelFrame(scrollable_frame, text="模拟次数", padding="10")
        sim_frame.pack(fill=tk.X, pady=10, padx=10)

        custom_frame = ttk.Frame(sim_frame)
        custom_frame.pack(fill=tk.X, pady=5)

        ttk.Label(custom_frame, text="模拟次数:").pack(side=tk.LEFT)
        self.sim_var = tk.StringVar(value="50000")
        sim_spinbox = ttk.Spinbox(custom_frame, from_=1000, to=500000,
                                  textvariable=self.sim_var, width=12)
        sim_spinbox.pack(side=tk.LEFT, padx=5)

        ttk.Button(custom_frame, text="应用",
                   command=self.apply_simulation_count).pack(side=tk.LEFT, padx=5)

        # 算法选择
        algo_frame = ttk.LabelFrame(scrollable_frame, text="算法选择", padding="10")
        algo_frame.pack(fill=tk.X, pady=10, padx=10)

        self.use_triangle_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(algo_frame, text="📐 使用三角定律（85%双狼定理）",
                        variable=self.use_triangle_var,
                        command=self.update_algo_settings).pack(anchor=tk.W, pady=5)

        self.use_weight_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(algo_frame, text="⚖️ 使用行为权重（贝叶斯更新）",
                        variable=self.use_weight_var,
                        command=self.update_algo_settings).pack(anchor=tk.W, pady=5)

        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        ttk.Label(scrollable_frame, text="开始分析",
                  font=("微软雅黑", 12, "bold")).pack(pady=10)

        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(fill=tk.X, pady=5, padx=10)

        buttons = [
            ("🎲 蒙特卡洛模拟", self.run_monte_carlo),
            ("📐 三角定律计算", self.run_triangle_law),
            ("📊 贝叶斯更新", self.run_bayesian_update),
            ("📈 综合分析", self.run_comprehensive_analysis)
        ]

        for text, cmd in buttons:
            btn = ttk.Button(btn_frame, text=text, command=cmd)
            btn.pack(fill=tk.X, pady=2)

        ttk.Label(scrollable_frame,
                  text="提示：综合分析会融合所有选中的算法",
                  font=("微软雅黑", 9), foreground=self.theme_manager.colors['gold']).pack(pady=10)

    def setup_middle_panel(self, parent):
        """设置中间面板"""
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 可视化号码牌
        visual_frame = ttk.Frame(notebook)
        notebook.add(visual_frame, text="🎴 号码牌视图")
        self.create_visual_tab(visual_frame)

        # 概率结果
        result_frame = ttk.Frame(notebook)
        notebook.add(result_frame, text="📊 概率结果")
        self.create_result_tab(result_frame)

        # 三角形分析
        triangle_frame = ttk.Frame(notebook)
        notebook.add(triangle_frame, text="📐 三角形分析")
        self.create_triangle_tab(triangle_frame)

    def create_visual_tab(self, parent):
        """创建可视化号码牌标签页"""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=10)

        ttk.Label(title_frame, text="玩家号码牌状态",
                  font=("微软雅黑", 14, "bold")).pack()
        ttk.Label(title_frame, text="点击号码牌可快速选择",
                  font=("微软雅黑", 9), foreground=self.theme_manager.colors['gold']).pack()

        columns_frame = ttk.Frame(main_frame)
        columns_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        # 左列 1-6
        left_column = ttk.Frame(columns_frame)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        ttk.Label(left_column, text="").pack(pady=5)

        for i in range(1, 7):
            card = PlayerCard(left_column, i, self.theme_manager.colors, self.quick_select_player)
            self.player_cards[i] = card

        # 右列 7-12
        right_column = ttk.Frame(columns_frame)
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        ttk.Label(right_column, text="").pack(pady=5)

        for i in range(7, 13):
            card = PlayerCard(right_column, i, self.theme_manager.colors, self.quick_select_player)
            self.player_cards[i] = card

        # 图例
        legend_frame = ttk.Frame(main_frame)
        legend_frame.pack(fill=tk.X, pady=5)

        ttk.Label(legend_frame, text="图例: ",
                  font=("微软雅黑", 10, "bold")).pack(side=tk.LEFT, padx=5)

        for color_name, color_value, text in [
            ('wolf', self.theme_manager.colors['wolf'], '狼人'),
            ('god', self.theme_manager.colors['god'], '神职'),
            ('human', self.theme_manager.colors['human'], '平民'),
            ('gold', self.theme_manager.colors['gold'], '好人标记'),
            ('player_bg', self.theme_manager.colors['player_bg'], '未知')
        ]:
            frame = tk.Frame(legend_frame, bg=color_value, width=20, height=20)
            frame.pack(side=tk.LEFT, padx=2)
            frame.pack_propagate(False)
            ttk.Label(legend_frame, text=text, foreground=color_value).pack(side=tk.LEFT, padx=5)

    def create_result_tab(self, parent):
        """创建结果标签页"""
        columns = ('玩家', '狼人概率', '神民概率', '平民概率', '所在三角')
        self.tree = ttk.Treeview(parent, columns=columns, show='headings', height=20,
                                 selectmode='browse')

        for col in columns:
            self.tree.heading(col, text=col)
            width = 70 if col == '玩家' else 100
            self.tree.column(col, width=width, anchor='center')

        vsb = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))

        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        self.tree.tag_configure('high', foreground=self.theme_manager.colors['wolf'])
        self.tree.tag_configure('medium', foreground=self.theme_manager.colors['gold'])
        self.tree.tag_configure('low', foreground=self.theme_manager.colors['god'])

    def create_triangle_tab(self, parent):
        """创建三角形分析标签页"""
        self.triangle_status_text = scrolledtext.ScrolledText(parent,
                                                              bg=self.theme_manager.colors['entry_bg'],
                                                              fg=self.theme_manager.colors['fg'],
                                                              font=("Consolas", 10),
                                                              height=20)
        self.triangle_status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.triangle_status_text.tag_config("bold", font=("Consolas", 10, "bold"))
        self.triangle_status_text.tag_config("wolf", foreground=self.theme_manager.colors['wolf'])
        self.triangle_status_text.tag_config("god", foreground=self.theme_manager.colors['god'])
        self.triangle_status_text.tag_config("human", foreground=self.theme_manager.colors['human'])
        self.triangle_status_text.tag_config("gold", foreground=self.theme_manager.colors['gold'])

        ttk.Button(parent, text="🔄 刷新分析",
                   command=self.update_triangle_analysis,
                   style='Accent.TButton').pack(pady=5)

        self.update_triangle_analysis()

    def setup_right_panel(self, parent):
        """设置右侧面板"""
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 日志
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="📝 实时日志")
        self.create_log_tab(log_frame)

        # 基础定律
        law_frame = ttk.Frame(notebook)
        notebook.add(law_frame, text="📏 基础定律")
        self.create_law_tab(law_frame)

        # 发言记录
        speech_frame = ttk.Frame(notebook)
        notebook.add(speech_frame, text="💬 发言记录")
        self.create_speech_tab(speech_frame)

        # 关于
        about_frame = ttk.Frame(notebook)
        notebook.add(about_frame, text="ℹ️ 关于")
        self.create_about_tab(about_frame)

    def create_log_tab(self, parent):
        """创建日志标签页"""
        self.log_text = scrolledtext.ScrolledText(parent,
                                                  bg=self.theme_manager.colors['entry_bg'],
                                                  fg=self.theme_manager.colors['fg'],
                                                  insertbackground=self.theme_manager.colors['fg'],
                                                  font=("Consolas", 9),
                                                  height=25)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Button(parent, text="🗑️ 清空日志",
                   command=self.clear_log).pack(pady=5)

    def create_law_tab(self, parent):
        """创建基础定律标签页"""
        self.law_right_text = scrolledtext.ScrolledText(parent,
                                                        bg=self.theme_manager.colors['entry_bg'],
                                                        fg=self.theme_manager.colors['fg'],
                                                        font=("Consolas", 10),
                                                        height=20,
                                                        wrap=tk.WORD)
        self.law_right_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.law_right_text.tag_config("bold", font=("Consolas", 10, "bold"))
        self.law_right_text.tag_config("title", font=("Consolas", 11, "bold"),
                                       foreground=self.theme_manager.colors['gold'])
        self.law_right_text.tag_config("wolf", foreground=self.theme_manager.colors['wolf'])
        self.law_right_text.tag_config("god", foreground=self.theme_manager.colors['god'])
        self.law_right_text.tag_config("human", foreground=self.theme_manager.colors['human'])

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="🔄 刷新定律",
                   command=self.update_law_display,
                   style='Accent.TButton').pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)

        ttk.Button(btn_frame, text="📋 复制内容",
                   command=lambda: self.copy_text(self.law_right_text)).pack(side=tk.LEFT, padx=2,
                                                                             expand=True, fill=tk.X)

        self.update_law_display()

    def update_law_display(self):
        """更新基础定律显示"""
        self.law_right_text.delete(1.0, tk.END)

        # 三角定律
        self.law_right_text.insert(tk.END, "📐 三角定律分布\n", "title")
        self.law_right_text.insert(tk.END, "─" * 40 + "\n")

        tri_probs = self.calculator.calculate_triangle_distribution(100000)
        for case, prob in tri_probs.items():
            self.law_right_text.insert(tk.END, f"{case}: {prob:.1%}\n")

        prob_double = 1 - tri_probs.get("四个三角各1狼", 0)
        self.law_right_text.insert(tk.END, f"\n✅ 至少一组双狼: {prob_double:.1%}\n\n")

        # 三行定律
        self.law_right_text.insert(tk.END, "📏 三行定律\n", "title")
        self.law_right_text.insert(tk.END, "─" * 40 + "\n")

        row_prob = self.calculator.calculate_row_probability(100000)
        self.law_right_text.insert(tk.END, f"连续三行有≥3狼: {row_prob:.1%}\n\n")

        # 四角定律
        self.law_right_text.insert(tk.END, "🔲 四角定律\n", "title")
        self.law_right_text.insert(tk.END, "─" * 40 + "\n")

        corner_probs = self.calculator.calculate_corner_probabilities(100000)
        for k, v in corner_probs.items():
            self.law_right_text.insert(tk.END, f"单组{k}狼: {v:.1%}\n")

        # 组合数学
        self.law_right_text.insert(tk.END, "\n" + "─" * 40 + "\n")
        self.law_right_text.insert(tk.END, "📊 组合数学\n", "title")
        self.law_right_text.insert(tk.END, f"总组合数: C(12,4) = 495\n")
        self.law_right_text.insert(tk.END, f"每组各1狼: 81/495 = {81 / 495:.2%}\n")
        self.law_right_text.insert(tk.END, f"至少一组双狼: {1 - 81 / 495:.2%}\n")

    def create_speech_tab(self, parent):
        """创建发言记录标签页"""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=5)

        ttk.Label(info_frame, text="📝 玩家发言记录",
                  font=("微软雅黑", 11, "bold")).pack(side=tk.LEFT)
        ttk.Label(info_frame, text="(可记录每轮发言，用于分析)",
                  font=("微软雅黑", 9), foreground=self.theme_manager.colors['gold']).pack(side=tk.LEFT, padx=10)

        select_frame = ttk.Frame(main_frame)
        select_frame.pack(fill=tk.X, pady=5)

        ttk.Label(select_frame, text="选择玩家:", font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=2)
        self.speech_player_var = tk.StringVar()
        self.speech_player_combo = ttk.Combobox(select_frame,
                                                textvariable=self.speech_player_var,
                                                values=self.config.players,
                                                state="readonly",
                                                width=10)
        self.speech_player_combo.pack(side=tk.LEFT, padx=5)
        self.speech_player_combo.bind('<<ComboboxSelected>>', self.on_speech_player_selected)

        ttk.Label(select_frame, text="轮次:", font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=(20, 2))
        self.speech_round_var = tk.StringVar(value="第1轮")
        round_values = [f"第{i}轮" for i in range(1, 11)] + ["警上", "警下", "遗言", "总结"]
        self.speech_round_combo = ttk.Combobox(select_frame,
                                               textvariable=self.speech_round_var,
                                               values=round_values,
                                               state="readonly",
                                               width=8)
        self.speech_round_combo.pack(side=tk.LEFT, padx=5)

        text_frame = ttk.LabelFrame(main_frame, text="发言内容", padding="5")
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.speech_text = scrolledtext.ScrolledText(text_frame,
                                                     bg=self.theme_manager.colors['entry_bg'],
                                                     fg=self.theme_manager.colors['fg'],
                                                     insertbackground=self.theme_manager.colors['fg'],
                                                     font=("微软雅黑", 10),
                                                     height=12,
                                                     wrap=tk.WORD,
                                                     undo=True)
        self.speech_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        btn_frame1 = ttk.Frame(main_frame)
        btn_frame1.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame1, text="💾 保存发言",
                   command=self.save_speech,
                   style='Accent.TButton').pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        ttk.Button(btn_frame1, text="🔄 清空当前",
                   command=self.clear_current_speech).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)

        list_frame = ttk.LabelFrame(main_frame, text="已保存的发言记录", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)

        left_list = ttk.Frame(list_container)
        left_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.speech_listbox = tk.Listbox(left_list,
                                         height=6,
                                         bg=self.theme_manager.colors['entry_bg'],
                                         fg=self.theme_manager.colors['fg'],
                                         selectbackground=self.theme_manager.colors['tree_select'],
                                         font=("微软雅黑", 9))
        self.speech_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        list_scrollbar = ttk.Scrollbar(left_list, orient=tk.VERTICAL,
                                       command=self.speech_listbox.yview)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.speech_listbox.configure(yscrollcommand=list_scrollbar.set)
        self.speech_listbox.bind('<<ListboxSelect>>', self.on_speech_record_selected)

        right_btn = ttk.Frame(list_container)
        right_btn.pack(side=tk.RIGHT, fill=tk.Y, padx=5)

        ttk.Button(right_btn, text="查看", command=self.view_speech_record, width=8).pack(pady=2)
        ttk.Button(right_btn, text="删除", command=self.delete_speech_record, width=8).pack(pady=2)

        btn_frame2 = ttk.Frame(main_frame)
        btn_frame2.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame2, text="🗑️ 清空所有记录",
                   command=self.clear_all_speech_records).pack(side=tk.RIGHT, padx=2)

    def create_about_tab(self, parent):
        """创建关于标签页"""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text_widget = tk.Text(main_frame, wrap=tk.WORD, font=('微软雅黑', 10),
                              bg=self.theme_manager.colors['entry_bg'],
                              fg=self.theme_manager.colors['fg'],
                              relief=tk.FLAT, borderwidth=0)
        text_widget.pack(fill=tk.BOTH, expand=True)

        about_text = """
        ╔══════════════════════════════════════════════════════════════╗
        ║                   狼人杀概论计算器 v1.0                        ║
        ║           Werewolf Probability Calculator                    ║
        ╚══════════════════════════════════════════════════════════════╝

        【核心功能】
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        ✓ 多算法融合分析
          • 蒙特卡洛模拟（NumPy加速，50000+次/秒）
          • 三角定律（85%双狼定理）
          • 贝叶斯更新（权重系统）
          • 综合分析（加权融合）

        ✓ 智能身份系统
          • 支持 50+ 种身份标记
          • 好人标记自动分配
          • 自定义标签权重
          • 实时身份状态追踪

        ✓ 可视化交互
          • 仿网易狼人杀号码牌
          • 点击卡片快速选择
          • 实时概率更新
          • 三角形格局分析

        【技术特性】
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        ▶ 算法精度
          组合数学基础：C(12,4) = 495 种分布
          三角定律准确率：83.64% 至少一组双狼
          贝叶斯更新：支持多权重协同

        ▶ 性能优化
          模拟次数：50,000 - 500,000 可调
          响应时间：< 1秒（50,000次，NumPy加速）
          内存占用：< 100MB

        ▶ 扩展性
          模块化设计（6个独立类）
          支持添加新身份
          可自定义算法权重
          支持主题切换（深色/浅色）

        【使用指南】
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        1. 选择玩家编号
        2. 标记已知身份
        3. 可选：添加行为权重
        4. 选择算法并计算
        5. 查看概率结果

        【版本信息】
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        版本号：v1.0
        发布日期：2026年3月
        开发作者：Haisi-1536
        开源协议：MIT License

        更新日志：
        v1.0 (2026.03)
          • 重构为模块化设计（6个独立类）
          • NumPy加速，性能提升10-20倍
          • 新增进度条和缓存机制
          • 优化三角形分析界面
          • 修复多个已知 bug
          • 新增完整配置保存/加载功能
          • 发言记录系统

        【下载与反馈】
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        GitHub：https://github.com/Haisi-1536/Werewolves

        问题反馈：
          • GitHub Issues
          • 发送邮件至：haisi@mail.com

        欢迎贡献代码、提出建议！
                """

        text_widget.insert(tk.END, about_text)

        # GitHub链接高亮
        start_pos = about_text.find("https://github.com/Haisi-1536/Werewolves")
        if start_pos != -1:
            line_count = len(about_text[:start_pos].split('\n'))
            char_count = len(about_text[:start_pos].split('\n')[-1])
            start_idx = f"{line_count}.{char_count}"
            end_idx = f"{line_count}.{char_count + len('https://github.com/Haisi-1536/Werewolves')}"

            text_widget.tag_add("hyperlink", start_idx, end_idx)
            text_widget.tag_config("hyperlink", foreground="blue", underline=True)
            text_widget.tag_bind("hyperlink", "<Button-1>",
                                 lambda e: webbrowser.open("https://github.com/Haisi-1536/Werewolves"))
            text_widget.tag_bind("hyperlink", "<Enter>",
                                 lambda e: text_widget.config(cursor="hand2"))
            text_widget.tag_bind("hyperlink", "<Leave>",
                                 lambda e: text_widget.config(cursor=""))

        # 邮箱链接高亮（可选）
        email_pos = about_text.find("haisi@mail.com")
        if email_pos != -1:
            line_count = len(about_text[:email_pos].split('\n'))
            char_count = len(about_text[:email_pos].split('\n')[-1])
            start_idx = f"{line_count}.{char_count}"
            end_idx = f"{line_count}.{char_count + len('haisi@mail.com')}"

            text_widget.tag_add("email", start_idx, end_idx)
            text_widget.tag_config("email", foreground="blue", underline=True)
            text_widget.tag_bind("email", "<Button-1>",
                                 lambda e: webbrowser.open("mailto:haisi@mail.com"))
            text_widget.tag_bind("email", "<Enter>",
                                 lambda e: text_widget.config(cursor="hand2"))
            text_widget.tag_bind("email", "<Leave>",
                                 lambda e: text_widget.config(cursor=""))

        text_widget.config(state=tk.DISABLED)

    def create_status_bar(self):
        """创建状态栏"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=5, pady=2)

        self.status_label = ttk.Label(status_frame, text="就绪", font=("微软雅黑", 9))
        self.status_label.pack(side=tk.LEFT)

        self.sim_label = ttk.Label(status_frame,
                                   text=f"模拟次数: {self.simulation_count}",
                                   font=("微软雅黑", 9))
        self.sim_label.pack(side=tk.RIGHT, padx=20)

        algo_status = []
        if self.use_triangle_law:
            algo_status.append("三角定律")
        if self.use_behavior_weight:
            algo_status.append("行为权重")
        algo_text = " | ".join(algo_status) if algo_status else "基础模式"

        self.algo_label = ttk.Label(status_frame,
                                    text=f"算法: {algo_text}",
                                    font=("微软雅黑", 9))
        self.algo_label.pack(side=tk.RIGHT, padx=20)

    # ========== 事件处理方法 ==========

    def log(self, message):
        """添加日志"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.log("日志已清空")

    def copy_text(self, text_widget):
        """复制文本到剪贴板"""
        try:
            content = text_widget.get(1.0, tk.END)
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.log("内容已复制到剪贴板")
            messagebox.showinfo("提示", "内容已复制到剪贴板")
        except Exception as e:
            self.log(f"复制失败: {e}")
            messagebox.showerror("错误", f"复制失败: {e}")

    def quick_select_player(self, player_num):
        """快速选择玩家 - 同时更新所有玩家选择下拉框"""
        # 更新身份输入页面的玩家选择
        self.player_var.set(str(player_num))

        # 更新权重设置页面的玩家选择
        self.weight_player_var.set(str(player_num))

        # 更新发言记录页面的玩家选择
        self.speech_player_var.set(str(player_num))

        self.log(f"快速选择玩家 {player_num}")

        # 清空所有分类的选中状态
        for var in self.role_vars.values():
            var.set('')

        # 如果该玩家已有身份，自动选中对应的身份
        if player_num in self.role_manager.known_info:
            role = self.role_manager.known_info[player_num]["role"]
            category = self.role_manager.known_info[player_num].get("category")

            if category and category in self.role_vars:
                self.role_vars[category].set(role)
                self.switch_to_category_tab(category)
                self.log(f"自动选中身份: {role} [分类: {category}]")
            else:
                for cat, roles in self.role_manager.role_categories.items():
                    if role in roles:
                        self.role_vars[cat].set(role)
                        self.switch_to_category_tab(cat)
                        self.log(f"自动选中身份: {role} [分类: {cat}]")
                        break

    def quick_select_player_with_speech(self, player_num):
        """快速选择玩家并自动加载最近发言"""
        # 先调用基本的选择
        self.quick_select_player(player_num)

        # 查找该玩家的所有发言记录
        player_records = [(rnd, content) for (p, rnd), content in self.speech_records.items()
                          if p == player_num]

        if player_records:
            # 按轮次排序
            def round_key(round_text):
                match = re.search(r'\d+', round_text)
                if match:
                    return int(match.group())
                # 处理非数字轮次（警上、警下等）
                priority = {"警上": 100, "警下": 101, "遗言": 200, "总结": 300}
                return priority.get(round_text, 999)

            player_records.sort(key=lambda x: round_key(x[0]), reverse=True)
            latest_round, _ = player_records[0]

            # 设置轮次并加载发言
            self.speech_round_var.set(latest_round)
            self.load_speech_record(player_num, latest_round)
            self.log(f"自动加载玩家{player_num}的{latest_round}发言")

    def switch_to_category_tab(self, target_category):
        """切换到指定的分类标签页"""
        try:
            tabs = self.role_notebook.tabs()
            for i, tab_id in enumerate(tabs):
                if self.role_notebook.tab(tab_id, "text") == target_category:
                    self.role_notebook.select(i)
                    break
        except:
            pass

    def on_player_selected(self, event):
        """玩家选择事件"""
        player = self.player_var.get()
        if player and player.isdigit():
            player = int(player)

            for var in self.role_vars.values():
                var.set('')

            if player in self.role_manager.known_info:
                role = self.role_manager.known_info[player]["role"]
                for category, roles in self.role_manager.role_categories.items():
                    if role in roles:
                        self.role_vars[category].set(role)
                        self.log(f"自动选中身份: {role}")
                        break

    def add_known_info(self):
        """添加已知信息"""
        try:
            player = int(self.player_var.get())

            current_tab_index = self.role_notebook.index(self.role_notebook.select())
            current_tab_text = self.role_notebook.tab(current_tab_index, "text")

            selected_role = None
            selected_category = None

            if current_tab_text in self.role_vars:
                current_role = self.role_vars[current_tab_text].get()
                if current_role:
                    selected_role = current_role
                    selected_category = current_tab_text

            if not selected_role:
                for category, var in self.role_vars.items():
                    role = var.get()
                    if role:
                        selected_role = role
                        selected_category = category
                        break

            if not selected_role:
                messagebox.showwarning("警告", "请选择身份")
                return

            old_info = self.role_manager.known_info.get(player)
            if old_info:
                self.log(f"修改玩家{player}的身份: {old_info['role']} -> {selected_role}")
            else:
                self.log(f"添加已知信息: 玩家{player} 是 {selected_role}")

            self.role_manager.add_known_info(player, selected_role, selected_category)
            self.update_info_listbox()
            self.update_player_cards()
            self.update_triangle_analysis()
            self.update_status()

            self.player_var.set('')

        except ValueError:
            messagebox.showerror("错误", "请选择有效的玩家编号")

    def delete_selected_info(self):
        """删除选中的信息"""
        selection = self.info_listbox.curselection()
        if selection:
            text = self.info_listbox.get(selection[0])
            try:
                if '玩家' in text:
                    player = int(text.split('玩家')[1].split(':')[0])
                    if self.role_manager.remove_known_info(player):
                        self.log(f"删除玩家{player}的已知信息")
                        self.update_info_listbox()
                        self.update_player_cards()
                        self.update_triangle_analysis()
                        self.update_status()
            except:
                pass

    def on_tag_selected(self, event):
        """标签选择事件"""
        tag_name = self.tag_preset_var.get()
        if tag_name and tag_name in self.role_manager.custom_tags:
            weights = self.role_manager.custom_tags[tag_name]

            self.wolf_weight.delete(0, tk.END)
            self.wolf_weight.insert(0, str(weights["wolf"]))
            self.god_weight.delete(0, tk.END)
            self.god_weight.insert(0, str(weights["god"]))
            self.human_weight.delete(0, tk.END)
            self.human_weight.insert(0, str(weights["human"]))

            self.tag_info_label.config(
                text=f"已加载标签: {tag_name} (狼{weights['wolf']} 神{weights['god']} 人{weights['human']})",
                foreground=self.theme_manager.colors['gold']
            )
            self.log(f"加载标签 '{tag_name}'")

    def on_weight_selected(self, event):
        """权重列表选择事件"""
        selection = self.weight_listbox.curselection()
        if selection:
            text = self.weight_listbox.get(selection[0])
            try:
                if '玩家' in text:
                    player = int(text.split('玩家')[1].split(':')[0])
                    weight_part = text.split(':')[1].strip()

                    wolf_match = re.search(r'狼([\d.]+)', weight_part)
                    god_match = re.search(r'神([\d.]+)', weight_part)
                    human_match = re.search(r'人([\d.]+)', weight_part)

                    if wolf_match and god_match and human_match:
                        self.weight_player_var.set(str(player))
                        self.wolf_weight.delete(0, tk.END)
                        self.wolf_weight.insert(0, wolf_match.group(1))
                        self.god_weight.delete(0, tk.END)
                        self.god_weight.insert(0, god_match.group(1))
                        self.human_weight.delete(0, tk.END)
                        self.human_weight.insert(0, human_match.group(1))
                        self.log(f"加载玩家{player}的权重配置")
            except Exception as e:
                self.log(f"解析权重失败: {e}")

    def save_custom_tag(self):
        """保存自定义标签"""
        try:
            wolf_weight = float(self.wolf_weight.get())
            god_weight = float(self.god_weight.get())
            human_weight = float(self.human_weight.get())

            tag_name = self.tag_preset_var.get()

            if not tag_name or tag_name == "":
                dialog = tk.Toplevel(self.root)
                dialog.title("新建标签")
                dialog.geometry("300x150")
                dialog.transient(self.root)
                dialog.grab_set()

                dialog.update_idletasks()
                x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
                y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
                dialog.geometry(f"+{x}+{y}")

                ttk.Label(dialog, text="请输入标签名称:", font=("微软雅黑", 10)).pack(pady=10)
                tag_entry = ttk.Entry(dialog, width=25, font=("微软雅黑", 10))
                tag_entry.pack(pady=5)
                tag_entry.focus()

                def do_save():
                    new_tag = tag_entry.get().strip()
                    if new_tag:
                        self.role_manager.custom_tags[new_tag] = {
                            "wolf": wolf_weight,
                            "god": god_weight,
                            "human": human_weight
                        }
                        tag_list = [""] + list(self.role_manager.custom_tags.keys())
                        self.tag_preset_combo['values'] = tag_list
                        self.tag_preset_var.set(new_tag)
                        self.log(f"新建标签: {new_tag}")
                        dialog.destroy()
                    else:
                        messagebox.showwarning("警告", "标签名称不能为空")

                tag_entry.bind('<Return>', lambda e: do_save())

                btn_frame = ttk.Frame(dialog)
                btn_frame.pack(pady=10)
                ttk.Button(btn_frame, text="保存", command=do_save).pack(side=tk.LEFT, padx=5)
                ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

            else:
                if messagebox.askyesno("确认",
                                       f"是否更新标签 '{tag_name}' 的权重为\n狼{wolf_weight} 神{god_weight} 人{human_weight}？"):
                    self.role_manager.custom_tags[tag_name] = {
                        "wolf": wolf_weight,
                        "god": god_weight,
                        "human": human_weight
                    }
                    self.log(f"更新标签: {tag_name}")

        except ValueError:
            messagebox.showerror("错误", "请输入有效的权重数值")

    def delete_current_tag(self):
        """删除当前选中的标签"""
        tag_name = self.tag_preset_var.get()
        if not tag_name:
            messagebox.showwarning("警告", "请先选择要删除的标签")
            return

        if tag_name not in self.role_manager.custom_tags:
            messagebox.showerror("错误", f"标签 '{tag_name}' 不存在")
            return

        if messagebox.askyesno("确认删除", f"确定要删除标签 '{tag_name}' 吗？"):
            del self.role_manager.custom_tags[tag_name]
            tag_list = [""] + list(self.role_manager.custom_tags.keys())
            self.tag_preset_combo['values'] = tag_list
            self.tag_preset_var.set("")
            self.log(f"删除标签: {tag_name}")

    def add_behavior_weight(self):
        """添加行为权重"""
        try:
            player = int(self.weight_player_var.get())
            wolf_weight = float(self.wolf_weight.get())
            god_weight = float(self.god_weight.get())
            human_weight = float(self.human_weight.get())

            old_weights = self.role_manager.behavior_weights.get(player)
            if old_weights:
                self.log(f"更新玩家{player}的权重")
            else:
                self.log(f"添加行为权重: 玩家{player}")

            self.role_manager.add_behavior_weight(player, wolf_weight, god_weight, human_weight)
            self.update_weight_listbox()

        except ValueError:
            messagebox.showerror("错误", "请输入有效的玩家编号和权重数值")

    def delete_selected_weight(self):
        """删除选中的权重"""
        selection = self.weight_listbox.curselection()
        if selection:
            text = self.weight_listbox.get(selection[0])
            try:
                if '玩家' in text:
                    player = int(text.split('玩家')[1].split(':')[0])
                    if self.role_manager.remove_behavior_weight(player):
                        self.log(f"删除玩家{player}的行为权重")
                        self.update_weight_listbox()

                        self.weight_player_var.set('')
                        self.wolf_weight.delete(0, tk.END)
                        self.wolf_weight.insert(0, "1.0")
                        self.god_weight.delete(0, tk.END)
                        self.god_weight.insert(0, "1.0")
                        self.human_weight.delete(0, tk.END)
                        self.human_weight.insert(0, "1.0")
            except:
                pass
        else:
            messagebox.showinfo("提示", "请在列表中选择要删除的权重项")

    def clear_all_weights(self):
        """清除所有权重"""
        if self.role_manager.behavior_weights:
            if messagebox.askyesno("确认", "确定要清除所有已设置的权重吗？"):
                self.role_manager.behavior_weights.clear()
                self.update_weight_listbox()
                self.log("已清除所有行为权重")

                self.weight_player_var.set('')
                self.wolf_weight.delete(0, tk.END)
                self.wolf_weight.insert(0, "1.0")
                self.god_weight.delete(0, tk.END)
                self.god_weight.insert(0, "1.0")
                self.human_weight.delete(0, tk.END)
                self.human_weight.insert(0, "1.0")

    def update_info_listbox(self):
        """更新信息列表"""
        self.info_listbox.delete(0, tk.END)

        for player, info in sorted(self.role_manager.known_info.items()):
            triangle = self.config.get_player_triangle(player)
            role_type = info["type"]

            prefix = {
                "wolf": "🐺",
                "god": "👼",
                "human": "👤"
            }.get(role_type, "⭐")

            display_text = f"{prefix} 玩家{player}: {info['role']} [{triangle}]"
            self.info_listbox.insert(tk.END, display_text)

        # 更新统计信息
        known_wolves = sum(1 for info in self.role_manager.known_info.values() if info.get("type") == "wolf")
        known_gods = sum(1 for info in self.role_manager.known_info.values() if info.get("type") == "god")
        known_humans = sum(1 for info in self.role_manager.known_info.values() if info.get("type") == "human")
        known_marks = sum(1 for info in self.role_manager.known_info.values() if info.get("type") == "good_mark")

        self.info_stats.config(
            text=f"已知: {len(self.role_manager.known_info)} | 狼: {known_wolves} | 神: {known_gods} | 民: {known_humans} | 标记: {known_marks}"
        )

    def update_weight_listbox(self):
        """更新权重列表"""
        self.weight_listbox.delete(0, tk.END)

        for player, weights in sorted(self.role_manager.behavior_weights.items()):
            display_text = f"玩家{player}: 狼{weights['狼权']:.1f} 神{weights['神权']:.1f} 人{weights['民权']:.1f}"
            self.weight_listbox.insert(tk.END, display_text)

    def update_player_cards(self):
        """更新所有玩家卡片"""
        for card in self.player_cards.values():
            card.update(self.role_manager.known_info)

    def update_triangle_analysis(self):
        """更新三角形分析"""
        if not hasattr(self, 'triangle_status_text'):
            return

        self.triangle_status_text.delete(1.0, tk.END)

        triangle_stats = {}
        for tri_name, tri_players in self.config.triangles.items():
            known_wolves = known_gods = known_humans = known_marks = 0
            unknown = []

            for player in tri_players:
                if player in self.role_manager.known_info:
                    info = self.role_manager.known_info[player]
                    role_type = info.get("type", "unknown")

                    if role_type == "wolf":
                        known_wolves += 1
                    elif role_type == "god":
                        known_gods += 1
                    elif role_type == "human":
                        known_humans += 1
                    elif role_type == "good_mark":
                        known_marks += 1
                else:
                    unknown.append(player)

            triangle_stats[tri_name] = {
                "known_wolves": known_wolves,
                "known_gods": known_gods,
                "known_humans": known_humans,
                "known_marks": known_marks,
                "unknown": unknown,
                "unknown_count": len(unknown)
            }

        self.triangle_status_text.insert(tk.END, "🔺 三角形实时状态\n", "bold")
        self.triangle_status_text.insert(tk.END, "═" * 40 + "\n")

        for tri_name, stats in triangle_stats.items():
            self.triangle_status_text.insert(tk.END, f"\n{tri_name}: ", "bold")
            self.triangle_status_text.insert(tk.END, f"[🐺{stats['known_wolves']} ", "wolf")
            self.triangle_status_text.insert(tk.END, f"👼{stats['known_gods']} ", "god")
            self.triangle_status_text.insert(tk.END, f"👤{stats['known_humans']} ", "human")
            self.triangle_status_text.insert(tk.END, f"⭐{stats['known_marks']}] ", "gold")
            self.triangle_status_text.insert(tk.END, f"未知:{stats['unknown_count']}\n")

            if stats['unknown']:
                self.triangle_status_text.insert(tk.END, f"   未知玩家: {sorted(stats['unknown'])}\n")

        self.triangle_status_text.insert(tk.END, "\n" + "═" * 40 + "\n")
        self.triangle_status_text.insert(tk.END, "📐 三角定律分析:\n", "bold")

        has_double = False
        for tri_name, stats in triangle_stats.items():
            if stats['known_wolves'] >= 2:
                has_double = True
                self.triangle_status_text.insert(tk.END, f"✅ {tri_name} 已满足双狼！\n", "wolf")
                opposite = self.config.triangle_opposites[tri_name]
                self.triangle_status_text.insert(tk.END, f"   ↪ 关注对角 {opposite} 的格局\n", "god")

        if not has_double:
            self.triangle_status_text.insert(tk.END, "⚠️ 当前尚未出现双狼三角形\n", "human")
            self.triangle_status_text.insert(tk.END, f"📊 至少一组双狼概率: ≈{1 - 81 / 495:.1%}\n")

        self.triangle_status_text.insert(tk.END, "\n🎯 最可能出双狼的三角形:\n", "bold")

        candidates = []
        for tri_name, stats in triangle_stats.items():
            if stats['known_wolves'] == 1 and stats['unknown_count'] >= 1:
                prob = 1 / stats['unknown_count']
                candidates.append((tri_name, prob, stats['unknown']))
            elif stats['known_wolves'] == 0 and stats['unknown_count'] >= 2:
                prob = 2 / stats['unknown_count']
                candidates.append((tri_name, prob, stats['unknown']))

        for tri_name, prob, unknown in sorted(candidates, key=lambda x: x[1], reverse=True)[:2]:
            self.triangle_status_text.insert(tk.END, f"  {tri_name}: 概率{prob:.1%} 未知:{sorted(unknown)}\n")

    def update_status(self):
        """更新状态栏"""
        known_count = len(self.role_manager.known_info)
        known_wolves = sum(1 for info in self.role_manager.known_info.values() if info.get("type") == "wolf")

        if known_count == 0:
            self.status_label.config(text="就绪 | 等待输入已知信息")
        else:
            self.status_label.config(text=f"运行中 | 已确认 {known_wolves} 狼, 剩余 {4 - known_wolves} 狼待找")

    def apply_simulation_count(self):
        """应用模拟次数"""
        try:
            count = int(self.sim_var.get())
            count = max(1000, min(500000, count))
            self.sim_var.set(str(count))
            self.simulation_count = count
            self.sim_label.config(text=f"模拟次数: {count}")
            self.log(f"设置模拟次数: {count}")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")

    def update_algo_settings(self):
        """更新算法设置"""
        self.use_triangle_law = self.use_triangle_var.get()
        self.use_behavior_weight = self.use_weight_var.get()

        algo_status = []
        if self.use_triangle_law:
            algo_status.append("三角定律")
        if self.use_behavior_weight:
            algo_status.append("行为权重")
        algo_text = " | ".join(algo_status) if algo_status else "基础模式"

        self.algo_label.config(text=f"算法: {algo_text}")
        self.log(f"算法设置: 三角定律{'开启' if self.use_triangle_law else '关闭'}, "
                 f"行为权重{'开启' if self.use_behavior_weight else '关闭'}")

    def clear_all(self):
        """清空所有信息"""
        if messagebox.askyesno("确认", "确定要清空所有信息吗？"):
            self.role_manager.clear_all()
            self.update_info_listbox()
            self.update_weight_listbox()
            self.update_player_cards()
            self.update_triangle_analysis()
            self.update_status()

            for item in self.tree.get_children():
                self.tree.delete(item)

            for card in self.player_cards.values():
                card.set_probabilities(0, 0, 0)

            self.log("已清空所有信息")

    # ========== 发言记录相关方法 ==========

    def on_speech_player_selected(self, event):
        """发言记录玩家选择事件 - 自动加载该玩家的当前轮次发言"""
        player = self.speech_player_var.get()
        round_text = self.speech_round_var.get()

        if player and player.isdigit() and round_text:
            self.load_speech_record(int(player), round_text)

    def load_speech_record(self, player, round_text):
        """加载发言记录"""
        key = (player, round_text)
        if key in self.speech_records:
            self.speech_text.delete(1.0, tk.END)
            self.speech_text.insert(1.0, self.speech_records[key])
            self.log(f"加载发言记录: 玩家{player} {round_text}")
        else:
            self.speech_text.delete(1.0, tk.END)

    def save_speech(self):
        """保存发言记录"""
        try:
            player = int(self.speech_player_var.get())
            round_text = self.speech_round_var.get()
            content = self.speech_text.get(1.0, tk.END).strip()

            if not content:
                messagebox.showwarning("警告", "发言内容不能为空")
                return

            key = (player, round_text)
            self.speech_records[key] = content
            self.update_speech_listbox()

            self.log(f"保存发言记录: 玩家{player} {round_text}")
            summary = content[:50] + "..." if len(content) > 50 else content
            self.log(f"  内容: {summary}")

        except ValueError:
            messagebox.showwarning("警告", "请选择玩家编号")

    def update_speech_listbox(self):
        """更新发言记录列表"""
        self.speech_listbox.delete(0, tk.END)
        for player, round_text in sorted(self.speech_records.keys(), key=lambda x: (x[0], x[1])):
            self.speech_listbox.insert(tk.END, f"玩家{player} - {round_text}")

    def on_speech_record_selected(self, event):
        """发言记录选择事件"""
        selection = self.speech_listbox.curselection()
        if selection:
            text = self.speech_listbox.get(selection[0])
            try:
                player = int(text.split(" - ")[0].replace("玩家", ""))
                round_text = text.split(" - ")[1]
                self.speech_player_var.set(str(player))
                self.speech_round_var.set(round_text)
                self.load_speech_record(player, round_text)
            except:
                pass

    def view_speech_record(self):
        """查看发言记录"""
        selection = self.speech_listbox.curselection()
        if not selection:
            messagebox.showinfo("提示", "请先在列表中选择要查看的记录")
            return

        text = self.speech_listbox.get(selection[0])
        try:
            player = int(text.split(" - ")[0].replace("玩家", ""))
            round_text = text.split(" - ")[1]
            key = (player, round_text)

            if key in self.speech_records:
                dialog = tk.Toplevel(self.root)
                dialog.title(f"玩家{player} {round_text} 发言记录")
                dialog.geometry("500x400")
                dialog.transient(self.root)

                text_widget = scrolledtext.ScrolledText(dialog,
                                                        bg=self.theme_manager.colors['entry_bg'],
                                                        fg=self.theme_manager.colors['fg'],
                                                        font=("微软雅黑", 10),
                                                        wrap=tk.WORD)
                text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                text_widget.insert(1.0, self.speech_records[key])
                text_widget.config(state=tk.DISABLED)

                ttk.Button(dialog, text="关闭", command=dialog.destroy).pack(pady=5)
        except:
            pass

    def delete_speech_record(self):
        """删除发言记录"""
        selection = self.speech_listbox.curselection()
        if not selection:
            messagebox.showinfo("提示", "请先在列表中选择要删除的记录")
            return

        text = self.speech_listbox.get(selection[0])
        try:
            player = int(text.split(" - ")[0].replace("玩家", ""))
            round_text = text.split(" - ")[1]
            key = (player, round_text)

            if messagebox.askyesno("确认删除", f"确定要删除玩家{player} {round_text}的发言记录吗？"):
                del self.speech_records[key]
                self.update_speech_listbox()

                current_player = self.speech_player_var.get()
                current_round = self.speech_round_var.get()
                if current_player and current_round:
                    if int(current_player) == player and current_round == round_text:
                        self.speech_text.delete(1.0, tk.END)

                self.log(f"删除发言记录: 玩家{player} {round_text}")
        except:
            pass

    def clear_current_speech(self):
        """清空当前发言"""
        if self.speech_text.get(1.0, tk.END).strip():
            if messagebox.askyesno("确认", "确定要清空当前输入内容吗？"):
                self.speech_text.delete(1.0, tk.END)

    def clear_all_speech_records(self):
        """清空所有发言记录"""
        if self.speech_records:
            if messagebox.askyesno("确认", f"确定要清空所有{len(self.speech_records)}条发言记录吗？"):
                self.speech_records.clear()
                self.speech_listbox.delete(0, tk.END)
                self.speech_text.delete(1.0, tk.END)
                self.log("已清空所有发言记录")

    # ========== 保存/加载配置（完整版） ==========

    def save_config(self):
        """保存完整配置到文件 - 包含所有程序状态"""
        try:
            # 收集所有需要保存的数据
            config_data = {
                # 版本信息
                "version": "2.0",
                "save_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

                # 游戏配置
                "game_config": {
                    "total_players": self.config.total_players,
                    "wolves": self.config.wolves,
                    "gods": self.config.gods,
                    "villagers": self.config.villagers
                },

                # 核心数据
                "role_manager": {
                    "known_info": self.role_manager.known_info,
                    "behavior_weights": self.role_manager.behavior_weights,
                    "custom_tags": self.role_manager.custom_tags
                },

                # 算法设置
                "algorithm_settings": {
                    "simulation_count": self.simulation_count,
                    "use_triangle_law": self.use_triangle_law,
                    "use_behavior_weight": self.use_behavior_weight
                },

                # 发言记录
                "speech_records": {
                    f"{player}_{round}": content
                    for (player, round), content in self.speech_records.items()
                },

                # 概率结果（当前显示在树形视图中的结果）
                "probability_results": self._get_current_results(),

                # 三角形分析状态
                "triangle_analysis": self.triangle_status_text.get(1.0, tk.END) if self.triangle_status_text else "",

                # 日志内容
                "log_content": self.log_text.get(1.0, tk.END) if self.log_text else "",

                # 基础定律显示内容
                "law_display": self.law_right_text.get(1.0, tk.END) if self.law_right_text else "",

                # 主题设置
                "theme": self.theme_manager.current_theme,

                # 界面状态（当前选中的标签页等）
                "ui_state": self._get_ui_state()
            }

            # 弹出保存文件对话框
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[
                    ("配置文件", "*.json"),
                    ("备份文件", "*.bak"),
                    ("所有文件", "*.*")
                ],
                title="保存完整配置",
                initialfile=f"狼人杀配置_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

            if not filename:  # 用户取消
                return

            # 保存到文件
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2, default=str)

            self.log(f"✅ 完整配置已保存: {filename}")
            self.log(f"  包含: 身份({len(self.role_manager.known_info)}个) | "
                     f"权重({len(self.role_manager.behavior_weights)}个) | "
                     f"发言({len(self.speech_records)}条)")
            messagebox.showinfo("保存成功", f"配置已保存到：\n{filename}")

        except Exception as e:
            self.log(f"❌ 保存失败: {str(e)}")
            messagebox.showerror("保存错误", f"保存配置时发生错误：\n{str(e)}")

    def _get_current_results(self) -> Dict:
        """获取当前概率结果"""
        results = {}
        try:
            if hasattr(self, 'tree') and self.tree:
                for item in self.tree.get_children():
                    values = self.tree.item(item)['values']
                    if values and len(values) >= 4:
                        player_text = values[0]
                        if '玩家' in player_text:
                            player_num = int(player_text.replace('玩家', ''))
                            results[player_num] = {
                                '狼人概率': values[1],
                                '神民概率': values[2],
                                '平民概率': values[3],
                                '所在三角': values[4] if len(values) > 4 else ''
                            }
        except Exception as e:
            self.log(f"获取结果时出错: {e}")
        return results

    def _get_ui_state(self) -> Dict:
        """获取当前UI状态"""
        state = {
            "selected_player": self.player_var.get() if hasattr(self, 'player_var') else "",
            "weight_selected_player": self.weight_player_var.get() if hasattr(self, 'weight_player_var') else "",
            "speech_selected_player": self.speech_player_var.get() if hasattr(self, 'speech_player_var') else "",
            "speech_selected_round": self.speech_round_var.get() if hasattr(self, 'speech_round_var') else "",
            "current_tab": None,
            "current_category_tab": None
        }

        # 获取当前选中的主标签页
        try:
            if hasattr(self, 'main_paned'):
                pass  # PanedWindow不直接支持获取当前标签页
        except:
            pass

        # 获取当前选中的身份分类标签页
        try:
            if hasattr(self, 'role_notebook'):
                current = self.role_notebook.index(self.role_notebook.select())
                state["current_category_tab"] = current
        except:
            pass

        return state

    def load_config(self):
        """加载完整配置 - 恢复所有程序状态"""
        try:
            from tkinter import filedialog
            filename = filedialog.askopenfilename(
                filetypes=[
                    ("配置文件", "*.json"),
                    ("备份文件", "*.bak"),
                    ("所有文件", "*.*")
                ],
                title="加载完整配置"
            )

            if not filename:  # 用户取消
                return

            # 从文件加载
            with open(filename, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # 检查版本兼容性
            saved_version = config_data.get("version", "1.0")
            self.log(f"加载配置: 版本 {saved_version}, 保存于 {config_data.get('save_time', '未知')}")

            # 1. 加载游戏配置（如果存在）
            if "game_config" in config_data:
                gc = config_data["game_config"]
                # 注意：这里不重新创建config，因为游戏配置通常是固定的
                self.log(f"  游戏配置: {gc.get('total_players')}人局")

            # 2. 加载核心数据
            if "role_manager" in config_data:
                rm_data = config_data["role_manager"]

                # 清空现有数据
                self.role_manager.clear_all()

                # 加载已知身份
                if "known_info" in rm_data:
                    self.role_manager.known_info = {
                        int(k): v for k, v in rm_data["known_info"].items()
                    }

                # 加载行为权重
                if "behavior_weights" in rm_data:
                    self.role_manager.behavior_weights = {
                        int(k): v for k, v in rm_data["behavior_weights"].items()
                    }

                # 加载自定义标签
                if "custom_tags" in rm_data:
                    # 合并标签，不覆盖现有的
                    for tag_name, tag_value in rm_data["custom_tags"].items():
                        self.role_manager.custom_tags[tag_name] = tag_value

                self.log(f"  加载身份: {len(self.role_manager.known_info)}个")
                self.log(f"  加载权重: {len(self.role_manager.behavior_weights)}个")
                self.log(f"  加载标签: {len(rm_data.get('custom_tags', {}))}个")

            # 3. 加载算法设置
            if "algorithm_settings" in config_data:
                algo = config_data["algorithm_settings"]
                self.simulation_count = algo.get("simulation_count", 50000)
                self.use_triangle_law = algo.get("use_triangle_law", True)
                self.use_behavior_weight = algo.get("use_behavior_weight", True)

                # 更新UI控件
                self.sim_var.set(str(self.simulation_count))
                self.use_triangle_var.set(self.use_triangle_law)
                self.use_weight_var.set(self.use_behavior_weight)
                self.update_algo_settings()
                self.sim_label.config(text=f"模拟次数: {self.simulation_count}")

            # 4. 加载发言记录
            if "speech_records" in config_data:
                self.speech_records.clear()
                for key_str, content in config_data["speech_records"].items():
                    try:
                        # key_str格式: "player_round"
                        player_str, round_text = key_str.split('_', 1)
                        player = int(player_str)
                        self.speech_records[(player, round_text)] = content
                    except:
                        continue

                self.update_speech_listbox()
                self.log(f"  加载发言: {len(self.speech_records)}条")

            # 5. 更新所有UI组件
            self.update_info_listbox()
            self.update_weight_listbox()
            self.update_player_cards()
            self.update_triangle_analysis()
            self.update_status()

            # 6. 加载概率结果（如果存在）
            if "probability_results" in config_data:
                results = config_data["probability_results"]
                # 清空现有结果
                for item in self.tree.get_children():
                    self.tree.delete(item)

                # 重新插入结果
                for player_num, probs in results.items():
                    player_num = int(player_num)
                    tag = 'medium'
                    wolf_prob_str = probs.get('狼人概率', '0%')
                    try:
                        wolf_val = float(wolf_prob_str.strip('%')) / 100
                        if wolf_val > 0.4:
                            tag = 'high'
                        elif wolf_val > 0.25:
                            tag = 'medium'
                        else:
                            tag = 'low'
                    except:
                        pass

                    self.tree.insert('', tk.END, values=(
                        f"玩家{player_num}",
                        probs.get('狼人概率', '0%'),
                        probs.get('神民概率', '0%'),
                        probs.get('平民概率', '0%'),
                        probs.get('所在三角', '')
                    ), tags=(tag,))

            # 7. 加载三角形分析内容（如果存在）
            if "triangle_analysis" in config_data and self.triangle_status_text:
                self.triangle_status_text.delete(1.0, tk.END)
                self.triangle_status_text.insert(1.0, config_data["triangle_analysis"])

            # 8. 加载日志内容（如果存在）
            if "log_content" in config_data and self.log_text:
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(1.0, config_data["log_content"])

            # 9. 加载基础定律显示（如果存在）
            if "law_display" in config_data and self.law_right_text:
                self.law_right_text.delete(1.0, tk.END)
                self.law_right_text.insert(1.0, config_data["law_display"])

            # 10. 加载主题
            if "theme" in config_data:
                saved_theme = config_data["theme"]
                if saved_theme != self.theme_manager.current_theme:
                    self.theme_manager.toggle()
                    self.theme_manager.apply_to_style(ttk.Style())
                    self.root.configure(bg=self.theme_manager.colors['bg'])
                    for card in self.player_cards.values():
                        card.colors = self.theme_manager.colors
                        card.update(self.role_manager.known_info)
                    self.refresh_ui_colors()

            # 11. 加载UI状态
            if "ui_state" in config_data:
                ui_state = config_data["ui_state"]

                # 恢复选中的玩家
                if ui_state.get("selected_player") and hasattr(self, 'player_var'):
                    self.player_var.set(ui_state["selected_player"])

                if ui_state.get("weight_selected_player") and hasattr(self, 'weight_player_var'):
                    self.weight_player_var.set(ui_state["weight_selected_player"])

                if ui_state.get("speech_selected_player") and hasattr(self, 'speech_player_var'):
                    self.speech_player_var.set(ui_state["speech_selected_player"])

                if ui_state.get("speech_selected_round") and hasattr(self, 'speech_round_var'):
                    self.speech_round_var.set(ui_state["speech_selected_round"])

                # 恢复选中的分类标签页
                if ui_state.get("current_category_tab") is not None and hasattr(self, 'role_notebook'):
                    try:
                        self.role_notebook.select(ui_state["current_category_tab"])
                    except:
                        pass

            # 12. 更新标签下拉框
            tag_list = [""] + list(self.role_manager.custom_tags.keys())
            self.tag_preset_combo['values'] = tag_list

            self.log(f"✅ 完整配置加载完成: {filename}")
            messagebox.showinfo("加载成功", f"配置已加载：\n{filename}\n\n"
                                            f"包含：\n"
                                            f"• 身份信息 {len(self.role_manager.known_info)} 条\n"
                                            f"• 权重设置 {len(self.role_manager.behavior_weights)} 条\n"
                                            f"• 发言记录 {len(self.speech_records)} 条\n"
                                            f"• 自定义标签 {len(self.role_manager.custom_tags)} 个")

        except Exception as e:
            self.log(f"❌ 加载失败: {str(e)}")
            messagebox.showerror("加载错误", f"加载配置时发生错误：\n{str(e)}\n\n"
                                             f"请确保文件格式正确。")


    # ========== 计算方法 ==========

    def run_with_progress(self, calc_func, title):
        """带进度条运行计算"""
        progress = ProgressDialog(self.root, title=title)

        def update_progress(value):
            return progress.update(value)

        try:
            results = calc_func(update_progress)
            progress.close()
            return results
        except Exception as e:
            progress.close()
            raise e

    def run_monte_carlo(self):
        """运行蒙特卡洛模拟"""
        try:
            self.log(f"开始蒙特卡洛模拟，次数: {self.simulation_count}")

            for item in self.tree.get_children():
                self.tree.delete(item)

            unknown_players = [p for p in self.config.players if p not in self.role_manager.known_info]
            if not unknown_players:
                messagebox.showinfo("提示", "没有未知玩家需要计算")
                return

            results = self.run_with_progress(
                lambda cb: self.calculator.monte_carlo_numpy(self.simulation_count, cb),
                "蒙特卡洛模拟"
            )

            for player, probs in results.items():
                triangle = self.config.get_player_triangle(player)
                wolf_prob = probs['狼人']

                if wolf_prob > 0.4:
                    tag = 'high'
                elif wolf_prob > 0.25:
                    tag = 'medium'
                else:
                    tag = 'low'

                self.tree.insert('', tk.END, values=(
                    f"玩家{player}",
                    f"{wolf_prob:.1%}",
                    f"{probs['神民']:.1%}",
                    f"{probs['平民']:.1%}",
                    triangle
                ), tags=(tag,))

                if player in self.player_cards:
                    self.player_cards[player].set_probabilities(
                        wolf_prob, probs['神民'], probs['平民']
                    )

            self.log("蒙特卡洛模拟完成")

        except Exception as e:
            messagebox.showerror("错误", f"计算过程中出现错误: {str(e)}")
            self.log(f"错误: {str(e)}")

    def run_triangle_law(self):
        """运行三角定律计算"""
        try:
            self.log(f"开始三角定律计算，次数: {self.simulation_count}")

            for item in self.tree.get_children():
                self.tree.delete(item)

            unknown_players = [p for p in self.config.players if p not in self.role_manager.known_info]
            if not unknown_players:
                messagebox.showinfo("提示", "没有未知玩家需要计算")
                return

            results = self.run_with_progress(
                lambda cb: self.calculator.triangle_law_simulation(self.simulation_count, cb),
                "三角定律计算"
            )

            for player, probs in results.items():
                triangle = self.config.get_player_triangle(player)
                wolf_prob = probs['狼人']

                if wolf_prob > 0.4:
                    tag = 'high'
                elif wolf_prob > 0.25:
                    tag = 'medium'
                else:
                    tag = 'low'

                self.tree.insert('', tk.END, values=(
                    f"玩家{player}",
                    f"{wolf_prob:.1%}",
                    f"{probs['神职']:.1%}",
                    f"{probs['平民']:.1%}",
                    triangle
                ), tags=(tag,))

                if player in self.player_cards:
                    self.player_cards[player].set_probabilities(
                        wolf_prob, probs['神职'], probs['平民']
                    )

            self.log("三角定律计算完成")

        except Exception as e:
            messagebox.showerror("错误", f"计算过程中出现错误: {str(e)}")
            self.log(f"错误: {str(e)}")

    def run_bayesian_update(self):
        """运行贝叶斯更新"""
        try:
            self.log("开始贝叶斯更新计算")

            for item in self.tree.get_children():
                self.tree.delete(item)

            unknown_players = [p for p in self.config.players if p not in self.role_manager.known_info]
            if not unknown_players:
                messagebox.showinfo("提示", "没有未知玩家需要计算")
                return

            results = self.calculator.bayesian_update()

            for player, probs in sorted(results.items(), key=lambda x: x[1]['狼人'], reverse=True):
                triangle = self.config.get_player_triangle(player)
                wolf_prob = probs['狼人']

                if wolf_prob > 0.4:
                    tag = 'high'
                elif wolf_prob > 0.25:
                    tag = 'medium'
                else:
                    tag = 'low'

                self.tree.insert('', tk.END, values=(
                    f"玩家{player}",
                    f"{wolf_prob:.1%}",
                    f"{probs['神职']:.1%}",
                    f"{probs['平民']:.1%}",
                    triangle
                ), tags=(tag,))

                if player in self.player_cards:
                    self.player_cards[player].set_probabilities(
                        wolf_prob, probs['神职'], probs['平民']
                    )

            self.log("贝叶斯更新完成")

        except Exception as e:
            messagebox.showerror("错误", f"计算过程中出现错误: {str(e)}")
            self.log(f"错误: {str(e)}")

    def run_comprehensive_analysis(self):
        """运行综合分析"""
        try:
            self.log(f"开始综合分析，次数: {self.simulation_count}")

            for item in self.tree.get_children():
                self.tree.delete(item)

            unknown_players = [p for p in self.config.players if p not in self.role_manager.known_info]
            if not unknown_players:
                messagebox.showinfo("提示", "没有未知玩家需要计算")
                return

            results = self.run_with_progress(
                lambda cb: self.calculator.comprehensive_analysis(
                    self.simulation_count,
                    self.use_triangle_law,
                    self.use_behavior_weight,
                    cb
                ),
                "综合分析"
            )

            for player, probs in sorted(results.items(), key=lambda x: x[1]['狼人'], reverse=True):
                triangle = self.config.get_player_triangle(player)
                wolf_prob = probs['狼人']

                if wolf_prob > 0.4:
                    tag = 'high'
                elif wolf_prob > 0.25:
                    tag = 'medium'
                else:
                    tag = 'low'

                self.tree.insert('', tk.END, values=(
                    f"玩家{player}",
                    f"{wolf_prob:.1%}",
                    f"{probs['神民']:.1%}",
                    f"{probs['平民']:.1%}",
                    triangle
                ), tags=(tag,))

                if player in self.player_cards:
                    self.player_cards[player].set_probabilities(
                        wolf_prob, probs['神民'], probs['平民']
                    )

            self.log("综合分析完成")

        except Exception as e:
            messagebox.showerror("错误", f"计算过程中出现错误: {str(e)}")
            self.log(f"错误: {str(e)}")


# ========== 程序入口 ==========

def main():
    root = tk.Tk()
    app = WerewolfProbabilityApp(root)
    root.mainloop()


if __name__ == "__main__":
    # 检查NumPy是否可用
    try:
        import numpy as np
    except ImportError:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("错误", "请先安装NumPy：pip install numpy")
        root.destroy()
        exit(1)

    main()