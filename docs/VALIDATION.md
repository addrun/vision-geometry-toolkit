# 验证记录

日期：2026-11-14。

| 检查 | 结果 |
| --- | --- |
| pytest | 8 项通过：米/像素单位、非法数值、已知 ArUco 合成位姿、无标记、分辨率不匹配、演示产物 |
| 安装入口 | 在独立虚拟环境使用既有依赖，`pip install --no-deps --no-build-isolation -e .` 成功；`vision-geometry demo` 可调用 |
| CLI | demo、calibrate、range、evaluate、aruco 全部完成调用 |
| 尺寸先验示例 | 120 px / 0.2 m / 1 m 得焦距 600 px；60 px 回算 2 m |
| ArUco 合成示例 | ID 7，边长 0.12 m，估计 Z 为 0.4528301887 m；接近由图案尺度设定的 0.45 m |
| 可选 YOLO CLI | 既有 YOLO11n 权重 + 上游 bus 图片，保存 1 帧图片与 3 条完整目标的估距记录 |
| 文档图 | 从本次合成结果生成 SVG，并已渲染检查 |

记录中的合成 MAE、重投影 RMSE 不能解读为真实摄像头空间精度。
真实模型命令检查只验证推理和保存流程；类别高度来自示例先验，没有对这张图做真实测距验收。
上游示例照片、权重和推理图片均未纳入仓库。

系统依赖测试：Python 3.12.3、NumPy 1.26.4、OpenCV 4.6.0、pytest 7.4.4。
另在已有模型环境中通过安装入口与测试，OpenCV 4.10.0；可选推理使用 Ultralytics 8.3.141 / PyTorch 2.5.0。
模型环境报告 torch/torchvision 版本配套警告，本次推理完成不表示依赖组合经过全面兼容性验证。
Ubuntu 系统 Python 可能需要另装 `python3-venv`；本次安装检查使用已有 Python 环境创建的隔离 venv。

没有完成真实相机畸变标定、独立实测距离集评估、姿态稳定性与误差统计，也没有把这些写成已完成成果。
GitHub Actions 状态应查看仓库实际运行结果。
