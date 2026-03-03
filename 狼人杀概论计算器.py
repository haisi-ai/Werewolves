import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import random
from collections import defaultdict
import math


class WerewolfProbabilityGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("狼人杀概率计算器 v2.0")
        self.root.geometry("1200x700")
        self.root.resizable(True, True)

        # 游戏配置
        self.total_players = 12
        self.wolves = 4
        self.gods = 4
        self.villagers = 4
        self.players = list(range(1, 13))

        # 已知信息存储
        self.known_info = {}
        self.behavior_weights = {}

        # 定义三角形分组
        self.triangles = {
            "三角形1": {1, 5, 9},
            "三角形2": {2, 6, 10},
            "三角形3": {3, 7, 11},
            "三角形4": {4, 8, 12}
        }

        # 定义四角分组
        self.corner_groups = [
            {1, 7, 4, 10},
            {2, 8, 5, 11},
            {3, 9, 6, 12}
        ]

        # 定义三行分组（用于三行定律）
        self.rows = [
            {1, 7}, {2, 8}, {3, 9}, {4, 10}, {5, 11}, {6, 12}
        ]
        self.row_combinations = [
            [self.rows[0], self.rows[1], self.rows[2]],
            [self.rows[1], self.rows[2], self.rows[3]],
            [self.rows[2], self.rows[3], self.rows[4]],
            [self.rows[3], self.rows[4], self.rows[5]],
            [self.rows[4], self.rows[5], self.rows[0]],
            [self.rows[5], self.rows[0], self.rows[1]]
        ]

        self.setup_ui()

    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # 标题
        title_label = ttk.Label(main_frame, text="🕵️ 狼人杀概率计算器",
                                font=("微软雅黑", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # 左侧：玩家信息输入区
        left_frame = ttk.LabelFrame(main_frame, text="玩家信息输入", padding="10")
        left_frame.grid(row=1, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)

        self.create_player_input_area(left_frame)

        # 中间：概率显示区
        middle_frame = ttk.LabelFrame(main_frame, text="概率计算结果", padding="10")
        middle_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        middle_frame.columnconfigure(0, weight=1)
        middle_frame.rowconfigure(0, weight=1)

        self.create_result_area(middle_frame)

        # 右侧：控制区和统计定律
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)

        self.create_control_area(right_frame)
        self.create_law_area(right_frame)

        # 底部：日志区域
        bottom_frame = ttk.LabelFrame(main_frame, text="计算日志", padding="10")
        bottom_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(bottom_frame, height=6, width=100)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 初始化日志
        self.log("系统初始化完成，请输入已知玩家信息")

    def create_player_input_area(self, parent):
        """创建玩家输入区域"""
        # 玩家编号选择
        ttk.Label(parent, text="玩家编号:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.player_var = tk.StringVar()
        self.player_combo = ttk.Combobox(parent, textvariable=self.player_var,
                                         values=self.players, state="readonly", width=10)
        self.player_combo.grid(row=0, column=1, pady=5, padx=5)
        self.player_combo.bind('<<ComboboxSelected>>', self.on_player_selected)

        # 身份选择
        ttk.Label(parent, text="身份信息:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.role_var = tk.StringVar()
        roles = ['金水', '查杀', '预言家', '女巫', '猎人', '白痴', '平民', '狼人']
        self.role_combo = ttk.Combobox(parent, textvariable=self.role_var,
                                       values=roles, state="readonly", width=10)
        self.role_combo.grid(row=1, column=1, pady=5, padx=5)

        # 添加按钮
        ttk.Button(parent, text="添加已知信息", command=self.add_known_info).grid(row=2, column=0, columnspan=2,
                                                                                  pady=10)

        # 行为权重设置
        ttk.Label(parent, text="行为权重（可选）:", font=("微软雅黑", 10, "bold")).grid(row=3, column=0, columnspan=2,
                                                                                      pady=10)

        ttk.Label(parent, text="狼人权重:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.wolf_weight = ttk.Entry(parent, width=10)
        self.wolf_weight.insert(0, "1.0")
        self.wolf_weight.grid(row=4, column=1, pady=2)

        ttk.Label(parent, text="好人权重:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.good_weight = ttk.Entry(parent, width=10)
        self.good_weight.insert(0, "1.0")
        self.good_weight.grid(row=5, column=1, pady=2)

        ttk.Button(parent, text="添加行为权重", command=self.add_behavior_weight).grid(row=6, column=0, columnspan=2,
                                                                                       pady=10)

        # 已知信息列表
        ttk.Label(parent, text="已添加信息:", font=("微软雅黑", 10, "bold")).grid(row=7, column=0, columnspan=2,
                                                                                  pady=10)

        self.info_listbox = tk.Listbox(parent, height=8, width=25)
        self.info_listbox.grid(row=8, column=0, columnspan=2, pady=5)

        # 删除按钮
        ttk.Button(parent, text="删除选中", command=self.delete_selected_info).grid(row=9, column=0, pady=5)
        ttk.Button(parent, text="清空所有", command=self.clear_all_info).grid(row=9, column=1, pady=5)

    def create_result_area(self, parent):
        """创建结果显示区域"""
        # 创建Treeview来显示概率结果
        columns = ('玩家', '狼人概率', '神民概率', '平民概率')
        self.tree = ttk.Treeview(parent, columns=columns, show='headings', height=15)

        # 设置列标题
        self.tree.heading('玩家', text='玩家编号')
        self.tree.heading('狼人概率', text='狼人概率')
        self.tree.heading('神民概率', text='神民概率')
        self.tree.heading('平民概率', text='平民概率')

        # 设置列宽
        self.tree.column('玩家', width=80, anchor='center')
        self.tree.column('狼人概率', width=120, anchor='center')
        self.tree.column('神民概率', width=120, anchor='center')
        self.tree.column('平民概率', width=120, anchor='center')

        # 添加滚动条
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 绑定选择事件
        self.tree.bind('<<TreeviewSelect>>', self.on_result_select)

    def create_control_area(self, parent):
        """创建控制区域"""
        control_frame = ttk.LabelFrame(parent, text="计算控制", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        ttk.Label(control_frame, text="模拟次数:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.sim_var = tk.StringVar(value="50000")
        sim_spinbox = ttk.Spinbox(control_frame, from_=1000, to=100000, textvariable=self.sim_var, width=10)
        sim_spinbox.grid(row=0, column=1, pady=5, padx=5)

        # 计算按钮
        ttk.Button(control_frame, text="🎲 蒙特卡洛模拟",
                   command=self.run_monte_carlo, width=20).grid(row=1, column=0, columnspan=2, pady=5)

        ttk.Button(control_frame, text="📐 三角形定律计算",
                   command=self.run_triangle_calc, width=20).grid(row=2, column=0, columnspan=2, pady=5)

        ttk.Button(control_frame, text="📊 贝叶斯更新",
                   command=self.run_bayesian_update, width=20).grid(row=3, column=0, columnspan=2, pady=5)

        ttk.Button(control_frame, text="📈 综合所有算法",
                   command=self.run_comprehensive_analysis, width=20).grid(row=4, column=0, columnspan=2, pady=5)

    def create_law_area(self, parent):
        """创建统计定律显示区域"""
        law_frame = ttk.LabelFrame(parent, text="基础统计定律", padding="10")
        law_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # 显示各种定律的初始概率
        self.law_text = tk.Text(law_frame, height=12, width=30, wrap=tk.WORD)
        self.law_text.grid(row=0, column=0, pady=5)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(law_frame, orient=tk.VERTICAL, command=self.law_text.yview)
        self.law_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 计算并显示基础概率
        self.calculate_basic_probabilities()

    def calculate_basic_probabilities(self):
        """计算基础概率（先验概率）"""
        self.law_text.delete(1.0, tk.END)

        # 计算三角形分布概率
        self.law_text.insert(tk.END, "📐 三角形定律（4狼分布）:\n")
        tri_probs = self.calculate_triangle_probabilities()
        for case, prob in tri_probs.items():
            self.law_text.insert(tk.END, f"  {case}: {prob:.3f}\n")

        # 计算三行定律概率
        self.law_text.insert(tk.END, "\n📏 三行定律:\n")
        row_prob = self.calculate_row_probability()
        self.law_text.insert(tk.END, f"  连续三行有≥3狼: {row_prob:.3f}\n")

        # 计算四角定律概率
        self.law_text.insert(tk.END, "\n🔲 四角定律:\n")
        corner_probs = self.calculate_corner_probabilities()
        for k, v in corner_probs.items():
            self.law_text.insert(tk.END, f"  单组有{k}狼: {v:.6f}\n")

        # 基础概率
        self.law_text.insert(tk.END, f"\n🎲 基础概率:\n")
        self.law_text.insert(tk.END, f"  任意玩家是狼: {self.wolves / self.total_players:.3f}\n")

    def calculate_triangle_probabilities(self, num_simulations=100000):
        """计算三角形分布概率"""
        case1 = case2 = case3 = case4 = 0

        for _ in range(num_simulations):
            wolves = set(random.sample(self.players, self.wolves))
            counts = []
            for tri in self.triangles.values():
                counts.append(len(wolves.intersection(tri)))

            if counts.count(2) == 2 and counts.count(0) == 2:
                case1 += 1
            elif counts.count(2) == 1 and counts.count(1) == 2:
                case2 += 1
            elif counts.count(1) == 4:
                case3 += 1
            elif 3 in counts:
                case4 += 1

        return {
            "两个三角各2狼": case1 / num_simulations,
            "一三角2狼,两三角1狼": case2 / num_simulations,
            "四个三角各1狼": case3 / num_simulations,
            "一三角有3狼": case4 / num_simulations
        }

    def calculate_row_probability(self, num_simulations=100000):
        """计算三行定律概率"""
        case_count = 0

        for _ in range(num_simulations):
            wolves = set(random.sample(self.players, self.wolves))
            for combo in self.row_combinations:
                combined = set().union(*combo)
                if len(wolves.intersection(combined)) >= 3:
                    case_count += 1
                    break

        return case_count / num_simulations

    def calculate_corner_probabilities(self, num_simulations=100000):
        """计算四角定律概率"""
        counts = {4: 0, 3: 0, 2: 0, 1: 0}

        for _ in range(num_simulations):
            wolves = set(random.sample(self.players, self.wolves))
            for group in self.corner_groups:
                count = len(wolves.intersection(group))
                if count >= 1:
                    counts[count] += 1

        total = num_simulations * len(self.corner_groups)
        return {k: v / total for k, v in counts.items()}

    def on_player_selected(self, event):
        """玩家选择事件"""
        player = self.player_var.get()
        if player:
            # 如果该玩家已有信息，显示出来
            if int(player) in self.known_info:
                self.role_var.set(self.known_info[int(player)])
            else:
                self.role_var.set('')

    def add_known_info(self):
        """添加已知信息"""
        try:
            player = int(self.player_var.get())
            role = self.role_var.get()

            if not player or not role:
                messagebox.showwarning("警告", "请选择玩家编号和身份")
                return

            self.known_info[player] = role
            self.update_info_listbox()
            self.log(f"添加已知信息: 玩家{player} 是 {role}")

            # 清空选择
            self.player_var.set('')
            self.role_var.set('')

        except ValueError:
            messagebox.showerror("错误", "请选择有效的玩家编号")

    def add_behavior_weight(self):
        """添加行为权重"""
        try:
            player = int(self.player_var.get())
            wolf_weight = float(self.wolf_weight.get())
            good_weight = float(self.good_weight.get())

            if not player:
                messagebox.showwarning("警告", "请选择玩家编号")
                return

            self.behavior_weights[player] = {
                '狼人权重': wolf_weight,
                '好人权重': good_weight
            }

            self.update_info_listbox()
            self.log(f"添加行为权重: 玩家{player} 狼人权重={wolf_weight}, 好人权重={good_weight}")

        except ValueError:
            messagebox.showerror("错误", "请输入有效的权重数值")

    def update_info_listbox(self):
        """更新信息列表"""
        self.info_listbox.delete(0, tk.END)

        # 显示已知身份
        for player, role in sorted(self.known_info.items()):
            self.info_listbox.insert(tk.END, f"玩家{player}: {role}")

        # 显示行为权重
        for player, weights in self.behavior_weights.items():
            if player not in self.known_info:  # 避免重复显示
                self.info_listbox.insert(tk.END,
                                         f"玩家{player}: 权重(狼{weights['狼人权重']}, 好{weights['好人权重']})")

    def delete_selected_info(self):
        """删除选中的信息"""
        selection = self.info_listbox.curselection()
        if selection:
            text = self.info_listbox.get(selection[0])
            # 解析文本获取玩家编号
            try:
                player = int(text.split(':')[0].replace('玩家', ''))
                if player in self.known_info:
                    del self.known_info[player]
                    self.log(f"删除玩家{player}的已知信息")
                elif player in self.behavior_weights:
                    del self.behavior_weights[player]
                    self.log(f"删除玩家{player}的行为权重")
                self.update_info_listbox()
            except:
                pass

    def clear_all_info(self):
        """清空所有信息"""
        self.known_info.clear()
        self.behavior_weights.clear()
        self.update_info_listbox()
        self.log("已清空所有信息")

        # 清空结果显示
        for item in self.tree.get_children():
            self.tree.delete(item)

    def log(self, message):
        """添加日志"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def run_monte_carlo(self):
        """运行蒙特卡洛模拟"""
        try:
            sim_count = int(self.sim_var.get())
            self.log(f"开始蒙特卡洛模拟，次数: {sim_count}")

            # 清空之前的结果
            for item in self.tree.get_children():
                self.tree.delete(item)

            # 获取未知玩家
            unknown_players = [p for p in self.players if p not in self.known_info]

            if not unknown_players:
                messagebox.showinfo("提示", "没有未知玩家需要计算")
                return

            # 初始化计数器
            role_counts = {p: {'狼人': 0, '神民': 0, '平民': 0} for p in unknown_players}

            # 统计已知身份数量
            confirmed_wolves = sum(1 for v in self.known_info.values() if v in ['狼人', '查杀'])
            confirmed_gods = sum(1 for v in self.known_info.values() if v in ['预言家', '女巫', '猎人', '白痴'])
            confirmed_villagers = sum(1 for v in self.known_info.values() if v == '平民')
            confirmed_good = sum(1 for v in self.known_info.values() if v == '金水')

            remaining_wolves = self.wolves - confirmed_wolves
            remaining_gods = self.gods - confirmed_gods
            remaining_villagers = self.villagers - confirmed_villagers

            # 蒙特卡洛模拟
            for i in range(sim_count):
                # 分配剩余身份
                remaining_roles = ['狼人'] * remaining_wolves

                # 分配神民和平民（包括从金水中分配的）
                gods_to_add = remaining_gods
                villagers_to_add = remaining_villagers

                # 如果有金水，随机分配到神民和平民
                if confirmed_good > 0:
                    gods_from_good = random.randint(0, confirmed_good)
                    gods_to_add += gods_from_good
                    villagers_to_add += (confirmed_good - gods_from_good)

                remaining_roles.extend(['神民'] * gods_to_add)
                remaining_roles.extend(['平民'] * villagers_to_add)

                random.shuffle(remaining_roles)

                # 分配给未知玩家
                for player, role in zip(unknown_players, remaining_roles):
                    role_counts[player][role] += 1

                # 显示进度
                if (i + 1) % 10000 == 0:
                    self.log(f"模拟进度: {i + 1}/{sim_count}")

            # 显示结果
            for player in unknown_players:
                wolf_prob = role_counts[player]['狼人'] / sim_count
                god_prob = role_counts[player]['神民'] / sim_count
                vill_prob = role_counts[player]['平民'] / sim_count

                self.tree.insert('', tk.END, values=(
                    f"玩家{player}",
                    f"{wolf_prob:.2%}",
                    f"{god_prob:.2%}",
                    f"{vill_prob:.2%}"
                ))

            self.log("蒙特卡洛模拟完成")

        except Exception as e:
            messagebox.showerror("错误", f"计算过程中出现错误: {str(e)}")
            self.log(f"错误: {str(e)}")

    def run_triangle_calc(self):
        """运行三角形定律计算"""
        try:
            sim_count = int(self.sim_var.get())
            self.log(f"开始三角形定律计算，次数: {sim_count}")

            # 清空之前的结果
            for item in self.tree.get_children():
                self.tree.delete(item)

            unknown_players = [p for p in self.players if p not in self.known_info]

            if not unknown_players:
                messagebox.showinfo("提示", "没有未知玩家需要计算")
                return

            # 计算每个三角形的未知玩家数量
            triangle_unknown = {}
            for tri_name, tri_players in self.triangles.items():
                unknown_in_tri = [p for p in tri_players if p in unknown_players]
                triangle_unknown[tri_name] = unknown_in_tri

            # 计数器
            wolf_counts = defaultdict(int)

            # 统计已知狼人
            known_wolves = sum(1 for v in self.known_info.values() if v in ['狼人', '查杀'])
            remaining_wolves = self.wolves - known_wolves

            for i in range(sim_count):
                # 根据三角形分布分配狼人
                wolves_chosen = set()

                while len(wolves_chosen) < remaining_wolves:
                    # 选择权重较高的三角形
                    weights = []
                    players_pool = []

                    for player in unknown_players:
                        if player not in wolves_chosen:
                            # 找到玩家所在的三角形
                            for tri_name, tri_players in self.triangles.items():
                                if player in tri_players:
                                    # 权重 = 该三角形中未知玩家的数量
                                    weight = len(
                                        [p for p in tri_players if p in unknown_players and p not in wolves_chosen])
                                    weights.append(max(1, weight))
                                    players_pool.append(player)
                                    break

                    if weights:
                        # 根据权重选择
                        total = sum(weights)
                        probs = [w / total for w in weights]
                        chosen = random.choices(players_pool, weights=probs)[0]
                        wolves_chosen.add(chosen)

                # 记录结果
                for wolf in wolves_chosen:
                    wolf_counts[wolf] += 1

            # 显示结果
            for player in unknown_players:
                prob = wolf_counts[player] / sim_count
                # 在树形视图中显示，只显示狼人概率
                self.tree.insert('', tk.END, values=(
                    f"玩家{player}",
                    f"{prob:.2%}",
                    "-",
                    "-"
                ))

            self.log("三角形定律计算完成")

        except Exception as e:
            messagebox.showerror("错误", f"计算过程中出现错误: {str(e)}")

    def run_bayesian_update(self):
        """运行贝叶斯更新"""
        try:
            self.log("开始贝叶斯更新计算")

            # 清空之前的结果
            for item in self.tree.get_children():
                self.tree.delete(item)

            unknown_players = [p for p in self.players if p not in self.known_info]

            if not unknown_players:
                messagebox.showinfo("提示", "没有未知玩家需要计算")
                return

            # 基础先验概率
            known_wolves = sum(1 for v in self.known_info.values() if v in ['狼人', '查杀'])
            remaining_wolves = self.wolves - known_wolves
            base_prob = remaining_wolves / len(unknown_players)

            results = {}

            for player in unknown_players:
                prob = base_prob

                # 如果有行为权重，进行贝叶斯更新
                if player in self.behavior_weights:
                    weights = self.behavior_weights[player]
                    wolf_factor = weights.get('狼人权重', 1.0)
                    good_factor = weights.get('好人权重', 1.0)

                    # 贝叶斯公式
                    numerator = base_prob * wolf_factor
                    denominator = numerator + (1 - base_prob) * good_factor
                    prob = numerator / denominator if denominator > 0 else base_prob

                results[player] = prob

            # 显示结果
            for player, prob in sorted(results.items(), key=lambda x: x[1], reverse=True):
                self.tree.insert('', tk.END, values=(
                    f"玩家{player}",
                    f"{prob:.2%}",
                    "-",
                    "-"
                ))

            self.log("贝叶斯更新完成")

        except Exception as e:
            messagebox.showerror("错误", f"计算过程中出现错误: {str(e)}")

    def run_comprehensive_analysis(self):
        """运行综合分析（结合所有算法）"""
        try:
            sim_count = int(self.sim_var.get())
            self.log(f"开始综合分析，次数: {sim_count}")

            # 清空之前的结果
            for item in self.tree.get_children():
                self.tree.delete(item)

            unknown_players = [p for p in self.players if p not in self.known_info]

            if not unknown_players:
                messagebox.showinfo("提示", "没有未知玩家需要计算")
                return

            # 初始化综合得分
            comprehensive_scores = {p: 0 for p in unknown_players}

            # 1. 蒙特卡洛得分
            self.log("计算蒙特卡洛得分...")
            mc_scores = self.get_monte_carlo_scores(unknown_players, sim_count // 2)

            # 2. 三角形定律得分
            self.log("计算三角形定律得分...")
            tri_scores = self.get_triangle_scores(unknown_players, sim_count // 2)

            # 3. 贝叶斯得分（行为权重）
            self.log("计算行为权重得分...")
            bayes_scores = self.get_bayes_scores(unknown_players)

            # 综合评分（加权平均）
            for player in unknown_players:
                comprehensive_scores[player] = (
                        mc_scores[player] * 0.4 +  # 蒙特卡洛权重40%
                        tri_scores[player] * 0.3 +  # 三角形定律权重30%
                        bayes_scores[player] * 0.3  # 贝叶斯权重30%
                )

            # 显示结果
            for player, score in sorted(comprehensive_scores.items(), key=lambda x: x[1], reverse=True):
                self.tree.insert('', tk.END, values=(
                    f"玩家{player}",
                    f"{score:.2%}",
                    f"{mc_scores[player]:.2%}",
                    f"{bayes_scores[player]:.2%}"
                ))

            self.log("综合分析完成")

        except Exception as e:
            messagebox.showerror("错误", f"计算过程中出现错误: {str(e)}")

    def get_monte_carlo_scores(self, unknown_players, sim_count):
        """获取蒙特卡洛得分"""
        role_counts = {p: 0 for p in unknown_players}

        # 统计已知身份
        confirmed_wolves = sum(1 for v in self.known_info.values() if v in ['狼人', '查杀'])
        confirmed_gods = sum(1 for v in self.known_info.values() if v in ['预言家', '女巫', '猎人', '白痴'])
        confirmed_villagers = sum(1 for v in self.known_info.values() if v == '平民')
        confirmed_good = sum(1 for v in self.known_info.values() if v == '金水')

        remaining_wolves = self.wolves - confirmed_wolves

        for _ in range(sim_count):
            # 随机选择狼人
            wolves = set(random.sample(unknown_players, remaining_wolves))
            for wolf in wolves:
                role_counts[wolf] += 1

        return {p: role_counts[p] / sim_count for p in unknown_players}

    def get_triangle_scores(self, unknown_players, sim_count):
        """获取三角形定律得分"""
        wolf_counts = defaultdict(int)

        known_wolves = sum(1 for v in self.known_info.values() if v in ['狼人', '查杀'])
        remaining_wolves = self.wolves - known_wolves

        for _ in range(sim_count):
            wolves = set(random.sample(unknown_players, remaining_wolves))

            # 检查三角形分布
            for tri_name, tri_players in self.triangles.items():
                wolves_in_tri = wolves.intersection(tri_players)
                if len(wolves_in_tri) >= 2:  # 三角形有2狼以上，给这些狼加分
                    for wolf in wolves_in_tri:
                        wolf_counts[wolf] += 1

        max_count = max(wolf_counts.values()) if wolf_counts else 1
        return {p: wolf_counts.get(p, 0) / max_count for p in unknown_players}

    def get_bayes_scores(self, unknown_players):
        """获取贝叶斯得分"""
        known_wolves = sum(1 for v in self.known_info.values() if v in ['狼人', '查杀'])
        remaining_wolves = self.wolves - known_wolves
        base_prob = remaining_wolves / len(unknown_players)

        scores = {}
        for player in unknown_players:
            prob = base_prob
            if player in self.behavior_weights:
                weights = self.behavior_weights[player]
                wolf_factor = weights.get('狼人权重', 1.0)
                good_factor = weights.get('好人权重', 1.0)

                numerator = base_prob * wolf_factor
                denominator = numerator + (1 - base_prob) * good_factor
                prob = numerator / denominator if denominator > 0 else base_prob

            scores[player] = prob

        return scores

    def on_result_select(self, event):
        """结果选择事件"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            if values:
                self.log(f"查看结果: {values[0]} - 狼人概率{values[1]}")


def main():
    root = tk.Tk()
    app = WerewolfProbabilityGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()