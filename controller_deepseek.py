import requests
import json
import os
from dotenv import load_dotenv

# 加载.env文件中的基础配置
load_dotenv()

class DeepSeekController:
    def __init__(self, intersection_ids, total_steps):  # 保持原构造函数参数
        self.intersection_ids = intersection_ids
        self.total_steps = total_steps  # 存储总仿真步数
        # 从环境变量读取API核心配置
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.api_url = os.getenv("DEEPSEEK_API_URL", "https://api.siliconflow.cn/v1/chat/completions")
        # 核心：从环境变量读取模型名，默认使用deepseek-chat
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    def get_action(self, state, current_step):
        """调用DeepSeek API获取信号灯相位决策（包含时间步显示）"""
        # 输出当前时间步/总步数
        print(f"\n当前时间步：{current_step}/{self.total_steps}")
        print("向API发送请求...")
        
        # 构造提示词（适配交通状态）
        prompt = f"""
        你是交通信号灯控制专家，当前交通状态：{json.dumps(state, ensure_ascii=False)}
        请为以下路口分配信号灯相位（仅返回0/1/2/3等数字，无需解释）：
        {self.intersection_ids}
        要求：每个路口返回一个相位数字，格式为JSON，示例：{{"intersection_0":0, "intersection_1":1}}
        """
        
        # 构造API请求体（使用终端指定的模型名）
        payload = {
            "model": self.model,  # 动态使用环境变量传入的模型名
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 200
        }
        # 请求头（必须包含API密钥）
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            # 发送API请求
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()  # 抛出HTTP错误
            result = response.json()
            
            print("DeepSeek决策中...")
            # 解析返回结果
            content = result["choices"][0]["message"]["content"]
            actions = json.loads(content)
            # 兜底：确保所有路口都有相位
            for inter_id in self.intersection_ids:
                if inter_id not in actions:
                    actions[inter_id] = 0
            
            print(f"DeepSeek选择相位为：{json.dumps(actions, ensure_ascii=False)}")
            return actions
        
        except Exception as e:
            print(f"API请求失败（模型：{self.model}）: {str(e)}")
            print("使用默认相位1")
            default_actions = {inter_id: 1 for inter_id in self.intersection_ids}
            print(f"默认选择相位为：{json.dumps(default_actions, ensure_ascii=False)}")
            return default_actions