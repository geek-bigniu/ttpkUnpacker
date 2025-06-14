import re
import sys

import esprima
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from loguru import logger


# 1. 为不同输出设置不同日志级别
def set_level_for_handlers():
    logger.remove()
    # 添加文件输出，记录 DEBUG 及以上级别
    logger.add(
        sys.stdout,
        level="INFO",
    )
    logger.add(
        "logs/app_{time}.log",
        level="DEBUG",  # 设置文件输出最低级别为 DEBUG
        rotation="1 MB",  # 按文件大小分割
        retention="7 days",  # 保留 7 天
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message}"
    )


set_level_for_handlers()


@dataclass
class Context:
    params: Dict[str, str]
    variables: Dict[str, str]
    parent: Optional['Context'] = None

    def get_param(self, name: str) -> Optional[str]:
        if name in self.params:
            return self.params[name]
        return self.parent.get_param(name) if self.parent else None

    def get_variable(self, name: str) -> Optional[str]:
        if name in self.variables:
            return self.variables[name]
        return self.parent.get_variable(name) if self.parent else None


class ASTConverter:
    def __init__(self, js_code: str, pagePath: dict):
        self.js_code = js_code
        self.global_vars: Dict[str, str] = {}
        self.contexts: List[Context] = [Context(params={}, variables={})]
        self.ast = None
        self.strip_chars = '"\''
        self.strip_chars_index = "'"
        self.importTpls = {}
        self.pagePath = pagePath
        self.templateList = []

    def extract_path(self, node: Any, context: Context, for_loop: bool = False, for_class: bool = False) -> str:
        if not hasattr(node, 'type'):
            logger.warning(f"无效节点: {node}")
            return 'unknown'

        logger.debug(f"Extracting path: node={node.type}, for_loop={for_loop}, for_class={for_class}")

        if node.type == 'MemberExpression':
            obj = self.extract_path(node.object, context, for_loop)
            prop = self.extract_path(node.object, context, for_loop)
            if obj == "data":
                return prop
            if context.get_param(obj) == "data":
                return prop
            if obj == 'unknown':
                logger.warning(f"无法解析 MemberExpression 的对象: {node.object.type}")
                return prop
            return f"{obj}.{prop}"

        elif node.type == 'Identifier':
            param = context.get_param(node.name) or node.name
            logger.debug(f"Identifier: name={node.name}, resolved={param}")
            return param

        elif node.type == 'Literal':
            return f'{node.raw}' if isinstance(node.value, str) else str(node.value)

        elif node.type == 'BinaryExpression':
            left = self.extract_path(node.left, context, for_loop, for_class)
            right = self.extract_path(node.right, context, for_loop, for_class)
            if node.operator == '+':
                if for_class:
                    # 对于 class 属性，返回独立表达式列表
                    if right == '" "':
                        return f"{left} }}}} {{{{"
                    elif left.endswith("{{"):
                        return f"{left} {right}"
                    if node.left.type == 'Literal' and node.right != 'Literal':
                        return f"{node.left.value}  {{{{{right}}}}}"
                    if node.right.type == 'Literal' and node.left != 'Literal':
                        return f"{{{{{right}}}}} {node.right.value}"
                    return f"{left} {{{{{right}}}}}"
                else:
                    return f"{left} + {right}"
            return f"{left} {node.operator} {right}"

        elif node.type == 'LogicalExpression':
            left = self.extract_path(node.left, context, for_loop, for_class)
            right = self.extract_path(node.right, context, for_loop, for_class)
            operator = node.operator
            return f"{left} {operator} {right}"

        elif node.type == 'UnaryExpression':
            operator = node.operator
            argument = self.extract_path(node.argument, context, for_loop, for_class)
            if operator == '!':
                return f"!{argument}"
            elif operator == '-':  # 添加对一元负号的支持
                return f"-{argument}"
            elif operator == 'void':
                return 'undefined'
            logger.warning(f"未支持的 UnaryExpression 运算符: {operator}")
            return 'unknown'

        elif node.type == 'ConditionalExpression':
            test = self.extract_path(node.test, context, for_loop, for_class)
            consequent = self.extract_path(node.consequent, context, for_loop, for_class)
            alternate = self.extract_path(node.alternate, context, for_loop, for_class)
            return f"{test} ? {consequent} : {alternate}"

        elif node.type == 'CallExpression' and hasattr(node.callee, 'name'):
            if self.global_vars.get(node.callee.name) in ['$.$sg', '$.$ss']:
                if len(node.arguments) != 2:
                    return self.extract_path(node.arguments[0], context, for_loop)
                first_arg = node.arguments[0]
                second_arg = node.arguments[1]
                if second_arg.type == 'MemberExpression':
                    prop_name = second_arg.property.name
                elif second_arg.type == 'CallExpression':
                    prop_name = self.extract_path(second_arg, context, for_loop)
                else:
                    prop_name = second_arg.value if second_arg.value is not None else \
                        ("'" + context.get_param(second_arg.name) + "'" if second_arg.name else 'unknown')
                logger.debug(f"s call: first_arg={first_arg.type}, prop_name={prop_name}")

                if for_loop:
                    if hasattr(first_arg, 'object') and hasattr(first_arg.object, 'name') and context.get_param(
                            first_arg.object.name) == "data":
                        prop = first_arg.property.name if hasattr(first_arg.property,
                                                                  'name') else first_arg.property.value
                        logger.debug(f"Loop: e.data detected, prop={prop}")
                        return f"{prop}.{prop_name}"
                    if first_arg.type == 'CallExpression' and self.global_vars.get(first_arg.callee.name) == '$.$sg':
                        path = self.extract_path(first_arg, context, for_loop=False, for_class=for_class)
                        logger.debug(f"Loop: nested s call, path={path}")
                        return f"{path}[{prop_name}]" if "'" in prop_name else f"{path}.{prop_name}"
                    elif first_arg.type == 'MemberExpression':
                        base_path = self.extract_path(first_arg, context, for_loop, for_class)
                        index_var = context.get_param(node.arguments[1].name) if hasattr(node.arguments[1],
                                                                                         'name') else 'unknown'
                        logger.debug(f"Loop: base_path={base_path}, index_var={index_var}")
                        return f"{base_path}[{index_var}]" if hasattr(node.arguments[1], 'name') else \
                            f"{base_path.replace(first_arg.object.name + '.', '')}[{index_var}]"

                base = self.extract_path(first_arg, context, for_loop, for_class)

                if type(prop_name) == int or second_arg.type in ['MemberExpression', 'CallExpression']:
                    return f"{base}[{prop_name}]"
                if base == 'unknown' or prop_name == 'unknown':
                    logger.warning(f"无法解析 s 调用: base={base}, prop_name={prop_name}")
                    return 'unknown'
                return f"{base}[{prop_name}]" if "'" in prop_name else f"{base}.{prop_name}"

            elif node.callee.name == '$.renderList' and for_loop:
                if len(node.arguments) < 1:
                    logger.warning(f"无效 renderList 调用: arguments={len(node.arguments)}")
                    return 'unknown'
                list_path = self.extract_path(node.arguments[0], context, for_loop=False, for_class=for_class)
                logger.debug(f"renderList: list_path={list_path}")
                return list_path if list_path != 'unknown' else 'unknown'
            elif node.callee.type == 'MemberExpression':
                return self.extract_path(node.arguments[0], context, for_loop, for_class)
        elif node.type == 'ArrayExpression':
            if len(node.elements) > 0:
                return self.extract_path(node.elements[0], context, for_loop, for_class)
            else:
                return '[]'

        logger.warning(f"未处理节点类型: {node.type}")
        return 'unknown'

    def resolve_component_name(self, component: Any, context: Context) -> str:
        if hasattr(component, 'name') and context.get_variable(component.name) is not None:
            return context.get_variable(component.name)
        if hasattr(component, 'name') and self.global_vars.get(component.name) == '$.Fragment':
            return "template"
        elif hasattr(component, 'name') and context.get_variable(component.name) == 'frame-animation':
            return "frame-animation"
        elif component.type == 'CallExpression' and len(component.arguments) > 0:
            return component.arguments[0].value
        return self.global_vars.get(component.name, component.name) if hasattr(component, 'name') else 'unknown'

    def to_mini_program_prop(self, key: str) -> str:
        """将驼峰命名转换为小程序的连字符命名"""
        import re
        if key in ['className']:
            return 'class'
        return re.sub(r'([A-Z])', r'-\1', key).lower()

    def render_class_expressions(self, node: Any, context: Context) -> List[str]:
        """处理复杂的 class 表达式，拆分为多个独立的 {{...}} 表达式"""
        expressions = []
        if node.type == 'BinaryExpression' and node.operator == '+':
            # 递归处理 BinaryExpression 的左右节点
            left = self.render_class_expressions(node.left, context)
            right = self.render_class_expressions(node.right, context)
            expressions.extend(left)
            expressions.extend(right)
        elif node.type == 'Literal' and node.raw == '" "':
            # 跳过空格字面量
            return []
        else:
            path = self.extract_path(node, context, for_class=True)
            if path != 'unknown':
                expressions.append(f"{{{path}}}")
        return expressions

    def render_props(self, props: Any, indent: int, context: Context) -> str:
        ttml = ""
        for prop in props.properties:
            key = prop.key.name if hasattr(prop.key, 'name') and prop.key.name is not None else prop.key.value
            value = prop.value
            if key in ['__fields', '__bridge', '__dirname']:
                continue
            mini_key = self.to_mini_program_prop(key)
            if key.startswith('bind'):
                ttml += f' {mini_key}="{value.arguments[0].value}"'
            elif key == 'className':
                if value is None or not hasattr(value, 'type'):
                    logger.warning(f"无效 className: {value}")
                    ttml += ' class=""'
                elif value.type == 'CallExpression' and hasattr(value.arguments[0], 'raw'):
                    if value.arguments[0].type == 'Literal':
                        if value.arguments[0].raw != '""':
                            ttml += f" class={value.arguments[0].raw}"
                    else:
                        path = self.extract_path(value, context, for_class=True).replace('"', "'")
                        if value.arguments[0].left is not None and value.arguments[0].left.type == 'Literal':
                            ttml += f' class="{path}"'
                        else:
                            ttml += f' class="{{{{{path}}}}}"'
                elif value.type in ['BinaryExpression', 'ConditionalExpression']:
                    # 处理复杂的 class 表达式，拆分为多个 {{...}}
                    class_expressions = self.render_class_expressions(value, context)
                    if class_expressions:
                        path = " ".join(class_expressions).replace('"', "'")
                        ttml += f' class="{path}"'
                    else:
                        ttml += ' class=""'
                else:
                    logger.warning(f"无法解析 className: {value.type}")
                    ttml += ' class=""'
            elif key.startswith("data-"):
                if hasattr(value, 'name') and value.type == 'Identifier':
                    ttml += f' {key}="{{{{{context.get_param(value.name) or value.name}}}}}"'
                elif value.type == 'CallExpression':
                    path = self.extract_path(value, context)
                    ttml += f' {key}="{{{{{path}}}}}"'
                else:
                    ttml += ' data-index=""'
            elif key == 'src':
                if value is None or not hasattr(value, 'type'):
                    logger.warning(f"无效 src 属性: {value}")
                    ttml += ' src=""'
                elif value.type in ['BinaryExpression', 'CallExpression', 'MemberExpression', 'LogicalExpression']:
                    path = self.extract_path(value, context).replace("\"", "'")
                    ttml += f' src="{{{{{path}}}}}"' if path != 'unknown' else ' src=""'
                elif value.type == 'ConditionalExpression':
                    path = self.extract_path(value, context).replace("\"", "'")
                    ttml += " src=\"%s\"" % ("{{" + path + "}}")
                elif value.type == 'Literal':
                    ttml += " src=\"%s\"" % value.value
                elif value.type == 'Identifier':
                    ttml += " src=\"%s\"" % ("{{" + context.get_param(value.name) + "}}")
                elif hasattr(value, 'raw') and value.raw is not None:
                    ttml += " src=\"%s\"" % ("{{" + value.raw.strip('"') + "}}")
                else:
                    logger.warning(f"无法解析 src 属性: {value.type}")
                    ttml += ' src=""'
            elif key in ['width', 'height', 'count', 'duration']:
                if hasattr(value, 'raw') and value.raw is not None:
                    ttml += f' {mini_key}="{value.raw.strip(self.strip_chars)}"'
                else:
                    ttml += f' {mini_key}=""'
            elif key == 'direction':
                path = self.extract_path(value, context).replace("\"", "'")
                ttml += f' {mini_key}="{{{{{path}}}}}"' if path != 'unknown' else f' {mini_key}=""'
            else:
                ttml += self.render_custom_prop(mini_key, value, context)
        return ttml

    def render_custom_prop(self, key: str, value: Any, context: Context) -> str:
        if value is None or not hasattr(value, 'type'):
            logger.warning(f"无效属性值: key={key}, value={value}")
            return f' {key}=""'
        elif value.type in ['CallExpression', 'BinaryExpression', 'ConditionalExpression', 'LogicalExpression']:
            val = self.extract_path(value, context).replace("\"", "'")
            return f' {key}="{{{{{val}}}}}"' if val != 'unknown' else f' {key}=""'
        elif value.type == 'UnaryExpression':
            val = value.operator + str(value.argument.value).replace("\"", "'")
            return f' {key}="{"false" if val == "!0" else "true"}"'
        elif value.type == 'MemberExpression':
            path = self.extract_path(value, context).replace("\"", "'")
            return f' {key}="{{{{{path}}}}}"' if path != 'unknown' else f' {key}=""'
        elif value.type == 'Identifier':
            param = context.get_param(value.name) or value.name
            return f' {key}="{param}"'
        elif value.type == 'Literal':
            clean_value = str(value.value).strip('"\'')
            return f' {key}="{clean_value}"'
        elif hasattr(value, 'raw') and value.raw is not None:
            clean_value = value.raw.strip('"\'')
            return f' {key}="{clean_value}"'
        return f' {key}=""'

    def convert_to_ttml(self, node: Any, indent: int = 0, context: Context = None) -> str:
        ttml = ""
        if not hasattr(node, 'type'):
            return ""

        if node.type == 'CallExpression' and hasattr(node.callee, 'name') and self.global_vars.get(
                node.callee.name) == '$.createVNode':
            component = node.arguments[0]
            component_name = self.resolve_component_name(component, context)
            props = node.arguments[1] if len(node.arguments) > 1 else None
            children = node.arguments[2] if len(node.arguments) > 2 else None

            if component_name == 'template':
                if children and children.type == 'ArrayExpression':
                    for child in children.elements:
                        ttml += self.convert_to_ttml(child, indent, context)
                elif children and children.type in ['CallExpression', 'ConditionalExpression']:
                    ttml += self.convert_to_ttml(children, indent, context)
                else:
                    logger.warning(f"无法解析的 template 子节点: {children.type if children else 'None'}")
                return ttml

            ttml = "  " * indent + f"<{component_name}"
            if props and props.type == 'ObjectExpression':
                ttml += self.render_props(props, indent, context)
            ttml += ">\n"

            if children and children.type == 'ArrayExpression':
                for child in children.elements:
                    if child is not None:
                        ttml += self.convert_to_ttml(child, indent + 1, context)
            elif children and children.type == 'CallExpression':
                ttml += self.convert_to_ttml(children, indent + 1, context)
            elif children and children.type == 'Literal':
                if children.value is not None:
                    ttml += "  " * (indent + 1) + children.value + "\n"
            elif children and children.type in ['BinaryExpression']:
                path = self.extract_path(children, context)
                ttml += "  " * (indent + 1) + f"{{{{{path}}}}}" + "\n"
            elif children and children.type in ['ConditionalExpression']:
                ttml += self.convert_to_ttml(children, indent, context)

            else:
                if hasattr(children, 'type'):
                    logger.warning(f"尝试解析无法解析的子节点: {children.type}")
                    path = self.extract_path(children, context)
                    ttml += "  " * (indent + 1) + path + "\n"
                    logger.warning(f"尝试解析子节点结果(可能不准确): {path}")
                else:
                    if children is not None:
                        logger.warning(f"无法解析的子节点: {children}")
            ttml += "  " * indent + f"</{component_name}>\n"

        elif node.type == 'CallExpression' and hasattr(node.callee, 'name') and self.global_vars.get(
                node.callee.name) in ['$.renderList']:
            list_name = self.extract_path(node.arguments[0], context, for_loop=True)
            if list_name == 'unknown':
                logger.warning(f"无法解析 renderList 的列表路径: {node.arguments[0].type}")
                return ""
            params = node.arguments[1].params
            new_context = Context(
                params={params[0].name: f"item_{len(self.contexts)}", params[1].name: f"index_{len(self.contexts)}"},
                variables={},
                parent=context
            )
            self.contexts.append(new_context)
            child_ttml = self.convert_to_ttml(node.arguments[1].body.body[0].argument, indent, new_context)
            if child_ttml.strip():
                lines = child_ttml.split('\n')
                first_line = lines[0]
                if first_line.strip().startswith('<'):
                    tag_start = first_line.find('<')
                    tag_end = first_line.find(' ', tag_start)
                    ttml += first_line[
                            :tag_end] + f' tt:for="{{{{{list_name}}}}}" tt:for-item="{new_context.params[params[0].name]}" tt:for-index="{new_context.params[params[1].name]}"' + first_line[
                                                                                                                                                                                  tag_end:] + '\n'
                    ttml += '\n'.join(lines[1:])
                else:
                    ttml += "  " * indent + f"<block tt:for=\"{{{{{list_name}}}}}\" tt:for-item=\"{new_context.params[params[0].name]}\" tt:for-index=\"{new_context.params[params[1].name]}\">\n"
                    ttml += child_ttml
                    ttml += "  " * indent + "</block>\n"
            self.contexts.pop()
        elif node.type == 'CallExpression' and hasattr(node.callee, 'name') and self.global_vars.get(
                node.callee.name) in ['$.renderTemplate']:
            """
            处理类似下面这种导入函数数据：
            <import src="./inline-components.ttml" />
            <import src="./new-inline-components.ttml" />
            <template tt:if="{{customView}}" is="{{customView}}"></template>
            """
            importList = node.arguments[1]
            if importList.type == 'Identifier' and importList.name == '$':
                isValue = self.extract_path(node.arguments[2], context)
                for importPage in self.importTpls:
                    # 确保路径是从根目录开始，需要添加/开头
                    ttml += "  " * indent + f"<import src=\"/{self.importTpls[importPage]}\"/>\n"
                ttml += "  " * indent + f"<template is=\"{{{{{isValue}}}}}\"></template>"
            if importList.type == 'Identifier' and re.match("[a-zA-z]",importList.name):
                logger.warning(f"尝试处理导入函数类型:{importList.name},暂未完善该功能，导出内容可能有问题")
                context_params = {}
                data_value = "{"
                index = 0
                for arg in node.arguments[3].properties:
                    context_params[arg.key.name] = context.get_param(arg.value.name)
                    data_value += str(arg.key.name) + ":" + str(context.get_param(arg.value.name))
                    if index != len(node.arguments[3].properties) - 1:
                        data_value += ","
                    index += 1
                data_value += "}"
                new_context = Context(
                    params=context_params,
                    variables={},
                    parent=context
                )
                self.contexts.append(new_context)
                isValue = self.extract_path(node.arguments[2], new_context)
                ttml += "  " * indent + f"<template is=\"{{{{{isValue}}}}}\" data=\"{{{{{data_value}}}}}\"></template>"
                self.contexts.pop()
            else:
                logger.warning(f"无法处理的导入函数类型:{importList.name},常规导入为$")
        elif node.type == 'ConditionalExpression':
            condition = self.extract_path(node.test, context)
            if condition == 'unknown':
                logger.warning(f"无法解析条件表达式: {node.test.type}")
                return ""

            # 处理一元表达式（如 !isIos）
            if node.consequent.type == 'Identifier':
                # 反转条件，例如 e.isIos 变为 !isIos
                if node.test.type == 'MemberExpression':
                    condition = f"!{condition}"
                elif node.test.type == 'UnaryExpression' and node.test.operator == '!':
                    condition = self.extract_path(node.test.argument, context)
                elif node.test.type == 'LogicalExpression':
                    condition = self.extract_path(node.test, context)

                else:
                    logger.warning(f"无法反转条件: {node.test.type}")
                    return ""

                alternate_ttml = self.convert_to_ttml(node.alternate, indent, context)
                if alternate_ttml.strip():
                    lines = alternate_ttml.split('\n')
                    first_line = lines[0]
                    if first_line.strip().startswith('<'):
                        tag_start = first_line.find('<')
                        tag_end = first_line.find(' ', tag_start)
                        ttml += first_line[:tag_end] + f' tt:if="{{{{{condition}}}}}"' + first_line[tag_end:] + '\n'
                        ttml += '\n'.join(lines[1:])
                    else:
                        ttml += "  " * indent + f"<block tt:if=\"{{{{{condition}}}}}\">\n"
                        ttml += alternate_ttml
                        ttml += "  " * indent + "</block>\n"
                return ttml
            elif node.consequent.type == "CallExpression" and self.global_vars.get(
                    node.consequent.callee.name) == '$.renderTemplate':
                # 自定义渲染模块的处理
                consequent_ttml = self.convert_to_ttml(node.consequent, indent, context)
                if consequent_ttml.strip():
                    lines = consequent_ttml.split('\n')
                    last_line = lines[len(lines) - 1]
                    if last_line.strip().startswith('<'):
                        tag_start = last_line.find('<')
                        tag_end = last_line.find(' ', tag_start)
                        ttml += '\n'.join(lines[:-1]) + "\n"
                        ttml += last_line[:tag_end] + f' tt:if="{{{{{condition}}}}}"' + last_line[tag_end:] + '\n'
                alternate = node.alternate
                while alternate.type == 'ConditionalExpression':
                    condition = self.extract_path(alternate.test, context)
                    if condition == 'unknown':
                        logger.warning(f"无法解析嵌套条件表达式: {alternate.test.type}")
                        break
                    alternate_ttml = self.convert_to_ttml(alternate.consequent, indent, context)
                    if alternate_ttml.strip():
                        lines = alternate_ttml.split('\n')
                        first_line = lines[0]
                        if first_line.strip().startswith('<'):
                            tag_start = first_line.find('<')
                            tag_end = first_line.find(' ', tag_start)
                            ttml += first_line[:tag_end] + f' tt:elif="{{{{{condition}}}}}"' + first_line[
                                                                                               tag_end:] + '\n'
                            ttml += '\n'.join(lines[1:])
                        else:
                            ttml += "  " * indent + f"<block tt:elif=\"{{{{{condition}}}}}\">\n"
                            ttml += alternate_ttml
                            ttml += "  " * indent + "</block>\n"
                    alternate = alternate.alternate
                if alternate.type != 'Identifier':
                    alternate_ttml = self.convert_to_ttml(alternate, indent, context)
                    if alternate_ttml.strip():
                        lines = alternate_ttml.split('\n')
                        first_line = lines[0]
                        if first_line.strip().startswith('<'):
                            tag_start = first_line.find('<')
                            tag_end = first_line.find(' ', tag_start)
                            ttml += first_line[:tag_end] + ' tt:else' + first_line[tag_end:] + '\n'
                            ttml += '\n'.join(lines[1:])
                        else:
                            ttml += "  " * indent + "<block tt:else>\n"
                            ttml += alternate_ttml
                            ttml += "  " * indent + "</block>\n"
                return ttml
            else:
                # 处理常规条件表达式
                consequent_ttml = self.convert_to_ttml(node.consequent, indent, context)
                if consequent_ttml.strip():
                    lines = consequent_ttml.split('\n')
                    first_line = lines[0]
                    if first_line.strip().startswith('<'):
                        tag_start = first_line.find('<')
                        tag_end = first_line.find(' ', tag_start)
                        ttml += first_line[:tag_end] + f' tt:if="{{{{{condition}}}}}"' + first_line[tag_end:] + '\n'
                        ttml += '\n'.join(lines[1:])
                    else:
                        ttml += "  " * indent + f"<block tt:if=\"{{{{{condition}}}}}\">\n"
                        ttml += consequent_ttml
                        ttml += "  " * indent + "</block>\n"

                alternate = node.alternate
                while alternate.type == 'ConditionalExpression':
                    condition = self.extract_path(alternate.test, context)
                    if condition == 'unknown':
                        logger.warning(f"无法解析嵌套条件表达式: {alternate.test.type}")
                        break
                    alternate_ttml = self.convert_to_ttml(alternate.consequent, indent, context)
                    if alternate_ttml.strip():
                        lines = alternate_ttml.split('\n')
                        first_line = lines[0]
                        if first_line.strip().startswith('<'):
                            tag_start = first_line.find('<')
                            tag_end = first_line.find(' ', tag_start)
                            ttml += first_line[:tag_end] + f' tt:elif="{{{{{condition}}}}}"' + first_line[
                                                                                               tag_end:] + '\n'
                            ttml += '\n'.join(lines[1:])
                        else:
                            ttml += "  " * indent + f"<block tt:elif=\"{{{{{condition}}}}}\">\n"
                            ttml += alternate_ttml
                            ttml += "  " * indent + "</block>\n"
                    alternate = alternate.alternate

                if alternate.type != 'Identifier':
                    alternate_ttml = self.convert_to_ttml(alternate, indent, context)
                    if alternate_ttml.strip():
                        lines = alternate_ttml.split('\n')
                        first_line = lines[0]
                        if first_line.strip().startswith('<'):
                            tag_start = first_line.find('<')
                            tag_end = first_line.find(' ', tag_start)
                            ttml += first_line[:tag_end] + ' tt:else' + first_line[tag_end:] + '\n'
                            ttml += '\n'.join(lines[1:])
                        else:
                            ttml += "  " * indent + "<block tt:else>\n"
                            ttml += alternate_ttml
                            ttml += "  " * indent + "</block>\n"

        elif node.type == 'CallExpression' and hasattr(node.callee, 'name') and self.global_vars.get(
                node.callee.name) == '$.$ss':
            path = self.extract_path(node.arguments[0], context, for_loop=False)
            ttml += "  " * indent + "{{" + path + "}}\n"
        elif node.type == 'CallExpression' and hasattr(node.callee, 'name') and self.global_vars.get(
                node.callee.name) == '$.createText':

            if node.arguments[0].type == 'Literal':
                path = node.arguments[0].value
                ttml += "  " * indent + path + "\n"
            elif node.arguments[0].type == 'BinaryExpression':
                path = self.extract_path(node.arguments[0], context, for_loop=False)
                ttml += "  " * indent + "{{" + path + "}}" + "\n"
            elif node.arguments[0].type == 'CallExpression':
                ttml += self.convert_to_ttml(node.arguments[0], indent, context)
            else:
                logger.error(f"尝试处理未知节点：{node.arguments[0].type}")
                path = self.extract_path(node.arguments[0], context, for_loop=False)
                ttml += "  " * indent + "{{" + path + "}}" + "\n"
        elif node.type == 'Identifier':
            # 单纯变量不处理
            pass
        elif node.type == 'CallExpression' and hasattr(node.callee, 'name') and self.global_vars.get(
                node.callee.name) == '$.renderSlot':
            arguments = node.arguments
            name = arguments[1].value
            ttml += "  " * indent + f"<slot name=\"{name}\">\n"
            ttml += self.convert_to_ttml(arguments[2], indent, context)
            ttml += "  " * indent + "</slot>\n"

        else:
            logger.warning(f"无法处理的节点类型: {node.type}")
        return ttml

    def convert_to_template(self):
        templates = []
        for template in self.templateList:
            left = template.left
            right = template.right
            name = left.property.value if left.property.value else left.property.name
            if name == 'render':
                # 普通内容渲染函数，直接跳过
                continue
            params = right.params
            new_context = Context(
                params={params[0].name: "data",
                        params[1].name: "ctx"
                        },
                variables={},
                parent=self.contexts[0]
            )
            self.contexts.append(new_context)
            render_body = None
            for node in right.body.body:
                if node.type == 'VariableDeclaration':
                    self.contexts[1].variables.update(self.extract_variable_mappings(node))
                    logger.debug(f"Template variables updated: {self.contexts[1].variables}")
                if node.type == 'ReturnStatement':
                    render_body = node.argument
            if render_body is not None and name is not None:
                ttml_content = f'<template name="{name}">\n'
                ttml_content += self.convert_to_ttml(render_body, context=self.contexts[1])
                ttml_content += "</template>"
                templates.append(ttml_content)
            self.contexts.pop()

        return "\n".join(templates)
        pass

    def parse_ast(self) -> None:
        try:
            self.ast = esprima.parseScript(self.js_code,locale=True)
            # logger.info("成功解析 JavaScript 代码")
        except Exception as e:
            logger.error(f"解析 JavaScript 失败: {e}")
            raise SystemExit(1)

    def extract_variable_mappings(self, node: Any) -> Dict[str, str]:
        if not hasattr(node, 'type') or node.type != 'VariableDeclaration':
            return {}
        mappings = {}
        for declarator in node.declarations:
            var_name = declarator.id.name
            init = declarator.init
            if init is None:
                logger.debug(f"Variable {var_name} has no initializer")
                continue
            if init.type == 'Identifier':
                mappings[var_name] = init.name
            elif init.type == 'MemberExpression':
                prop = init.property.name if init.property.type == 'Identifier' else init.property.value
                mappings[var_name] = f"$.{prop}"
            elif init.type == 'CallExpression':
                if len(init.arguments) == 1:
                    mappings[var_name] = init.arguments[0].value.replace("tt-", "")
                elif init.callee.type == 'MemberExpression':
                    mappings[var_name] = init.callee.property.name
            elif init.type == 'FunctionExpression':
                importModelList = init.body.body[0].argument.arguments[1:]
                for modelName in importModelList:
                    if modelName.object is not None:
                        import_name = modelName.object.name.replace("$m_", "")
                        self.importTpls[import_name] = self.pagePath[import_name]
                        # logger.info("找到导包函数", declarator.id.name, import_name)
            elif init.type == 'SequenceExpression' and init.expressions[0].type == 'MemberExpression' and \
                    init.expressions[0].property.name == 'VOID':

                express_1 = init.expressions[1]
                if express_1.type == 'MemberExpression':
                    prop = express_1.property.name if express_1.property.type == 'Identifier' else express_1.property.value
                    mappings[var_name] = f"$.{prop}"
                elif express_1.type == "CallExpression" and mappings[
                    express_1.callee.name] == '$.resolveBuiltinComponent':
                    prop = express_1.arguments[0].value.replace("tt-", "")
                    mappings[var_name] = prop
                    pass
            elif init.type == 'ObjectExpression' and len(init.properties) == 0:
                # tpls的空对象
                mappings[var_name] = "$.tpls"
                pass
            else:
                logger.warning(f"未处理的参数：{init.type}")

        return mappings

    def convert(self) -> str:
        self.parse_ast()
        create_commonjs_module = self.ast.body[0].expression.right.arguments[0].body.body
        render_function = None
        if len(create_commonjs_module) > 1:
            for objFun in create_commonjs_module:
                if objFun.type == "ExpressionStatement":
                    # 获取render节点
                    for expression in objFun.expression.expressions:
                        if expression.left and expression.left.property and expression.left.property.name == 'render':
                            render_function = expression.right
                            break
                    if render_function is not None:
                        break

        else:
            render_function = create_commonjs_module[1].expression.expressions[1].right
        if render_function == None:
            logger.error("未找到render函数", create_commonjs_module)
            return ""
        logger.debug(f"render_function: {render_function.type}")

        render_params = render_function.params
        self.contexts[0].params = {
            render_params[0].name: "data",
            render_params[1].name: "context"
        }

        for node in create_commonjs_module:
            if node.type == 'VariableDeclaration':
                self.global_vars.update(self.extract_variable_mappings(node))
                logger.debug(f"Global variables updated: {self.global_vars}")
            if node.type == 'ExpressionStatement':
                for item in node.expression.expressions:
                    if item.type == "AssignmentExpression" and item.left.type == "MemberExpression" and item.right.type == "FunctionExpression":
                        # 模板定义处理
                        self.templateList.append(item)

        for node in render_function.body.body:
            if node.type == 'VariableDeclaration':
                self.contexts[0].variables.update(self.extract_variable_mappings(node))
                logger.debug(f"Render variables updated: {self.contexts[0].variables}")

        render_body = None
        for node in render_function.body.body:
            if node.type == 'ReturnStatement':
                render_body = node.argument
                break

        if not render_body:
            logger.error("未找到 render 函数的返回语句")
            raise SystemExit(1)

        ttml_content = self.convert_to_template()
        ttml_content += self.convert_to_ttml(render_body, context=self.contexts[0])
        ttml_content += ""
        return ttml_content


def run(js_code: str, pagePath: dict, output_file: str = "output.ttml") -> None:
    converter = ASTConverter(js_code, pagePath=pagePath)
    ttml_content = converter.convert()
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(ttml_content)


if __name__ == "__main__":
    try:
        # 这里是单文件调试，输入对应的page-frame.js文件对应的地址，可以吧page-frame.js的内容复制到js_code.js里进行调试
        with open("js_code.js", mode="r", encoding="utf-8") as file:
            js_code = "".join(file.readlines())
        pagePath = {'Base_593616de': "pages/API/inline-components.ttml"}
        output_file = "output.ttml"
        run(js_code, pagePath)
        logger.info(f"TTML 内容已生成到 {output_file}")
    except FileNotFoundError:
        logger.error("未找到 js_code.js 文件")
        raise SystemExit(1)
