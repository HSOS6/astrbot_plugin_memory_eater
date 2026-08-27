# astrbot_plugin_memory_eater

## 指令

| 指令 | 别名 | 作用喵 |
|---|---|---|
| `/mem_start` | `开吃` `内存开吃` | 让内存开始泄漏喵 |
| `/mem_stop` | `停下` `别吃了` | 停下 |
| `/mem_release` | `吐出来` `内存释放` | 释放 |
| `/mem_status` | `吃了多少` `内存状态` | 看看吃了多少还剩多少内存 |

## 插件配置

| 配置项 | 参考 | 说明喵 |
|---|---|---|
| `threshold_mb` | 100 | 剩多少 MB 停 |
| `chunk_mb` | 64 | 一次多大 |
| `interval_s` | 0.5 | 每次口之间歇多久 |
| `auto_start` | true | 装好是否自动启动 |

## 文件分布

```
astrbot_plugin_memory_eater/
├── main.py               # 插件本体（后台循环 + 指令）
├── metadata.yaml         # 滚木
├── _conf_schema.json     # 设置文件
└── requirements.txt      # 滚木
```

---
