# 来源与工作边界

本仓库由 shhr 的本地视觉学习实验整理：

| 原实验内容 | 发布版内容 |
| --- | --- |
| `ultralytics-main/destence_decet` 的尺寸先验估距、焦距校准和距离叠字 | 提取独立几何模块，统一米/像素单位，JSON 配置，CSV 评估，按需 YOLO 推理 |
| `ros2_ws/arcuo_detect` 中的 ArUco / solvePnP / 可视化尝试 | 明确字典、标记尺寸、图像尺寸校验和坐标变换方向，输出可检查的位姿 JSON |

原目录还包含第三方参考仓库与教程脚本；本发布版重新组织实现，不将它们整包收录或宣称为个人原创算法。
2026-11-14 的发布整理新增了命令行、输入校验、合成演示、测试与文档；这些新增内容不表示早期实验当时就已完成同样验证。

- 检测使用 [Ultralytics](https://github.com/ultralytics/ultralytics)，本仓库不包含其框架源码或预训练权重。遵循本仓库与所用上游依赖的许可。
- ArUco 检测、solvePnP、projectPoints 使用 [OpenCV](https://docs.opencv.org/4.x/d5/dae/tutorial_aruco_detection.html)。它们是成熟库算法，不是本项目提出的新算法。
- 单目尺寸先验公式是针孔成像模型的基础关系；本项目的价值在实验组织、可复现输入输出和边界说明。
- 示例 ArUco 图案由 OpenCV 程序生成，示例距离与像素扰动为合成数据；不包含私人录制、第三方演示照片或真实实验精度承诺。

本仓库以 AGPL-3.0-only 发布，完整许可见 LICENSE。
