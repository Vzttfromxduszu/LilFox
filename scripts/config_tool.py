"""配置管理工具"""

import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    get_config_manager,
    init_configs,
    Environment,
    get_environment,
)


def cmd_validate(args):
    """验证配置"""
    print("验证配置...")
    
    manager = init_configs()
    
    if args.config:
        is_valid = manager.validate_config(args.config)
        if is_valid:
            print(f"✅ 配置 '{args.config}' 验证通过")
        else:
            print(f"❌ 配置 '{args.config}' 验证失败")
            errors = manager.get_validation_errors(args.config)
            for error in errors:
                print(f"  - {error.field}: {error.message}")
    else:
        results = manager.validate_all_configs()
        print("\n配置验证结果:")
        print("-" * 60)
        for name, is_valid in results.items():
            status = "✅ 通过" if is_valid else "❌ 失败"
            print(f"  {name:20} - {status}")
            if not is_valid:
                errors = manager.get_validation_errors(name)
                for error in errors:
                    print(f"    - {error.field}: {error.message}")
        print("-" * 60)


def cmd_show(args):
    """显示配置"""
    manager = init_configs()
    
    if args.config:
        config = manager.get_config(args.config)
        if config:
            print(f"\n配置: {args.config}")
            print("-" * 60)
            config_dict = config.get_config_dict()
            for key, value in sorted(config_dict.items()):
                if args.format == "json":
                    print(f'  "{key}": {repr(value)},')
                else:
                    print(f"  {key}: {value}")
            print("-" * 60)
        else:
            print(f"❌ 未找到配置: {args.config}")
    else:
        print("\n所有配置:")
        print("-" * 60)
        for name, config in manager.get_all_configs().items():
            print(f"\n{name}:")
            config_dict = config.get_config_dict()
            for key, value in sorted(config_dict.items()):
                print(f"  {key}: {value}")
        print("-" * 60)


def cmd_export(args):
    """导出配置"""
    manager = init_configs()
    
    if args.config:
        success = manager.save_config_to_file(args.config, args.output, args.format)
        if success:
            print(f"✅ 配置 '{args.config}' 已导出到 {args.output}")
        else:
            print(f"❌ 导出配置 '{args.config}' 失败")
    else:
        print("❌ 请指定要导出的配置名称")


def cmd_info(args):
    """显示环境信息"""
    manager = init_configs()
    
    info = manager.get_environment_info()
    
    print("\n环境信息:")
    print("-" * 60)
    print(f"  环境: {info['environment']}")
    print(f"  生产环境: {info['is_production']}")
    print(f"  开发环境: {info['is_development']}")
    print(f"  预发布环境: {info['is_staging']}")
    print(f"\n  已加载配置: {', '.join(info['configs'])}")
    print(f"\n  服务URL:")
    for name, url in info['service_urls'].items():
        print(f"    {name}: {url}")
    print("-" * 60)


def cmd_switch(args):
    """切换环境"""
    env = Environment.from_string(args.environment)
    
    print(f"切换到环境: {env.value}")
    
    env_file = f".env.{env.value}"
    if not os.path.exists(env_file):
        print(f"⚠️  警告: 环境文件 {env_file} 不存在")
    
    os.environ["ENVIRONMENT"] = env.value
    
    print(f"✅ 环境已切换到 {env.value}")
    print(f"💡 提示: 重新加载配置以应用更改")


def cmd_list(args):
    """列出所有配置"""
    manager = init_configs()
    
    print("\n可用配置:")
    print("-" * 60)
    for name in manager.get_all_configs().keys():
        config = manager.get_config(name)
        print(f"  {name:20} - {config.APP_NAME} v{config.VERSION}")
    print("-" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="LilFox 配置管理工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    validate_parser = subparsers.add_parser("validate", help="验证配置")
    validate_parser.add_argument("--config", help="指定配置名称")
    validate_parser.set_defaults(func=cmd_validate)
    
    show_parser = subparsers.add_parser("show", help="显示配置")
    show_parser.add_argument("--config", help="指定配置名称")
    show_parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    show_parser.set_defaults(func=cmd_show)
    
    export_parser = subparsers.add_parser("export", help="导出配置")
    export_parser.add_argument("--config", required=True, help="配置名称")
    export_parser.add_argument("--output", required=True, help="输出文件路径")
    export_parser.add_argument("--format", choices=["json", "env"], default="json", help="输出格式")
    export_parser.set_defaults(func=cmd_export)
    
    info_parser = subparsers.add_parser("info", help="显示环境信息")
    info_parser.set_defaults(func=cmd_info)
    
    switch_parser = subparsers.add_parser("switch", help="切换环境")
    switch_parser.add_argument("environment", choices=["development", "staging", "production", "test"], help="环境名称")
    switch_parser.set_defaults(func=cmd_switch)
    
    list_parser = subparsers.add_parser("list", help="列出所有配置")
    list_parser.set_defaults(func=cmd_list)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == "__main__":
    main()
