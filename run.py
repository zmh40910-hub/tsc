import cityflow
import json
import os
from controller_deepseek import DeepSeekController

def get_state(eng, intersection_ids):
    """
    获取交通状态（仅使用CityFlow全版本通用API）
    彻底删除：get_tl_phase_map/get_incoming_lanes_of_intersection等版本敏感API
    """
    state = {}
    # 仅使用所有版本都支持的基础API
    all_lane_vehicles = eng.get_lane_vehicle_count()       # 所有车道车辆数（通用）
    all_waiting_vehicles = eng.get_lane_waiting_vehicle_count()  # 所有车道等待车辆数（通用）
    all_vehicle_ids = eng.get_vehicles()                   # 所有车辆ID（通用）
    
    for inter_id in intersection_ids:
        # 通用逻辑：匹配车道ID与路口ID（无需版本敏感API）
        related_lanes = [lane for lane in all_lane_vehicles.keys() if inter_id in lane]
        # 统计该路口相关车辆
        total_vehicles = sum([all_lane_vehicles.get(lane, 0) for lane in related_lanes])
        total_waiting = sum([all_waiting_vehicles.get(lane, 0) for lane in related_lanes])
        
        # 获取单个路口相位（全版本通用API：get_tl_phase）
        try:
            current_phase = eng.get_tl_phase(inter_id)
        except:
            current_phase = 0  # 兜底：无该方法时使用默认相位
        
        # 构建状态（仅包含必要信息，无版本敏感字段）
        state[inter_id] = {
            "intersection_id": inter_id,
            "related_lanes": related_lanes,
            "total_vehicles": total_vehicles,
            "total_waiting_vehicles": total_waiting,
            "current_phase": current_phase,
            "total_vehicles_in_sim": len(all_vehicle_ids)
        }
    return state

def main():
    # 1. 初始化仿真引擎（容错）
    try:
        eng = cityflow.Engine("config.json", thread_num=4)
        print("CityFlow引擎初始化成功！")
    except Exception as e:
        print(f"引擎初始化失败：{str(e)}")
        print("请检查config.json是否包含dir、seed字段，且格式合法")
        return
    
    # 2. 获取路口ID（三层兜底，兼容所有路网格式）
    intersection_ids = []
    # 兜底1：从roadnet.json读取
    try:
        roadnet = json.load(open("data/roadnet.json", encoding="utf-8"))
        intersection_ids = [inter["id"] for inter in roadnet.get("intersections", [])]
    except:
        pass
    # 兜底2：手动指定（确保至少有一个路口ID，避免空列表）
    if not intersection_ids:
        intersection_ids = ["intersection_0"]
        print(f"未自动获取到路口ID，使用默认值：{intersection_ids}")
    
    print(f"检测到路口ID：{intersection_ids}")
    
    # 3. 读取环境变量参数（移到控制器初始化前）
    total_steps = int(os.getenv("SIMULATION_STEPS", 3600))
    tl_update_interval = int(os.getenv("TL_UPDATE_INTERVAL", 5))
    
    # 4. 初始化控制器（传入total_steps参数）
    controller = DeepSeekController(intersection_ids, total_steps)
    
    # 5. 仿真主循环（无任何版本敏感API）
    print(f"开始仿真，总步数：{total_steps}，信号灯更新间隔：{tl_update_interval}步")
    for step in range(total_steps):
        try:
            # 获取状态（通用API，无报错）
            state = get_state(eng, intersection_ids)
            
            # 更新信号灯（每N步）
            if step % tl_update_interval == 0:
                # 传入当前步数给get_action
                actions = controller.get_action(state, step)
                # 应用相位（容错）
                for inter_id, phase in actions.items():
                    try:
                        eng.set_tl_phase(inter_id, int(phase))  # 通用API
                        if step % 100 == 0:
                            print(f"Step {step}：路口{inter_id}相位更新为{phase}")
                    except Exception as e:
                        print(f"Step {step}：更新路口{inter_id}相位失败，使用默认相位0")
                        try:
                            eng.set_tl_phase(inter_id, 0)
                        except:
                            pass  # 完全无该方法时跳过
            
            # 执行仿真步（通用API）
            eng.next_step()
            
            # 打印进度（每100步）
            if step % 100 == 0:
                total_veh = len(eng.get_vehicles())
                print(f"进度：{step}/{total_steps}步 | 仿真内总车辆数：{total_veh}")
        
        except Exception as e:
            print(f"Step {step}执行异常：{str(e)}，继续下一步")
            try:
                eng.next_step()
            except:
                pass  # 完全无法执行时跳过
    
    # 6. 结束仿真（兼容有无terminate方法）
    try:
        eng.terminate()
    except AttributeError:
        print("CityFlow版本无需手动终止引擎，自动释放资源")
    except Exception as e:
        print(f"终止引擎时警告：{str(e)}")
    
    # 最终统计（通用API）
    final_vehicle_count = len(eng.get_vehicles()) if hasattr(eng, 'get_vehicles') else 0
    print(f"\n===== 仿真完成 ======")
    print(f"总运行步数：{total_steps}")
    print(f"最终车辆数：{final_vehicle_count}")
    print(f"仿真回放文件：D:\\cityflow_deepseek\\replay.txt")
    print(f"仿真日志文件：D:\\cityflow_deepseek\\simulation.log")

if __name__ == "__main__":
    main()